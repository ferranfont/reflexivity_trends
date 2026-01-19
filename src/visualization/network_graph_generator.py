import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from pyvis.network import Network
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import sys

# Fix encoding for Windows console
sys.stdout.reconfigure(encoding='utf-8')

# Cargar variables de entorno
load_dotenv()

# Add project root to path
# Add project root to path
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(BASE_DIR)
import config


# --- 1. CONFIGURACIÓN (Desde .env) ---
URI = os.getenv("NEO4J_URI")
AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))

# --- 2. FUNCIÓN PARA OBTENER DATOS ---
def obtener_datos_grafo(tx):
    # Esta query trae: La Noticia (Origen) -> Relación -> La Empresa (Destino)
    query = """
    MATCH (n:Noticia)-[r:MENCIONA]->(e:Empresa)
    WHERE n.subjetividad < 0.5  // Filtramos solo noticias "serias" para el ejemplo
    RETURN n.titulo AS Fuente, type(r) AS Relacion, e.nombre AS Objetivo, n.sentimiento AS Sentimiento
    LIMIT 20
    """
    result = tx.run(query)
    return [record.data() for record in result]

# --- 3. EJECUCIÓN PRINCIPAL ---
def main():
    print("🔌 Conectando a Neo4j...")
    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        with driver.session() as session:
            datos = session.execute_read(obtener_datos_grafo)
        driver.close()
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return

    if not datos:
        print("⚠️ No se encontraron datos. Revisa tu base de datos o el filtro WHERE.")
        return

    # --- A) SALIDA EN TERMINAL (TABLA PANDAS) ---
    print("\n📊 MODO TERMINAL: Tabla de Datos")
    df = pd.DataFrame(datos)
    # Mostramos las primeras filas
    print(df.head(10))
    print("-" * 50)

    # --- PREPARAR EL GRAFO (NETWORKX) ---
    G = nx.DiGraph()  # Grafo dirigido
    for fila in datos:
        # Añadir nodos y aristas
        # Acortamos el título de la noticia para que se vea bien en el gráfico
        fuente_corta = fila['Fuente'][:15] + "..."
        G.add_edge(fuente_corta, fila['Objetivo'], weight=fila['Sentimiento'])

    # --- B) SALIDA PNG (IMAGEN ESTÁTICA) ---
    print("🖼️  GENERANDO PNG...")
    plt.figure(figsize=(12, 8))
    pos = nx.spring_layout(G, seed=42)  # Algoritmo de distribución para que no se amontonen

    # Dibujar nodos y conexiones
    nx.draw(G, pos, with_labels=True,
            node_color='skyblue',
            node_size=2000,
            font_size=9,
            font_weight='bold',
            edge_color='gray',
            arrowsize=20)

    plt.title("Grafo de Inversión Reflexiva (Matplotlib)")
    plt.title("Grafo de Inversión Reflexiva (Matplotlib)")
    png_path = os.path.join(config.DIRS["CHARTS_PNG"], "grafo_inversion.png")
    plt.savefig(png_path)
    print(f"✅ Imagen guardada como '{png_path}'")

    # --- C) SALIDA WEB (INTERACTIVA) ---
    print("🌐 GENERANDO WEB INTERACTIVA...")
    # Use cdn_resources='remote' to avoid creating a local 'lib' folder
    net = Network(notebook=False, height="750px", width="100%", bgcolor="#222222", font_color="white", cdn_resources='remote')

    # Convertir el grafo de NetworkX a Pyvis directamente
    net.from_nx(G)

    # Opciones de física para que las burbujas reboten bonito
    net.toggle_physics(True)

    # Guardar y abrir
    nombre_archivo = os.path.join(config.DIRS["CHARTS_HTML"], "grafo_interactivo.html")
    net.save_graph(nombre_archivo)
    print(f"✅ Archivo web guardado: {nombre_archivo}")

    # Intentar abrir automáticamente en el navegador (funciona en Windows/Mac)
    try:
        os.startfile(nombre_archivo)
    except AttributeError:
        # Para Linux o Mac si startfile no existe
        os.system(f"open {nombre_archivo}" if os.name == 'posix' else f"xdg-open {nombre_archivo}")

if __name__ == "__main__":
    main()
