"""
SEC EDGAR full-text search article adapter (Capa C - Los informados).

Free official SEC full-text search API (filings since 2001), no key.
What companies SAY in regulatory filings is the factual counterweight to the
media/retail narrative: 8-K material events, S-1 risk factors, 10-K language.
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

API_URL = "https://efts.sec.gov/LATEST/search-index"


class EdgarFullTextAdapter(BaseSource):
    """Searches recent SEC filings mentioning the query phrase."""

    def __init__(self, max_records: int = 20, forms: str = "8-K,10-K,10-Q,S-1"):
        self.max_records = max_records
        self.forms = forms
        self.source_id = "edgar_fts"
        self.headers = {"User-Agent": config.EDGAR_USER_AGENT}

    def fetch(self, query: str) -> List[StandardArticle]:
        print(f"  [EDGAR-FTS] Searching filings for: {query}...")
        params = {
            "q": f'"{query}"',
            "forms": self.forms,
        }
        try:
            resp = requests.get(API_URL, params=params, headers=self.headers, timeout=45)
            resp.raise_for_status()
            hits = resp.json().get("hits", {}).get("hits", [])[: self.max_records]
            articles: List[StandardArticle] = []

            for hit in hits:
                src = hit.get("_source", {})
                names = src.get("display_names", [])
                company = names[0] if names else "Unknown filer"
                form = src.get("file_type") or src.get("form", "")
                file_date = src.get("file_date", "")

                # _id format: "0001234567-26-000123:document.htm"
                doc_id = hit.get("_id", "")
                adsh, _, filename = doc_id.partition(":")
                ciks = src.get("ciks", [])
                if ciks and adsh and filename:
                    cik_int = int(ciks[0])
                    url = (
                        f"https://www.sec.gov/Archives/edgar/data/{cik_int}/"
                        f"{adsh.replace('-', '')}/{filename}"
                    )
                else:
                    url = "https://www.sec.gov/cgi-bin/srqsb?text=" + adsh

                article_data = {
                    "source_id": self.source_id,
                    "source_name": "SEC EDGAR",
                    "title": f"{company} - {form} filing mentions '{query}'",
                    "url": url,
                    "published_date": file_date,
                    "abstract": (
                        f"Regulatory filing ({form}) by {company} dated {file_date} "
                        f"containing the phrase '{query}'."
                    ),
                    "full_text": None,
                    "metadata": {
                        "form_type": form,
                        "accession_number": adsh,
                        "ciks": ciks,
                        "display_names": names,
                    },
                }
                try:
                    articles.append(ArticleModel(**article_data).model_dump())
                except Exception as e:
                    print(f"  [EDGAR-FTS] Validation Error: {e}")

            time.sleep(0.2)  # SEC fair-use pacing
            print(f"  [EDGAR-FTS] Found {len(articles)} filings.")
            return articles
        except Exception as e:
            print(f"  [EDGAR-FTS] Error: {e}")
            return []
