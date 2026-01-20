"""
Reflexivity Trends - Master Pipeline
Orchestrates the entire flow from data acquisition to visualization.

Usage:
    python run_pipeline.py --theme cybersecurity_ai
    python run_pipeline.py --all
"""

import os
import sys
import argparse
import time
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import config

# Import Modules
# We import main functions or use subprocess if they are scripts. 
# Importing is better for integration but requires they have a callable 'main' that accepts args or we pass args.
# For simplicity and isolation, we will import the main functions and call them.

from src.acquisition_data_manager import main_news_fetcher
from src.attribution_analysis import find_metadata_IA_llama_LLM
# from src.vector_database import loader_neo4j (Deleted)
from src.visualization import dashboard_generator

def run_theme_pipeline(theme_id, sample_mode=False):
    print("\n" + "#" * 80)
    print(f"🚀 STARTING PIPELINE FOR THEME: {theme_id}")
    print("#" * 80)

    # 1. ACQUISITION
    print(f"\n[Step 1/4] Acquisition (News & Trends)...")
    try:
        # Call acquisition with specific theme
        main_news_fetcher.main(target_theme=theme_id) 
    except Exception as e:
        print(f"❌ Acquisition Failed: {e}")
        return

    # 2. ATTRIBUTION (Analysis)
    print(f"\n[Step 2/4] Attribution Analysis (LLM)...")
    try:
        # This one accepts theme_id
        find_metadata_IA_llama_LLM.main(theme_id=theme_id, sample_mode=sample_mode)
    except Exception as e:
        print(f"❌ Analysis Failed: {e}")
        return

    # 3. PERSISTENCE (Neo4j + Vectors)
    print(f"\n[Step 3/4] Persistence (Neo4j & Vectors)...")
    try:
        from src.vector_database import atribution_mapping_neo4j
        atribution_mapping_neo4j.main(theme_id=theme_id)
    except Exception as e:
        print(f"❌ Database Loading Failed: {e}")
        # We continue even if DB fails, to show Dashboard
        
    # 4. VISUALIZATION (Graph & Dashboard)
    print(f"\n[Step 4/4] Visualization...")
    
    # 4a. Graph Visualization
    print(f"  > Generating Knowledge Graph...")
    try:
        from src.visualization import graph_visualizer
        graph_visualizer.explore_theme(theme_id)
    except Exception as e:
        print(f"  ❌ Graph Viz Failed: {e}")

    # 4b. Dashboard
    print(f"  > Generating Dashboard...")
    try:
        dashboard_generator.generate_dashboard(theme_id=theme_id)
    except Exception as e:
        print(f"  ❌ Dashboard Failed: {e}")
        return

    print(f"\n✅ PIPELINE COMPLETED FOR: {theme_id}")


def main():
    parser = argparse.ArgumentParser(description="Run Reflexivity Trends Pipeline")
    parser.add_argument("--theme", type=str, help="Specific theme ID to process")
    parser.add_argument("--all", action="store_true", help="Process all enabled themes")
    parser.add_argument("--sample", action="store_true", help="Run in sample mode (faster, fewer articles)")
    
    args = parser.parse_args()

    if args.theme:
        if args.theme not in config.INVESTING_THEMES:
            print(f"Error: Theme '{args.theme}' not found in config.")
            return
        run_theme_pipeline(args.theme, sample_mode=args.sample)
        
    elif args.all:
        for theme_id, settings in config.INVESTING_THEMES.items():
            if settings["enabled"]:
                run_theme_pipeline(theme_id, sample_mode=args.sample)
    else:
        print("Please specify --theme <id> or --all")

if __name__ == "__main__":
    main()
