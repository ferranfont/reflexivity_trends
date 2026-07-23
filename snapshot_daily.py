"""
Reflexivity Trends - Daily Metrics Snapshot
===========================================
Collects quantitative signals from all enabled FREE metric sources and stores
them point-in-time in SQLite (data/metrics/metrics.sqlite).

This is the script to run once a day (cron / Windows Task Scheduler):
    python snapshot_daily.py                # all enabled themes
    python snapshot_daily.py --theme cybersecurity_ai

Layers collected (see plan_I+D.md):
  Capa A (retail crowd)      -> StockTwits volume + bull ratio
  Capa B (aggregate attention)-> Wikipedia pageviews
  Capa C (the informed)      -> SEC EDGAR Form 4 / 8-K counts
  Capa D (informed consensus)-> Polymarket odds + volume
  Capa E (media contagion)   -> GDELT worldwide article counts

The point-in-time dataset this accumulates is the project's core asset:
history can only be built by running this every day, starting today.
"""

import os
import sys
import argparse
from datetime import datetime, timezone

# Windows consoles / Task Scheduler often default to cp1252, which cannot encode
# the emojis in our status output. Force UTF-8 so the cron job never dies on a print.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, ValueError):
    pass

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config

from src.timeseries_store import metrics_store


def build_metric_sources():
    sources = []
    if config.ENABLE_METRIC_WIKIPEDIA:
        from src.acquisition_data_manager.metric_adapters.wikipedia_pageviews_adapter import (
            WikipediaPageviewsAdapter,
        )
        sources.append(WikipediaPageviewsAdapter())
    if config.ENABLE_METRIC_GDELT_VOLUME:
        from src.acquisition_data_manager.metric_adapters.gdelt_volume_adapter import (
            GdeltVolumeAdapter,
        )
        sources.append(GdeltVolumeAdapter())
    if config.ENABLE_METRIC_STOCKTWITS:
        from src.acquisition_data_manager.metric_adapters.stocktwits_adapter import (
            StockTwitsAdapter,
        )
        sources.append(StockTwitsAdapter())
    if config.ENABLE_METRIC_POLYMARKET:
        from src.acquisition_data_manager.metric_adapters.polymarket_adapter import (
            PolymarketAdapter,
        )
        sources.append(PolymarketAdapter())
    if config.ENABLE_METRIC_EDGAR_INSIDER:
        from src.acquisition_data_manager.metric_adapters.edgar_insider_adapter import (
            EdgarInsiderAdapter,
        )
        sources.append(EdgarInsiderAdapter())
    return sources


def snapshot_theme(theme_id: str, theme_config: dict, sources) -> int:
    print(f"\n{'=' * 60}\n📸 SNAPSHOT: {theme_config.get('name', theme_id)} ({theme_id})\n{'=' * 60}")
    ingestion_time = datetime.now(timezone.utc).isoformat()
    total = 0
    for source in sources:
        name = source.__class__.__name__
        print(f"\n[{name}]")
        try:
            points = source.fetch_metrics(theme_id, theme_config)
        except Exception as e:
            print(f"  [!] {name} failed entirely: {e}")
            continue
        saved = metrics_store.save_points(theme_id, points, ingestion_time=ingestion_time)
        total += saved
    print(f"\n--- Stored {total} points for theme '{theme_id}' ---")
    print("Store contents:")
    print(metrics_store.summary(theme_id))
    return total


def main():
    parser = argparse.ArgumentParser(description="Daily point-in-time metrics snapshot")
    parser.add_argument("--theme", help="Specific theme ID (default: all enabled)")
    args = parser.parse_args()

    print("=" * 60)
    print("REFLEXIVITY TRENDS - DAILY METRICS SNAPSHOT")
    print(f"UTC: {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    themes = config.INVESTING_THEMES
    if args.theme:
        if args.theme not in themes:
            print(f"Error: theme '{args.theme}' not found in config.")
            return
        selected = {args.theme: themes[args.theme]}
    else:
        selected = {k: v for k, v in themes.items() if v.get("enabled")}

    if not selected:
        print("No enabled themes to snapshot.")
        return

    sources = build_metric_sources()
    print(f"Active metric sources: {[s.__class__.__name__ for s in sources]}")

    grand_total = 0
    for theme_id, theme_config in selected.items():
        grand_total += snapshot_theme(theme_id, theme_config, sources)

    print(f"\n{'=' * 60}\n✅ Snapshot completed. Total points stored: {grand_total}")
    print(f"DB: {metrics_store.DB_PATH}")


if __name__ == "__main__":
    main()
