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

try:
    from src.acquisition_data_manager.acquisition_manager import UnifiedAcquisitionManager
except ImportError:
    try:
        from .acquisition_manager import UnifiedAcquisitionManager
    except ImportError:
        from acquisition_manager import UnifiedAcquisitionManager

def main(target_theme=None):
    print("="*60)
    print("REFLEXIVITY TRENDS - UNIFIED DATA ACQUISITION")
    print("="*60)
    
    # 1. Initialize Manager
    manager = UnifiedAcquisitionManager()
    
    # 2. Iterate over Investing Themes
    all_themes = config.INVESTING_THEMES
    
    if target_theme:
        if target_theme not in all_themes:
            print(f"Error: Theme '{target_theme}' not found in configuration.")
            return
        # Filter to just the target theme
        themes_to_process = {target_theme: all_themes[target_theme]}
        print(f"🎯 Target Mode: Processing ONLY theme '{target_theme}'")
    else:
        themes_to_process = all_themes
        print(f"🔄 Bulk Mode: Processing ALL enabled themes")
    
    for theme_id, theme_data in themes_to_process.items():
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
    print("Acquisition process completed.")

if __name__ == "__main__":
    # helper for manual run
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", help="Specific theme to run")
    args = parser.parse_args()
    main(target_theme=args.theme)
