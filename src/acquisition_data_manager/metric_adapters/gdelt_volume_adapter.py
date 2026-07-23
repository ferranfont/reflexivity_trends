"""
GDELT news-volume metric adapter (Capa E - Contagio mediatico).

Free GDELT DOC 2.0 API, no key. Measures how many articles worldwide mention
each theme keyword per day -> breadth/contagion of the narrative in mass media.

Metric produced: gdelt_article_count (daily raw article count per keyword).
"""

import os
import sys
import time
from typing import List, Dict, Any

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import config
from src.acquisition_data_manager.base_source import BaseMetricSource, StandardMetric

API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


class GdeltVolumeAdapter(BaseMetricSource):
    source_id = "gdelt"

    def __init__(self, timespan: str = "1m", pause: float = 5.0, max_retries: int = 3):
        self.timespan = timespan
        self.pause = pause            # GDELT's free API throttles aggressively (~1 req / 5s)
        self.max_retries = max_retries
        self.headers = {"User-Agent": config.HTTP_USER_AGENT}

    def _get_with_backoff(self, params):
        """GET with exponential backoff on 429 (GDELT rate limits hard)."""
        delay = self.pause
        for attempt in range(self.max_retries):
            resp = requests.get(API_URL, params=params, headers=self.headers, timeout=45)
            if resp.status_code == 429:
                if attempt < self.max_retries - 1:
                    print(f"  [GDELT-vol] 429 rate-limited, backing off {delay:.0f}s...")
                    time.sleep(delay)
                    delay *= 2
                    continue
            resp.raise_for_status()
            return resp
        resp.raise_for_status()
        return resp

    def fetch_metrics(self, theme_id: str, theme_config: Dict[str, Any]) -> List[StandardMetric]:
        keywords = theme_config.get("keywords", [])
        points: List[StandardMetric] = []

        for kw in keywords:
            params = {
                "query": f'"{kw}" sourcelang:english',
                "mode": "timelinevolraw",
                "format": "json",
                "timespan": self.timespan,
            }
            try:
                resp = self._get_with_backoff(params)
                data = resp.json()
                for series in data.get("timeline", []):
                    for item in series.get("data", []):
                        # date format: 20260715T000000Z
                        d = item.get("date", "")
                        if len(d) < 8:
                            continue
                        points.append(
                            StandardMetric(
                                source_id=self.source_id,
                                entity=kw,
                                metric="gdelt_article_count",
                                event_date=f"{d[0:4]}-{d[4:6]}-{d[6:8]}",
                                value=float(item.get("value", 0)),
                                metadata={"series": series.get("series", "")},
                            )
                        )
                time.sleep(self.pause)  # be gentle with the free API
            except Exception as e:
                print(f"  [GDELT-vol] Error for '{kw}': {e}")

        print(f"  [GDELT-vol] Collected {len(points)} daily points for {len(keywords)} keywords.")
        return points
