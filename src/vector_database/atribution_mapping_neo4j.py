"""
Análisis de Reflexividad con Neo4j Graph Database
Grafo Vectorial para búsqueda semántica de noticias de ciberseguridad

Usa los datos procesados por llama_LLM.py para:
1. Crear un grafo de conocimiento con noticias, empresas, categorías y fases
2. Almacenar embeddings vectoriales para búsqueda semántica
3. Permitir consultas Cypher avanzadas y búsqueda por similitud
"""

import json
import os
from glob import glob
from datetime import datetime
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


# --- CONFIGURACIÓN ---
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")

# Neo4j Connection (Actualiza con tus credenciales)
# Para Neo4j Desktop: bolt://localhost:7687
# Para Neo4j Aura: neo4j+s://xxxx.databases.neo4j.io
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "tu_contraseña")

# Modelo de embeddings (gratuito y local)
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # 384 dimensiones


def find_latest_reflexivity_file():
    """Encuentra el archivo JSON de reflexividad más reciente."""
    pattern = os.path.join(DATA_DIR, "cybersecurity_reflexivity_*.json")
    files = glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getmtime)


def parse_entidades(entidades_str):
    """Parsea el string de entidades a lista."""
    if not entidades_str or entidades_str == '[]':
        return []
    try:
        if isinstance(entidades_str, str):
            return json.loads(entidades_str)
        return list(entidades_str) if entidades_str else []
    except:
        return []


