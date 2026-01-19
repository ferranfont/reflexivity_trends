"""
Reflexivity Trends - Neo4j Loader
Ingests analyzed thematic data into the Neo4j Knowledge Graph.

Graph Schema:
(Theme {id, name}) <-[:RELATED_TO_THEME]- (Article {title, sentiment, subjectivity}) -[:MENTIONS]-> (Entity {name})
"""

import os
import sys
import json
import glob
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

# Cargar variables de entorno
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class Neo4jLoader:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def clean_theme_data(self, theme_id):
        """
        Optional: Remove existing articles for this theme to avoid duplicates/stale data.
        Keeps the Theme node itself, but detaches relations.
        """
        query = """
        MATCH (a:Article)-[:RELATED_TO_THEME]->(t:Theme {id: $theme_id})
        DETACH DELETE a
        """
        with self.driver.session() as session:
            session.run(query, theme_id=theme_id)
            print(f"  [Neo4j] Cleaned old articles for theme: {theme_id}")

    def create_theme_node(self, theme_id, theme_name):
        query = """
        MERGE (t:Theme {id: $theme_id})
        ON CREATE SET t.name = $theme_name, t.created_at = timestamp()
        ON MATCH SET t.last_updated = timestamp()
        RETURN t
        """
        with self.driver.session() as session:
            session.run(query, theme_id=theme_id, theme_name=theme_name)
            print(f"  [Neo4j] Merged Theme Node: {theme_id}")

    def load_data(self, theme_id, articles_data):
        """
        Loads a list of article dictionaries into the graph.
        """
        query_article = """
        MATCH (t:Theme {id: $theme_id})
        MERGE (a:Article {url: $url})
        SET a.title = $title,
            a.sentiment = $sentiment,
            a.subjectivity = $subjectivity,
            a.hype_phase = $hype_phase,
            a.category = $category,
            a.reasoning = $reasoning,
            a.date = $date,
            a.source = $source
        MERGE (a)-[:RELATED_TO_THEME]->(t)
        RETURN a
        """
        
        query_entity = """
        MATCH (a:Article {url: $url})
        MERGE (e:Entity {name: $entity_name})
        MERGE (a)-[:MENTIONS]->(e)
        """

        with self.driver.session() as session:
            for article in articles_data:
                # 1. Create Article Node
                session.run(query_article, 
                            theme_id=theme_id,
                            url=article.get("url", "no_url_" + str(hash(article.get("title")))),
                            title=article.get("title", "No Title"),
                            sentiment=article.get("sentimiento", 0),
                            subjectivity=article.get("subjetividad", 0),
                            hype_phase=article.get("fase_hype", "Unknown"),
                            category=article.get("categoria_theme", "General"),
                            reasoning=article.get("razonamiento", ""),
                            date=article.get("published_date", ""),
                            source=article.get("source_name", "Aggregator")
                )
                
                # 2. Create Entity Nodes
                entities = article.get("entidades", [])
                # entities might be a JSON string if loaded from CSV/JSON dump improperly, or a list
                if isinstance(entities, str):
                    try:
                        entities = json.loads(entities)
                    except:
                        entities = [entities]
                
                for entity_name in entities:
                    if entity_name and isinstance(entity_name, str):
                        session.run(query_entity, 
                                    url=article.get("url", "no_url_" + str(hash(article.get("title")))),
                                    entity_name=entity_name.strip())
            
            print(f"  [Neo4j] Ingested {len(articles_data)} articles and their entities.")


def main(theme_id):
    print("=" * 70)
    print(f"NEO4J LOADER: {theme_id}")
    print("=" * 70)

    if not NEO4J_PASSWORD:
        print("Error: NEO4J_PASSWORD not found in .env")
        return

    # 1. Locate Data
    theme_dirs = config.get_theme_dirs(theme_id)
    data_dir = theme_dirs["DATA"]
    
    # Priority: Analyzed files
    pattern = os.path.join(data_dir, "analyzed_reflexivity_*.json")
    files = glob.glob(pattern)
    
    if not files:
        print(f"Error: No analyzed data found in {data_dir}. Run attribution first.")
        return
        
    input_file = max(files, key=os.path.getmtime)
    print(f"Loading data from: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 2. Connect to Neo4j
    loader = Neo4jLoader(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    
    try:
        # 3. Setup Theme
        theme_name = config.INVESTING_THEMES[theme_id]["name"]
        loader.create_theme_node(theme_id, theme_name)
        
        # 4. Clean previous (optional, for idempotent runs per batch)
        # un-comment if you want to wipe previous articles for this theme every run
        # loader.clean_theme_data(theme_id)
        
        # 5. Load
        loader.load_data(theme_id, data)
        
    except Exception as e:
        print(f"Neo4j Error: {e}")
    finally:
        loader.close()
        print("Connection closed.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load theme data into Neo4j")
    parser.add_argument("--theme", type=str, required=True, help="Theme ID from config.py")
    args = parser.parse_args()
    
    main(args.theme)
