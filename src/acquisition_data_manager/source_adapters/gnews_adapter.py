import sys
import os
from datetime import datetime
from typing import List
from gnews import GNews
from ..base_source import BaseSource, StandardArticle

# Add root directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

class GNewsAdapter(BaseSource):
    """
    Adapter for GNews library to fetch news articles.
    """
    
    def __init__(self):
        self.client = GNews(
            language=config.GNEWS_LANGUAGE,
            country=config.GNEWS_COUNTRY,
            period=config.GNEWS_PERIOD,
            max_results=config.GNEWS_MAX_RESULTS,
            exclude_websites=['youtube.com', 'facebook.com', 'twitter.com']
        )
        self.source_id = "gnews"

    def fetch(self, query: str) -> List[StandardArticle]:
        print(f"  [GNews] Searching for: {query}...")
        try:
            results = self.client.get_news(query)
            articles: List[StandardArticle] = []
            
            for item in results:
                # GNews returns: title, description, published date, url, publisher
                
                # Check for description
                snippet = item.get("description", "")
                if not snippet or snippet == " ":
                    snippet = item.get("title", "") # Fallback to title

                article: StandardArticle = {
                    "source_id": self.source_id,
                    "source_name": item.get("publisher", {}).get("title", "Google News"),
                    "title": item.get("title", "No Title"),
                    "url": item.get("url", ""),
                    "published_date": item.get("published date", datetime.now().isoformat()),
                    "abstract": snippet,
                    "full_text": None, # GNews listing doesn't have full text
                    "metadata": {
                        "original_publisher": item.get("publisher", {})
                    }
                }
                articles.append(article)
                
            print(f"  [GNews] Found {len(articles)} articles.")
            return articles
            
        except Exception as e:
            print(f"  [GNews] Error: {e}")
            return []
