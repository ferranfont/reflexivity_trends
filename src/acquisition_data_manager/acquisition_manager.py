import sys
import os
import json
from typing import List
from datetime import datetime

# Add root directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

from src.acquisition_data_manager.source_adapters.gnews_adapter import GNewsAdapter
from src.acquisition_data_manager.source_adapters.serpapi_adapter import SerpApiTrendsAdapter
from src.acquisition_data_manager.base_source import BaseSource, StandardArticle

class UnifiedAcquisitionManager:
    """
    Orchestrates data fetching from multiple sources.
    Uses config.py to determine which adapters to enable.
    """
    
    def __init__(self):
        self.sources: List[BaseSource] = []
        self._initialize_sources()
        
    def _initialize_sources(self):
        """Loads enabled adapters based on config"""
        print("Initializing Acquisition Manager...")
        
        if config.ENABLE_USE_GNEWS:
            print("  [+] GNews Adapter Enabled")
            self.sources.append(GNewsAdapter())
            
        if config.ENABLE_USE_SERPAPI_TRENDS:
            print("  [+] SerpApi Trends Adapter Enabled")
            self.sources.append(SerpApiTrendsAdapter())
            
        if config.ENABLE_USE_TWITTER:
            print("  [!] Twitter Adapter Enabled (Not Implemented)")
            # self.sources.append(TwitterAdapter())

    def fetch_all(self, search_terms: List[str], output_dirs=None) -> List[StandardArticle]:
        """
        Runs all enabled adapters for the given search terms.
        """
        all_articles: List[StandardArticle] = []
        
        for term in search_terms:
            print(f"\n--- Processing Term: '{term}' ---")
            for source in self.sources:
                try:
                    # Check if fetch accepts 'output_dirs' (new signature)
                    import inspect
                    sig = inspect.signature(source.fetch)
                    if 'output_dirs' in sig.parameters:
                        articles = source.fetch(term, output_dirs=output_dirs)
                    else:
                        articles = source.fetch(term)
                        
                    all_articles.extend(articles)
                except Exception as e:
                    print(f"Error fetching from {source}: {e}")
                    
        return all_articles
        
    def save_to_json(self, articles: List[StandardArticle], filename: str = None, output_dir: str = None):
        """Saves the aggregated results to a JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"unified_data_{timestamp}.json"
            
        # Use provided output_dir or default to legacy path
        if output_dir:
            output_path = os.path.join(output_dir, filename)
        else:
            output_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", filename)
        
        # Ensure data dir exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
            
        print(f"\nSuccessfully saved {len(articles)} articles to: {output_path}")
        return output_path
