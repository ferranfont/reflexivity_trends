"""
Point-in-time metrics store (SQLite).

Append-only: every snapshot is kept with its ingestion_time so backtests can be
reconstructed exactly as they would have been seen live (no look-ahead bias).
The "latest" view deduplicates by taking the most recent ingestion per point.

DB location: data/metrics/metrics.sqlite
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

DB_DIR = os.path.join(config.BASE_DIR, "data", "metrics")
DB_PATH = os.path.join(DB_DIR, "metrics.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS metrics (
    theme_id       TEXT NOT NULL,
    source_id      TEXT NOT NULL,
    entity         TEXT NOT NULL,
    metric         TEXT NOT NULL,
    event_date     TEXT NOT NULL,   -- YYYY-MM-DD the value refers to
    value          REAL NOT NULL,
    ingestion_time TEXT NOT NULL,   -- ISO-8601 UTC: when we captured it
    metadata       TEXT,            -- JSON extras
    PRIMARY KEY (theme_id, source_id, entity, metric, event_date, ingestion_time)
);
CREATE INDEX IF NOT EXISTS idx_metrics_lookup
    ON metrics (theme_id, metric, entity, event_date);
"""


def get_connection() -> sqlite3.Connection:
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(_SCHEMA)
    return conn


def save_points(theme_id: str, points: List[dict], ingestion_time: Optional[str] = None) -> int:
    """
    Persist a batch of StandardMetric dicts for a theme.
    Returns the number of rows inserted (duplicates of the same snapshot are ignored).
    """
    if not points:
        return 0
    ts = ingestion_time or datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    inserted = 0
    try:
        with conn:
            for p in points:
                try:
                    conn.execute(
                        "INSERT OR IGNORE INTO metrics "
                        "(theme_id, source_id, entity, metric, event_date, value, ingestion_time, metadata) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            theme_id,
                            p["source_id"],
                            p["entity"],
                            p["metric"],
                            p["event_date"],
                            float(p["value"]),
                            ts,
                            json.dumps(p.get("metadata", {}), ensure_ascii=False),
                        ),
                    )
                    inserted += 1
                except (KeyError, TypeError, ValueError) as e:
                    print(f"  [MetricsStore] Skipping malformed point: {e} -> {p}")
    finally:
        conn.close()
    return inserted


def load_latest(theme_id: str, metric: Optional[str] = None):
    """
    Return a pandas DataFrame with the latest-known value per
    (source_id, entity, metric, event_date). This is the 'current best view';
    for point-in-time backtests query the raw table filtering ingestion_time <= t.
    """
    import pandas as pd

    query = """
        SELECT m.theme_id, m.source_id, m.entity, m.metric, m.event_date,
               m.value, m.ingestion_time, m.metadata
        FROM metrics m
        JOIN (
            SELECT theme_id, source_id, entity, metric, event_date,
                   MAX(ingestion_time) AS max_it
            FROM metrics
            WHERE theme_id = ?
            GROUP BY theme_id, source_id, entity, metric, event_date
        ) last
          ON  m.theme_id = last.theme_id
          AND m.source_id = last.source_id
          AND m.entity = last.entity
          AND m.metric = last.metric
          AND m.event_date = last.event_date
          AND m.ingestion_time = last.max_it
    """
    params = [theme_id]
    if metric:
        query += " WHERE m.metric = ?"
        params.append(metric)
    query += " ORDER BY m.metric, m.entity, m.event_date"

    conn = get_connection()
    try:
        df = pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()
    return df


def summary(theme_id: str) -> str:
    """Human-readable summary of what the store holds for a theme."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT source_id, metric, COUNT(DISTINCT entity) AS entities,
                   COUNT(*) AS points, MIN(event_date), MAX(event_date)
            FROM metrics WHERE theme_id = ?
            GROUP BY source_id, metric ORDER BY source_id, metric
            """,
            (theme_id,),
        ).fetchall()
    finally:
        conn.close()
    if not rows:
        return f"  (store empty for theme '{theme_id}')"
    lines = [
        f"  {r[0]:<12} {r[1]:<22} entities={r[2]:<4} points={r[3]:<6} range={r[4]}..{r[5]}"
        for r in rows
    ]
    return "\n".join(lines)
