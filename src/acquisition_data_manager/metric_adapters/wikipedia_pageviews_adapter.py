"""
Wikipedia Pageviews metric adapter (Capa B - Atencion agregada).

Free Wikimedia REST API, no key required, daily history since 2015.
Academic precedent: Moat et al. (2013) - Wikipedia usage precedes market moves.

Metric produced: wiki_pageviews (daily views per configured page).
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from urllib.parse import quote

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import config
from src.acquisition_data_manager.base_source import BaseMetricSource, StandardMetric

API_TMPL = (
    "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
    "{project}/all-access/user/{title}/daily/{start}/{end}"
)


class WikipediaPageviewsAdapter(BaseMetricSource):
    source_id = "wikipedia"

    def __init__(self, project: str = "en.wikipedia", lookback_days: int = 30):
        self.project = project
        self.lookback_days = lookback_days
        self.headers = {"User-Agent": config.HTTP_USER_AGENT}

    def fetch_metrics(self, theme_id: str, theme_config: Dict[str, Any]) -> List[StandardMetric]:
        pages = theme_config.get("wikipedia_pages", [])
        if not pages:
            print("  [Wikipedia] No 'wikipedia_pages' configured for this theme. Skipping.")
            return []

        end = datetime.now(timezone.utc) - timedelta(days=1)  # yesterday (today is incomplete)
        start = end - timedelta(days=self.lookback_days)
        points: List[StandardMetric] = []

        for page in pages:
            title = quote(page.replace(" ", "_"), safe="")
            url = API_TMPL.format(
                project=self.project,
                title=title,
                start=start.strftime("%Y%m%d00"),
                end=end.strftime("%Y%m%d00"),
            )
            try:
                resp = requests.get(url, headers=self.headers, timeout=30)
                if resp.status_code == 404:
                    print(f"  [Wikipedia] Page not found: '{page}' (check exact title)")
                    continue
                resp.raise_for_status()
                for item in resp.json().get("items", []):
                    ts = item.get("timestamp", "")  # YYYYMMDD00
                    points.append(
                        StandardMetric(
                            source_id=self.source_id,
                            entity=page,
                            metric="wiki_pageviews",
                            event_date=f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}",
                            value=float(item.get("views", 0)),
                            metadata={"project": self.project},
                        )
                    )
            except Exception as e:
                print(f"  [Wikipedia] Error for '{page}': {e}")

        print(f"  [Wikipedia] Collected {len(points)} daily points for {len(pages)} pages.")
        return points