class Neo4jReflexivityGraph:
    """Clase para manejar el grafo de reflexividad en Neo4j."""

    def __init__(self, uri, user, password):
        """Inicializa la conexión a Neo4j y el modelo de embeddings."""
        print("Conectando a Neo4j...")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

        # Verificar conexión
        try:
            self.driver.verify_connectivity()
            print(f"Conectado a Neo4j: {uri}")
        except Exception as e:
            print(f"ERROR: No se pudo conectar a Neo4j: {e}")
            print("\nAsegurate de:")
            print("1. Tener Neo4j Desktop instalado y corriendo")
            print("2. O tener una instancia de Neo4j Aura activa")
            print("3. Actualizar las credenciales en el archivo .env:")
            print("   NEO4J_URI=bolt://localhost:7687")
            print("   NEO4J_USER=neo4j")
            print("   NEO4J_PASSWORD=tu_contraseña")
            raise

        print("Cargando modelo de embeddings...")
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        print(f"Modelo cargado: {EMBEDDING_MODEL}")

    def close(self):
        """Cierra la conexión."""
        self.driver.close()

    def setup_schema(self):
        """Crea índices y constraints en Neo4j."""
        print("\nConfigurando esquema de Neo4j...")

        with self.driver.session() as session:
            # Constraints para unicidad
            constraints = [
                "CREATE CONSTRAINT noticia_url IF NOT EXISTS FOR (n:Noticia) REQUIRE n.url IS UNIQUE",
                "CREATE CONSTRAINT empresa_nombre IF NOT EXISTS FOR (e:Empresa) REQUIRE e.nombre IS UNIQUE",
                "CREATE CONSTRAINT categoria_nombre IF NOT EXISTS FOR (c:Categoria) REQUIRE c.nombre IS UNIQUE",
                "CREATE CONSTRAINT fase_nombre IF NOT EXISTS FOR (f:FaseHype) REQUIRE f.nombre IS UNIQUE",
                "CREATE CONSTRAINT fuente_nombre IF NOT EXISTS FOR (s:Fuente) REQUIRE s.nombre IS UNIQUE",
            ]

            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    pass  # El constraint ya existe

            # Índice vectorial para búsqueda semántica
            try:
                session.run("""
                    CREATE VECTOR INDEX news_embeddings IF NOT EXISTS
                    FOR (n:Noticia) ON (n.embedding)
                    OPTIONS {indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }}
                """)
                print("Indice vectorial creado.")
            except Exception as e:
                print(f"Indice vectorial: {e}")

            # Índices para búsqueda rápida
            indices = [
                "CREATE INDEX noticia_sentimiento IF NOT EXISTS FOR (n:Noticia) ON (n.sentimiento)",
                "CREATE INDEX noticia_subjetividad IF NOT EXISTS FOR (n:Noticia) ON (n.subjetividad)",
                "CREATE INDEX noticia_fecha IF NOT EXISTS FOR (n:Noticia) ON (n.fecha)",
            ]

            for idx in indices:
                try:
                    session.run(idx)
                except:
                    pass

        print("Esquema configurado.")

    def ingest_noticia(self, tx, noticia, vector):
        """
        Crea un nodo Noticia y sus relaciones en el grafo.

        Estructura del grafo:
        (Noticia)-[:MENCIONA]->(Empresa)
        (Noticia)-[:PERTENECE_A]->(Categoria)
        (Noticia)-[:EN_FASE]->(FaseHype)
        (Noticia)-[:PUBLICADO_POR]->(Fuente)
        """
        query = """
        // Crear o actualizar nodo Noticia
        MERGE (n:Noticia {url: $url})
        SET n.titulo = $titulo,
            n.abstract = $abstract,
            n.fecha = $fecha,
            n.sentimiento = $sentimiento,
            n.subjetividad = $subjetividad,
            n.relevancia = $relevancia,
            n.razonamiento = $razonamiento,
            n.search_term = $search_term,
            n.embedding = $vector,
            n.updated_at = datetime()

        // Crear relación con Fuente
        WITH n
        MERGE (s:Fuente {nombre: $fuente})
        MERGE (n)-[:PUBLICADO_POR]->(s)

        // Crear relación con Categoría
        WITH n
        MERGE (c:Categoria {nombre: $categoria})
        MERGE (n)-[:PERTENECE_A]->(c)

        // Crear relación con Fase del Hype
        WITH n
        MERGE (f:FaseHype {nombre: $fase_hype})
        MERGE (n)-[:EN_FASE]->(f)

        // Crear relaciones con Empresas/Entidades
        WITH n
        UNWIND $entidades AS empresa_nombre
        MERGE (e:Empresa {nombre: empresa_nombre})
        MERGE (n)-[:MENCIONA]->(e)

        RETURN count(*) as created
        """

        entidades = parse_entidades(noticia.get('entidades', '[]'))

        tx.run(
            query,
            url=noticia.get('link', f"unknown_{hash(noticia.get('title', ''))}"),
            titulo=noticia.get('title', ''),
            abstract=str(noticia.get('abstract', ''))[:1000],
            fecha=noticia.get('date', ''),
            sentimiento=float(noticia.get('sentimiento', 0)),
            subjetividad=float(noticia.get('subjetividad', 0)),
            relevancia=float(noticia.get('relevancia_tendencia', 0)),
            razonamiento=noticia.get('razonamiento', ''),
            search_term=noticia.get('search_term', ''),
            fuente=noticia.get('source', 'Unknown'),
            categoria=noticia.get('categoria_cyber', 'General Cybersecurity'),
            fase_hype=noticia.get('fase_hype', 'Desconocido'),
            entidades=entidades if entidades else [],
            vector=vector
        )

    def ingest_all(self, datos):
        """Ingesta todos los datos en el grafo."""
        print(f"\nIniciando ingesta de {len(datos)} articulos...")

        with self.driver.session() as session:
            for i, noticia in enumerate(datos):
                # Saltar registros con errores
                if noticia.get('fase_hype') == 'ERROR':
                    continue

                # Generar embedding del texto
                texto = f"{noticia.get('title', '')} {noticia.get('razonamiento', '')} {noticia.get('abstract', '')[:200]}"
                vector = self.model.encode(texto).tolist()

                # Guardar en grafo
                session.execute_write(self.ingest_noticia, noticia, vector)

                if (i + 1) % 50 == 0:
                    print(f"  Procesados: {i + 1}/{len(datos)}")

        print(f"Ingesta completada: {len(datos)} articulos.")

    def query_similar(self, query_text, n_results=5, filters=None):
        """
        Busca noticias similares usando búsqueda vectorial.

        Args:
            query_text: Texto de búsqueda
            n_results: Número de resultados
            filters: Dict con filtros (sentimiento, subjetividad, categoria, etc.)
        """
        # Generar embedding de la consulta
        query_vector = self.model.encode(query_text).tolist()

        # Construir query Cypher
        where_clauses = []
        if filters:
            if 'sentimiento_min' in filters:
                where_clauses.append(f"n.sentimiento >= {filters['sentimiento_min']}")
            if 'sentimiento_max' in filters:
                where_clauses.append(f"n.sentimiento <= {filters['sentimiento_max']}")
            if 'subjetividad_max' in filters:
                where_clauses.append(f"n.subjetividad <= {filters['subjetividad_max']}")
            if 'subjetividad_min' in filters:
                where_clauses.append(f"n.subjetividad >= {filters['subjetividad_min']}")
            if 'categoria' in filters:
                where_clauses.append(f"n.categoria = '{filters['categoria']}'")

        where_clause = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

        query = f"""
        CALL db.index.vector.queryNodes('news_embeddings', $n_results, $query_vector)
        YIELD node AS n, score
        {where_clause}
        MATCH (n)-[:PUBLICADO_POR]->(s:Fuente)
        MATCH (n)-[:PERTENECE_A]->(c:Categoria)
        MATCH (n)-[:EN_FASE]->(f:FaseHype)
        OPTIONAL MATCH (n)-[:MENCIONA]->(e:Empresa)
        RETURN n.titulo AS titulo,
               n.url AS url,
               s.nombre AS fuente,
               c.nombre AS categoria,
               f.nombre AS fase_hype,
               n.sentimiento AS sentimiento,
               n.subjetividad AS subjetividad,
               n.razonamiento AS razonamiento,
               collect(DISTINCT e.nombre) AS entidades,
               score
        ORDER BY score DESC
        LIMIT $n_results
        """

        with self.driver.session() as session:
            result = session.run(query, query_vector=query_vector, n_results=n_results)
            return [dict(record) for record in result]

    def get_graph_stats(self):
        """Obtiene estadísticas del grafo."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Noticia) WITH count(n) as noticias
                MATCH (e:Empresa) WITH noticias, count(e) as empresas
                MATCH (c:Categoria) WITH noticias, empresas, count(c) as categorias
                MATCH (f:FaseHype) WITH noticias, empresas, categorias, count(f) as fases
                MATCH (s:Fuente) WITH noticias, empresas, categorias, fases, count(s) as fuentes
                RETURN noticias, empresas, categorias, fases, fuentes
            """)
            return dict(result.single())

    def get_top_entities(self, limit=10):
        """Obtiene las entidades más mencionadas."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (e:Empresa)<-[:MENCIONA]-(n:Noticia)
                RETURN e.nombre AS empresa, count(n) AS menciones
                ORDER BY menciones DESC
                LIMIT $limit
            """, limit=limit)
            return [dict(record) for record in result]

    def get_category_analysis(self):
        """Análisis por categoría."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Noticia)-[:PERTENECE_A]->(c:Categoria)
                RETURN c.nombre AS categoria,
                       count(n) AS total,
                       avg(n.sentimiento) AS sentimiento_promedio,
                       avg(n.subjetividad) AS subjetividad_promedio
                ORDER BY total DESC
            """)
            return [dict(record) for record in result]

    def get_hype_distribution(self):
        """Distribución por fase del hype."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Noticia)-[:EN_FASE]->(f:FaseHype)
                RETURN f.nombre AS fase,
                       count(n) AS total,
                       avg(n.sentimiento) AS sentimiento_promedio
                ORDER BY total DESC
            """)
            return [dict(record) for record in result]

    def find_bubble_candidates(self, subjetividad_min=0.6, sentimiento_min=0.5):
        """
        Encuentra candidatos a burbuja: alto sentimiento + alta subjetividad.
        Según Soros, cuando la narrativa supera la realidad, hay riesgo de burbuja.
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Noticia)-[:PERTENECE_A]->(c:Categoria)
                MATCH (n)-[:EN_FASE]->(f:FaseHype)
                WHERE n.subjetividad >= $subj_min AND n.sentimiento >= $sent_min
                RETURN n.titulo AS titulo,
                       c.nombre AS categoria,
                       f.nombre AS fase,
                       n.sentimiento AS sentimiento,
                       n.subjetividad AS subjetividad,
                       n.razonamiento AS razonamiento
                ORDER BY n.subjetividad DESC, n.sentimiento DESC
                LIMIT 10
            """, subj_min=subjetividad_min, sent_min=sentimiento_min)
            return [dict(record) for record in result]

    def find_opportunities(self, subjetividad_max=0.4, sentimiento_min=0.3):
        """
        Encuentra oportunidades: buenos fundamentales + baja especulación.
        Tecnologías consolidadas con hechos verificables.
        """
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n:Noticia)-[:PERTENECE_A]->(c:Categoria)
                MATCH (n)-[:EN_FASE]->(f:FaseHype)
                WHERE n.subjetividad <= $subj_max AND n.sentimiento >= $sent_min
                RETURN n.titulo AS titulo,
                       c.nombre AS categoria,
                       f.nombre AS fase,
                       n.sentimiento AS sentimiento,
                       n.subjetividad AS subjetividad,
                       n.razonamiento AS razonamiento
                ORDER BY n.sentimiento DESC, n.subjetividad ASC
                LIMIT 10
            """, subj_max=subjetividad_max, sent_min=sentimiento_min)
            return [dict(record) for record in result]


def print_results(results, title):
    """Imprime resultados de forma legible."""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)

    if not results:
        print("No se encontraron resultados.")
        return

    for i, r in enumerate(results, 1):
        print(f"\n[{i}]", end=" ")
        if 'score' in r:
            print(f"Similitud: {r['score']:.2%}")
        if 'titulo' in r:
            print(f"   Titulo: {r['titulo'][:70]}...")
        if 'fuente' in r:
            print(f"   Fuente: {r['fuente']}")
        if 'categoria' in r:
            print(f"   Categoria: {r['categoria']}")
        if 'fase' in r or 'fase_hype' in r:
            print(f"   Fase Hype: {r.get('fase') or r.get('fase_hype')}")
        if 'sentimiento' in r:
            print(f"   Sentimiento: {r['sentimiento']:.2f} | Subjetividad: {r.get('subjetividad', 0):.2f}")
        if 'razonamiento' in r and r['razonamiento']:
            print(f"   Razonamiento: {r['razonamiento']}")


def main(theme_id):
    """Función principal para ingesta por tema."""
    print("=" * 70)
    print(f"ANALISIS DE REFLEXIVIDAD CON NEO4J - Theme: {theme_id}")
    print("Grafo de Conocimiento + Busqueda Semantica Vectorial")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. Buscar archivo JSON más reciente (Usando Config)
    # Importar config de forma relativa si es necesario, pero ya está en sys.path
    try:
        import config
    except ImportError:
         sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
         import config
         
    theme_dirs = config.get_theme_dirs(theme_id)
    data_dir = theme_dirs["DATA"]
    pattern = os.path.join(data_dir, "analyzed_reflexivity_*.json")
    files = glob(pattern)
    
    if not files:
        print(f"\nERROR: No se encontraron archivos analizados en {data_dir}.")
        return

    json_file = max(files, key=os.path.getmtime)
    print(f"\nArchivo de datos: {json_file}")

    # 2. Cargar datos
    with open(json_file, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    print(f"Cargados {len(datos)} registros.")

    # 3. Conectar a Neo4j e ingestar datos
    try:
        graph = Neo4jReflexivityGraph(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
    except Exception as e:
        print(f"\nNo se pudo conectar a Neo4j. Verifica la configuracion.")
        return

    try:
        # Configurar esquema (Indices, Vectores)
        graph.setup_schema()

        # Ingestar datos (Embeddings + Grafo)
        graph.ingest_all(datos)

        # 4. Mostrar estadísticas simples
        print("\n" + "=" * 60)
        stats = graph.get_graph_stats()
        print(f"Estadísticas del Grafo: {stats}")

    except Exception as e:
        print(f"\nError durante el proceso: {e}")
        import traceback
        traceback.print_exc()

    finally:
        graph.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme", required=True, help="Theme ID")
    args = parser.parse_args()
    main(args.theme)
