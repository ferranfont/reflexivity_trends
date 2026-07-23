"""
Polymarket metric adapter (Capa D - Consenso informado / contraste).

Free Gamma API, no key, no wallet needed for read-only data.
Role in the reflexivity framework: prediction-market prices are the closest
thing to an objective consensus probability (money at stake). The reflexive
signal is the DIVERGENCE between the retail/media narrative and these odds.

Strategy: fetch top open markets by volume and keep those whose question
matches any of the theme's 'market_keywords' (client-side filter = robust
against API query-param changes).

Metrics produced (snapshot for today, per matched market):
  pm_prob_yes    - implied probability of the YES outcome
  pm_volume_usd  - lifetime volume (liquidity/attention proxy)
"""

import os
import sys
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import config
from src.acquisition_data_manager.base_source import BaseMetricSource, StandardMetric

API_URL = "https://gamma-api.polymarket.com/markets"


class PolymarketAdapter(BaseMetricSource):
    source_id = "polymarket"

    def __init__(self, top_n_markets: int = 500):
        self.top_n = top_n_markets
        self.headers = {"User-Agent": config.HTTP_USER_AGENT}

    def fetch_metrics(self, theme_id: str, theme_config: Dict[str, Any]) -> List[StandardMetric]:
        keywords = [k.lower() for k in theme_config.get("market_keywords", [])]
        if not keywords:
            print("  [Polymarket] No 'market_keywords' configured for this theme. Skipping.")
            return []

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        points: List[StandardMetric] = []
        matched = 0

        try:
            fetched = 0
            offset = 0
            page_size = 100
            while fetched < self.top_n:
                params = {
                    "closed": "false",
                    "limit": page_size,
                    "offset": offset,
                    "order": "volumeNum",
                    "ascending": "false",
                }
                resp = requests.get(API_URL, params=params, headers=self.headers, timeout=45)
                resp.raise_for_status()
                markets = resp.json()
                if not markets:
                    break

                for m in markets:
                    question = (m.get("question") or "").lower()
                    if not any(kw in question for kw in keywords):
                        continue
                    matched += 1
                    slug = m.get("slug") or m.get("id", "unknown")
                    meta = {
                        "question": m.get("question"),
                        "end_date": m.get("endDate"),
                        "url": f"https://polymarket.com/market/{slug}",
                    }
                    # outcomePrices is a JSON-encoded list of strings, e.g. '["0.65", "0.35"]'
                    try:
                        prices = json.loads(m.get("outcomePrices") or "[]")
                        if prices:
                            points.append(StandardMetric(
                                source_id=self.source_id, entity=slug, metric="pm_prob_yes",
                                event_date=today, value=round(float(prices[0]), 4), metadata=meta,
                            ))
                    except (ValueError, TypeError):
                        pass
                    vol = m.get("volumeNum")
                    if vol is not None:
                        points.append(StandardMetric(
                            source_id=self.source_id, entity=slug, metric="pm_volume_usd",
                            event_date=today, value=round(float(vol), 2), metadata=meta,
                        ))

                fetched += len(markets)
                offset += page_size
                if len(markets) < page_size:
                    break
        except Exception as e:
            print(f"  [Polymarket] Error: {e}")

        print(f"  [Polymarket] Matched {matched} open markets; {len(points)} points.")
        return points
