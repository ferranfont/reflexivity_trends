"""
Reflexivity Trends - Graph Visualizer
Generates an interactive network graph of the theme using Neo4j data and PyVis.
"""

import os
import sys
import webbrowser
from dotenv import load_dotenv
from neo4j import GraphDatabase
from pyvis.network import Network

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class GraphVisualizer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def generate_theme_graph(self, theme_id, output_path):
        query = """
        MATCH (t:Theme {id: $theme_id})
        OPTIONAL MATCH (t)<-[:RELATED_TO_THEME]-(a:Article)
        OPTIONAL MATCH (a)-[:MENTIONS]->(e:Entity)
        RETURN t, a, e
        LIMIT 200
        """
        
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white", cdn_resources='remote')
        net.force_atlas_2based()
        
        # Add Theme Node data
        theme_name = config.INVESTING_THEMES.get(theme_id, {}).get("name", theme_id)
        
        # We need to track added nodes to avoid duplicates if PyVis doesn't handle them automatically (it does usually if IDs match)
        # But Neo4j objects need to be converted to IDs.
        
        nodes_added = set()
        
        with self.driver.session() as session:
            result = session.run(query, theme_id=theme_id)
            
            for record in result:
                t_node = record['t']
                a_node = record['a']
                e_node = record['e']
                
                # Theme Node
                if t_node:
                    t_id = f"Theme_{t_node['id']}"
                    if t_id not in nodes_added:
                        net.add_node(t_id, label=t_node['name'], title=t_node['name'], color='#FF4500', size=30)
                        nodes_added.add(t_id)
                
                # Article Node
                if a_node:
                    a_id = f"Article_{a_node.element_id}" # or use URL/Title hash if element_id varies
                    # Using hash of URL for consistency
                    a_id = f"Article_{hash(a_node.get('url', ''))}"
                    
                    if a_id not in nodes_added:
                        title = a_node.get('title', 'No Title')
                        sentiment = a_node.get('sentiment', 0)
                        # Color based on sentiment?
                        color = '#00FF00' if sentiment > 0.1 else '#FF0000' if sentiment < -0.1 else '#CCCCCC'
                        
                        net.add_node(a_id, label=title[:20]+"...", title=title, color=color, size=15)
                        nodes_added.add(a_id)
                    
                    # Edge Theme -> Article
                    net.add_edge(t_id, a_id, color='rgba(255,255,255,0.3)')

                    # Entity Node
                    if e_node:
                        e_name = e_node.get('name', 'Unknown')
                        e_id = f"Entity_{e_name}"
                        
                        if e_id not in nodes_added:
                            net.add_node(e_id, label=e_name, title=e_name, color='#1E90FF', size=10)
                            nodes_added.add(e_id)
                        
                        # Edge Article -> Entity
                        net.add_edge(a_id, e_id, color='rgba(255,255,255,0.1)')

        # --- Add Legend Nodes (Visual Hack for PyVis) ---
        # We place them far away or just add them so they appear.
        # Alternatively, we can assume the user sees the colors.
        # Better approach: Add independent nodes representing the legend categories.
        
        legend_x = -1000
        legend_y = -1000
        step_y = 100
        
        # Legend: Theme
        net.add_node("Leg_Theme", label="Theme (Invest Thesis)", color='#FF4500', size=20, x=legend_x, y=legend_y, physics=False, shape='box')
        # Legend: Positive
        net.add_node("Leg_Pos", label="Article (Positive)", color='#00FF00', size=20, x=legend_x, y=legend_y+step_y, physics=False, shape='box')
        # Legend: Negative
        net.add_node("Leg_Neg", label="Article (Negative)", color='#FF0000', size=20, x=legend_x, y=legend_y+(step_y*2), physics=False, shape='box')
        # Legend: Entity
        net.add_node("Leg_Ent", label="Entity (Company/Tech)", color='#1E90FF', size=20, x=legend_x, y=legend_y+(step_y*3), physics=False, shape='box')
        
        # Save
        print(f"Generating graph with {len(net.nodes)} nodes...")
        try:
           net.save_graph(output_path)
           print(f"Graph saved to: {output_path}")
        except Exception as e:
           print(f"Error saving graph: {e}")

def explore_theme(theme_id):
    if not NEO4J_PASSWORD:
        print("Skipping Graph Viz: No Neo4j Password.")
        return

    print(f"\n[Graph Viz] Generating network for: {theme_id}")
    
    # Correct path handling
    theme_dirs = config.get_theme_dirs(theme_id)
    viz_dir = theme_dirs["VISUALIZATION"]
    output_file = os.path.join(viz_dir, "graph_network.html")
    
    viz = GraphVisualizer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    try:
        viz.generate_theme_graph(theme_id, output_file)
        
        # Auto-open in browser
        print("Opening Graph in browser...")
        try:
            webbrowser.get('chrome').open('file://' + output_file)
        except:
             # Fallback if chrome not registered specifically
            webbrowser.open('file://' + output_file)
            
    except Exception as e:
        print(f"Graph Viz Error: {e}")
    finally:
        viz.close()

if __name__ == "__main__":
    explore_theme("cybersecurity_ai")
