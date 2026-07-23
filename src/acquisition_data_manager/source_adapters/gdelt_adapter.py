"""
GDELT article adapter (Capa E - Medios a escala global).

Free GDELT DOC 2.0 API, no key. Complements GNews with worldwide coverage:
returns articles from thousands of outlets with country/language metadata,
which lets the pipeline measure geographic breadth of narrative contagion.
"""

import os
import sys
import time
from typing import List

import requests

from ..base_source import BaseSource, StandardArticle
from src.models import ArticleModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import config

API_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


class GdeltAdapter(BaseSource):
    """Fetches recent articles matching a query from the global GDELT index."""

    def __init__(self, max_records: int = 30, timespan: str = "2w"):
        self.max_records = max_records
        self.timespan = timespan
        self.source_id = "gdelt"
        self.headers = {"User-Agent": config.HTTP_USER_AGENT}

    def fetch(self, query: str) -> List[StandardArticle]:
        print(f"  [GDELT] Searching for: {query}...")
        params = {
            "query": f'"{query}" sourcelang:english',
            "mode": "artlist",
            "maxrecords": self.max_records,
            "format": "json",
            "timespan": self.timespan,
            "sort": "hybridrel",
        }
        try:
            resp = requests.get(API_URL, params=params, headers=self.headers, timeout=45)
            resp.raise_for_status()
            results = resp.json().get("articles", [])
            articles: List[StandardArticle] = []

            for item in results:
                seendate = item.get("seendate", "")  # 20260715T123000Z
                published = (
                    f"{seendate[0:4]}-{seendate[4:6]}-{seendate[6:8]}"
                    if len(seendate) >= 8 else ""
                )
                title = item.get("title", "").strip()
                if not title:
                    continue
                article_data = {
                    "source_id": self.source_id,
                    "source_name": item.get("domain", "GDELT"),
                    "title": title,
                    "url": item.get("url", ""),
                    "published_date": published,
                    "abstract": title,  # artlist mode carries no snippet
                    "full_text": None,
                    "metadata": {
                        "domain": item.get("domain"),
                        "source_country": item.get("sourcecountry"),
                        "language": item.get("language"),
                    },
                }
                try:
                    articles.append(ArticleModel(**article_data).model_dump())
                except Exception as e:
                    print(f"  [GDELT] Validation Error: {e}")

            time.sleep(1)  # be gentle with the free API
            print(f"  [GDELT] Found {len(articles)} articles.")
            return articles
        except Exception as e:
            print(f"  [GDELT] Error: {e}")
            return []
