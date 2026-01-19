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
    
    # 2. Iterate over Investing Themes
    themes = config.INVESTING_THEMES
    
    for theme_id, theme_data in themes.items():
        if not theme_data.get("enabled", False):
            print(f"\n[SKIP] Theme '{theme_data['name']}' is DISABLED or FROZEN.")
            continue
            
        print(f"\n" + "="*40)
        print(f"🚀 PROCESSING THEME: {theme_data['name']}")
        print(f"ID: {theme_id}")
        print("="*40)
        
        # Get theme-specific output directories
        theme_dirs = config.get_theme_dirs(theme_id)
        
        # Get keywords for this theme
        terms = theme_data.get("keywords", [])
        print(f"Search Terms: {len(terms)}")
        
        # 3. Fetch Data (passing output context)
        # Note: We pass theme_dirs so adapters know where to save auxiliary files (CSVs)
        articles = manager.fetch_all(terms, output_dirs=theme_dirs)
        
        # 4. Save Results to Theme Data Folder
        if articles:
            # Save to the specific data folder for this theme
            manager.save_to_json(articles, output_dir=theme_dirs["DATA"])
        else:
            print(f"\nNo data found for theme: {theme_data['name']}")

    print("\n" + "="*60)
    print("All enabled themes processed.")

if __name__ == "__main__":
    main()
