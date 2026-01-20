
"""
Neo4j RAG Explorer
Buscador semántico (RAG) para noticias de inversión.

Utiliza la librería `sentence-transformers` (Hugging Face) para convertir texto en vectores numéricos (embeddings).
Esta herramienta transforma tanto tus preguntas como las noticias almacenadas en representaciones matemáticas de su significado semántico.
Esto permite encontrar noticias conceptualmente similares a tu pregunta, incluso si no usan las mismas palabras exactas.

Permite hacer preguntas en lenguaje natural y encontrar noticias relevantes por su significado.
"""

import os
import sys
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Configuración rutas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

load_dotenv()

# Configuración
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

class RAGExplorer:
    def __init__(self):
        print("🔌 Conectando a Neo4j...")
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.driver.verify_connectivity()
        
        print("🧠 Cargando modelo de lenguaje (Embeddings)...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        print("✅ Sistema listo para consultas.")

    def close(self):
        self.driver.close()

    def semantic_search(self, query_text, limit=5, min_score=0.5):
        """
        Realiza una búsqueda vectorial:
        1. Convierte la pregunta del usuario en un vector numérico.
        2. Busca en Neo4j los artículos cuyos vectores sean matemáticamente cercanos.
        """
        # 1. Vectorizar la consulta
        query_vector = self.model.encode(query_text).tolist()

        # 2. Consulta Cypher usando el índice vectorial
        cypher_query = """
        CALL db.index.vector.queryNodes('news_embeddings', $limit, $query_vector)
        YIELD node AS n, score
        WHERE score >= $min_score
        RETURN n.titulo AS Titulo, 
               n.razonamiento AS Razonamiento, 
               n.sentimiento AS Sentimiento,
               n.fase_hype AS Fase,
               score AS Similitud
        """

        with self.driver.session() as session:
            result = session.run(cypher_query, 
                                 query_vector=query_vector, 
                                 limit=limit, 
                                 min_score=min_score)
            return [dict(record) for record in result]

def main():
    if not NEO4J_PASSWORD:
        print("Error: Configura NEO4J_PASSWORD en .env")
        return

    rag = RAGExplorer()

    print("\n" + "="*60)
    print("🤖 BUSCADOR SEMÁNTICO (RAG) DE INVERSIONES")
    print("   Pregunta sobre tendencias, riesgos o tecnologías.")
    print("="*60)

    while True:
        question = input("\nPregunta (o 'salir'): ")
        if question.lower() in ['salir', 'exit', '0']:
            break

        print(f"🔍 Buscando conceptos relacionados con: '{question}'...")
        
        try:
            results = rag.semantic_search(question)
            
            if not results:
                print("❌ No encontré noticias relevantes para esa consulta.")
            else:
                print(f"\n✅ Encontradas {len(results)} noticias relevantes:\n")
                for i, r in enumerate(results, 1):
                    similitud = r['Similitud'] * 100
                    print(f"{i}. [{similitud:.1f}%] {r['Titulo']}")
                    print(f"   💡 Contexto: {r['Razonamiento'][:200]}...")
                    print(f"   📊 Sentimiento: {r['Sentimiento']:.2f} | Fase: {r['Fase']}")
                    print("-" * 40)
                    
        except Exception as e:
            print(f"Error en la búsqueda: {e}")
            print("Consejo: Asegúrate de que el índice 'news_embeddings' existe en Neo4j.")

    rag.close()

if __name__ == "__main__":
    main()
