"""
SEC EDGAR insider-activity metric adapter (Capa C - Los informados).

Free official SEC APIs, no key. SEC requires a descriptive User-Agent with
contact info (config.EDGAR_USER_AGENT) and asks for <=10 req/sec.

Reflexivity rationale: when the retail narrative heats up while insiders file
Form 4 (mostly sales at bubble tops), that divergence IS the Soros signal.

Metrics produced (per configured ticker):
  edgar_form4_count_30d - number of Form 4 filings in the last 30 days
  edgar_form4_count_7d  - same, last 7 days (acceleration)
  edgar_8k_count_30d    - material-event filings (news-flow proxy from the company itself)
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import config
from src.acquisition_data_manager.base_source import BaseMetricSource, StandardMetric

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_TMPL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
CACHE_PATH = os.path.join(config.BASE_DIR, "data", "metrics", "sec_company_tickers.json")


class EdgarInsiderAdapter(BaseMetricSource):
    source_id = "edgar"

    def __init__(self):
        self.headers = {"User-Agent": config.EDGAR_USER_AGENT}
        self._ticker_to_cik = None

    def _load_ticker_map(self) -> Dict[str, int]:
        if self._ticker_to_cik is not None:
            return self._ticker_to_cik
        data = None
        # Cache the ~1MB mapping for 7 days
        if os.path.exists(CACHE_PATH) and (
            time.time() - os.path.getmtime(CACHE_PATH) < 7 * 86400
        ):
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        if data is None:
            resp = requests.get(TICKER_MAP_URL, headers=self.headers, timeout=45)
            resp.raise_for_status()
            data = resp.json()
            os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
            with open(CACHE_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f)
        self._ticker_to_cik = {
            v["ticker"].upper(): int(v["cik_str"]) for v in data.values()
        }
        return self._ticker_to_cik

    def fetch_metrics(self, theme_id: str, theme_config: Dict[str, Any]) -> List[StandardMetric]:
        tickers = theme_config.get("tickers", [])
        if not tickers:
            print("  [EDGAR] No 'tickers' configured for this theme. Skipping.")
            return []

        try:
            cik_map = self._load_ticker_map()
        except Exception as e:
            print(f"  [EDGAR] Could not load ticker->CIK map: {e}")
            return []

        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        d7 = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        d30 = (now - timedelta(days=30)).strftime("%Y-%m-%d")
        points: List[StandardMetric] = []

        for ticker in tickers:
            cik = cik_map.get(ticker.upper())
            if not cik:
                print(f"  [EDGAR] Ticker not found in SEC map: {ticker}")
                continue
            try:
                resp = requests.get(
                    SUBMISSIONS_TMPL.format(cik=cik), headers=self.headers, timeout=45
                )
                resp.raise_for_status()
                recent = resp.json().get("filings", {}).get("recent", {})
                forms = recent.get("form", [])
                dates = recent.get("filingDate", [])

                f4_30 = f4_7 = k8_30 = 0
                for form, fdate in zip(forms, dates):
                    if fdate >= d30:
                        if form == "4":
                            f4_30 += 1
                            if fdate >= d7:
                                f4_7 += 1
                        elif form == "8-K":
                            k8_30 += 1

                meta = {"cik": cik}
                points.extend([
                    StandardMetric(source_id=self.source_id, entity=ticker,
                                   metric="edgar_form4_count_30d", event_date=today,
                                   value=float(f4_30), metadata=meta),
                    StandardMetric(source_id=self.source_id, entity=ticker,
                                   metric="edgar_form4_count_7d", event_date=today,
                                   value=float(f4_7), metadata=meta),
                    StandardMetric(source_id=self.source_id, entity=ticker,
                                   metric="edgar_8k_count_30d", event_date=today,
                                   value=float(k8_30), metadata=meta),
                ])
                time.sleep(0.15)  # SEC fair-use pacing
            except Exception as e:
                print(f"  [EDGAR] Error for {ticker}: {e}")

        print(f"  [EDGAR] Collected {len(points)} points for {len(tickers)} tickers.")
        return points
