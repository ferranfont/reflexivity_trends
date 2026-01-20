
"""
Neo4j Database Explorer
Un script interactivo para explorar tu base de datos Neo4j como si fueran tablas SQL.
"""

import os
import sys
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Configuración de rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

# Cargar entorno
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

class Neo4jExplorer:
    def __init__(self, uri, user, password):
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            self.driver.verify_connectivity()
            print("✅ Conectado a Neo4j exitosamente.")
        except Exception as e:
            print(f"❌ Error conectando a Neo4j: {e}")
            sys.exit(1)

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters)
            # Convertir a lista de dicts
            return [dict(record) for record in result]

    def show_overview(self):
        """Muestra un resumen de cuantos nodos hay de cada tipo (Tablas)."""
        query = """
        MATCH (n)
        RETURN labels(n) as Tipo, count(n) as Cantidad
        ORDER BY Cantidad DESC
        """
        data = self.run_query(query)
        # Limpiar el formato de labels (viene como lista ['Article'], lo pasamos a string 'Article')
        clean_data = []
        for d in data:
            tipo = d['Tipo'][0] if d['Tipo'] else "Sin Etiqueta"
            clean_data.append({"Tabla (Nodo)": tipo, "Total Registros": d['Cantidad']})
        
        print("\n📊 RESUMEN DE LA BASE DE DATOS:")
        if clean_data:
            df = pd.DataFrame(clean_data)
            print(df.to_string(index=False))
        else:
            print("  (Base de datos vacía)")

    def show_table_content(self, label, limit=20):
        """Muestra el contenido de un nodo como si fuera una tabla (SELECT *)."""
        # Primero obtenemos las keys (columnas) dinámicamente
        query = f"MATCH (n:{label}) RETURN n LIMIT {limit}"
        
        data = self.run_query(query)
        if not data:
            print(f"\n⚠️ No hay registros en la tabla '{label}'.")
            return

        # Extraer propiedades de los nodos
        rows = []
        for record in data:
            node = record['n']
            rows.append(dict(node))

        print(f"\n📋 TABLA: {label} (Ultimos {limit} registros)")
        df = pd.DataFrame(rows)
        
        # Reordenar columnas si existen para que sea más legible
        priority_cols = ['title', 'name', 'sentimiento', 'fase_hype', 'subjetividad']
        cols = [c for c in priority_cols if c in df.columns] + [c for c in df.columns if c not in priority_cols]
        
        # Truncar textos largos para que quepa en la pantalla
        pd.set_option('display.max_colwidth', 50)
        pd.set_option('display.max_columns', 10)
        pd.set_option('display.width', 1000)
        
        print(df[cols].to_string())

    def custom_query(self):
        print("\n✍️ Escribe tu consulta Cypher (ej. MATCH (n) RETURN n LIMIT 5):")
        q = input("Cypher > ")
        try:
            data = self.run_query(q)
            if data:
                # Intentar aplanar si el resultado tiene nodos anidados
                flat_data = []
                for record in data:
                    row = {}
                    for k, v in record.items():
                        if hasattr(v, 'items'): # Si es un nodo/dict
                            for prop_k, prop_v in v.items():
                                row[f"{k}.{prop_k}"] = prop_v
                        else:
                            row[k] = v
                    flat_data.append(row)
                
                df = pd.DataFrame(flat_data)
                print(df.to_string())
            else:
                print("✅ Consulta ejecutada (Sin resultados o vacía).")
        except Exception as e:
            print(f"❌ Error en la consulta: {e}")

def main():
    if not NEO4J_PASSWORD:
        print("Error: Falta NEO4J_PASSWORD en .env")
        return

    explorer = Neo4jExplorer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    while True:
        print("\n" + "="*50)
        print("🔍 NEO4J DATABASE EXPLORER")
        print("="*50)
        print("1. Ver Resumen (Tablas disponibles)")
        print("2. Ver Tabla 'Theme' (Temas)")
        print("3. Ver Tabla 'Article' (Noticias)")
        print("4. Ver Tabla 'Entity' (Empresas/Entidades)")
        print("5. Consulta Personalizada")
        print("0. Salir")
        
        choice = input("\nElige una opción: ")

        if choice == '1':
            explorer.show_overview()
        elif choice == '2':
            explorer.show_table_content("Theme")
        elif choice == '3':
            explorer.show_table_content("Article", limit=10)
        elif choice == '4':
            explorer.show_table_content("Entity", limit=20)
        elif choice == '5':
            explorer.custom_query()
        elif choice == '0':
            print("Adiós! 👋")
            explorer.close()
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()
