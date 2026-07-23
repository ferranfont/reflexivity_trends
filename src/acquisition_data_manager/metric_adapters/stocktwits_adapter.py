"""
StockTwits metric adapter (Capa A - Multitud retail).

Public API, no key required for the symbol stream (30 most recent messages).
Users self-label messages Bullish/Bearish -> clean retail sentiment without NLP.
The academically strongest signal is message VOLUME and its acceleration,
so we derive msgs/hour from the timestamps of the latest stream page.

Metrics produced (snapshot for today):
  st_msgs_per_hour  - posting rate over the latest 30 messages
  st_bull_ratio     - bullish / (bullish + bearish) among labeled messages
  st_labeled_share  - fraction of messages carrying any label (engagement proxy)

NOTE: StockTwits occasionally blocks datacenter IPs / non-browser agents (403).
The adapter degrades gracefully; daily snapshots via cron accumulate history.
"""

import os
import sys
import time
from datetime import datetime, timezone
from typing import List, Dict, Any

import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
import config
from src.acquisition_data_manager.base_source import BaseMetricSource, StandardMetric

API_TMPL = "https://api.stocktwits.com/api/2/streams/symbol/{symbol}.json"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


class StockTwitsAdapter(BaseMetricSource):
    source_id = "stocktwits"

    def fetch_metrics(self, theme_id: str, theme_config: Dict[str, Any]) -> List[StandardMetric]:
        tickers = theme_config.get("tickers", [])
        if not tickers:
            print("  [StockTwits] No 'tickers' configured for this theme. Skipping.")
            return []

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        points: List[StandardMetric] = []

        for ticker in tickers:
            try:
                resp = requests.get(
                    API_TMPL.format(symbol=ticker), headers=BROWSER_HEADERS, timeout=30
                )
                if resp.status_code in (403, 429, 503):
                    is_cf = "just a moment" in resp.text[:400].lower() or "cf-" in resp.headers.get("Server", "").lower()
                    if is_cf:
                        print(
                            "  [StockTwits] Cloudflare challenge — the free endpoint is no longer "
                            "reachable server-side. Use the official StockTwits API (free token, "
                            "requires registration) or a residential proxy. Skipping ticker stream."
                        )
                        return points  # whole source is gated; no point looping every ticker
                    print(f"  [StockTwits] Blocked/rate-limited for {ticker} (HTTP {resp.status_code}).")
                    time.sleep(2)
                    continue
                resp.raise_for_status()
                messages = resp.json().get("messages", [])
                if not messages:
                    continue

                bullish = bearish = labeled = 0
                timestamps = []
                for msg in messages:
                    ts = msg.get("created_at")
                    if ts:
                        timestamps.append(datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
                    sentiment = (msg.get("entities") or {}).get("sentiment") or {}
                    basic = sentiment.get("basic")
                    if basic:
                        labeled += 1
                        if basic == "Bullish":
                            bullish += 1
                        elif basic == "Bearish":
                            bearish += 1

                n = len(messages)
                meta = {"n_messages": n, "bullish": bullish, "bearish": bearish}

                if len(timestamps) >= 2:
                    span_hours = max(
                        (max(timestamps) - min(timestamps)).total_seconds() / 3600.0, 0.05
                    )
                    points.append(StandardMetric(
                        source_id=self.source_id, entity=ticker, metric="st_msgs_per_hour",
                        event_date=today, value=round(n / span_hours, 3), metadata=meta,
                    ))
                if bullish + bearish > 0:
                    points.append(StandardMetric(
                        source_id=self.source_id, entity=ticker, metric="st_bull_ratio",
                        event_date=today, value=round(bullish / (bullish + bearish), 3), metadata=meta,
                    ))
                points.append(StandardMetric(
                    source_id=self.source_id, entity=ticker, metric="st_labeled_share",
                    event_date=today, value=round(labeled / n, 3), metadata=meta,
                ))
                time.sleep(1)
            except Exception as e:
                print(f"  [StockTwits] Error for {ticker}: {e}")

        print(f"  [StockTwits] Collected {len(points)} points for {len(tickers)} tickers.")
        return points
