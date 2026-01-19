"""
Unified Acquisition CLI
This script uses the UnifiedAcquisitionManager to fetch data from all enabled sources
defined in config.py.
"""

import sys
import os

# Add root directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

from acquisition_manager import UnifiedAcquisitionManager

def main():
    print("="*60)
    print("REFLEXIVITY TRENDS - UNIFIED DATA ACQUISITION")
    print("="*60)
    
    # 1. Initialize Manager
    manager = UnifiedAcquisitionManager()
    
    # 2. Get Search Terms
    terms = config.DEFAULT_SEARCH_TERMS
    print(f"\nSearch Terms: {len(terms)}")
    
    # 3. Fetch Data
    articles = manager.fetch_all(terms)
    
    # 4. Save Results
    if articles:
        manager.save_to_json(articles)
    else:
        print("\nNo data found from any source.")

if __name__ == "__main__":
    main()
