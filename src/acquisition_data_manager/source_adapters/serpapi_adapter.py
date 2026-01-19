import sys
import os
from datetime import datetime
from typing import List
from serpapi import GoogleSearch
from ..base_source import BaseSource, StandardArticle
import json

# Add root directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

class SerpApiTrendsAdapter(BaseSource):
    """
    Adapter for Google Trends via SerpApi.
    Converts Time-Series trend data into a 'News Article' format 
    so it can be ingested by the same pipeline.
    """
    
    def __init__(self):
        self.api_key = config.SERPAPI_API_KEY
        self.source_id = "serpapi_trends"
        
        if not self.api_key:
            print("  [SerpApi] WARNING: No API Key found in config or environment.")

    def fetch(self, query: str) -> List[StandardArticle]:
        if not self.api_key:
            return []
            
        print(f"  [SerpApi] Fetching Trends data for: {query}...")
        
        params = {
          "engine": "google_trends",
          "q": query,
          "data_type": "TIMESERIES",
          "api_key": self.api_key
        }

        try:
            search = GoogleSearch(params)
            results = search.get_dict()
            
            articles: List[StandardArticle] = []
            
            if "interest_over_time" in results:
                timeline = results["interest_over_time"].get("timeline_data", [])
                if not timeline:
                    return []
                
                # Create a "summary" article representing the trend
                # We analyze the last few data points to see direction
                last_points = timeline[-5:]
                trend_values = [p.get("values", [{}])[0].get("extracted_value", 0) for p in last_points]
                
                start_date = timeline[0]["date"]
                end_date = timeline[-1]["date"]
                avg_value = sum(trend_values) / len(trend_values) if trend_values else 0
                
                # Construct a textual abstract of the trend
                abstract = (
                   f"Google Trends analysis for '{query}' from {start_date} to {end_date}. "
                   f"Recent interest levels: {trend_values}. "
                   f"Average interest: {avg_value:.1f}/100. "
                )
                
                article: StandardArticle = {
                    "source_id": self.source_id,
                    "source_name": "Google Trends (SerpApi)",
                    "title": f"Google Search Trend Analysis: {query}",
                    "url": "https://trends.google.com/trends/explore?q=" + query,
                    "published_date": datetime.now().isoformat(),
                    "abstract": abstract,
                    "full_text": json.dumps(timeline[:20]), # Store first 20 points as 'full text' raw data
                    "metadata": {
                        "average_interest": avg_value,
                        "data_points": len(timeline)
                    }
                }
                articles.append(article)
                print(f"  [SerpApi] Generated trend report.")
                
            return articles

        except Exception as e:
            print(f"  [SerpApi] Error: {e}")
            return []
