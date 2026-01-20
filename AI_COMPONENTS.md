# Componentes de Inteligencia Artificial en Reflexivity Trends

Este proyecto no es una simple base de datos; es un sistema de múltiples capas de inteligencia artificial que trabajan en conjunto. Aquí está el desglose de **qué** se usa y **dónde**.

## 1. El "Analista Financiero" (LLM Generativo)
*   **Qué:** **Llama 3 (vía Groq API)**.
*   **Dónde:** En la fase de `Attribution Analysis` (`find_metadata_IA_llama_LLM.py`).
*   **Función:** Actúa como un experto humano que lee cada noticia. No solo resume, sino que **razona**.
*   **Algoritmo:** Large Language Model (Transformer Decoder-only).
*   **Output Inteligente:**
    *   `sentimiento`: Un valor numérico (-1 a 1) calculado por la comprensión lectora del modelo, no por palabras clave simples.
    *   `subjetividad`: El modelo juzga si el texto son hechos (0.1) o pura especulación/opinión (0.9).
    *   `fase_hype`: Clasifica el evento en la Curva de Gartner (Lanzamiento, Pico de Expectativas, Abismo de Desilusión).
    *   `razonamiento`: Redacta un párrafo explicando *por qué* es relevante para un inversor.

## 2. El "Traductor Matemático" (Embeddings Vectoriales)
*   **Qué:** **Sentence-Transformers (Modelo: `all-MiniLM-L6-v2`)**.
*   **Dónde:**
    1.  En la Ingesta (`atribution_mapping_neo4j.py`): Convierte las noticias procesadas en vectores.
    2.  En la Búsqueda (`neo4j_query_RAG_explorer.py`): Convierte tus preguntas en vectores.
*   **Función:** Transforma conceptos abstractos (palabras) en **puntos en un espacio geométrico multidimensional** (384 dimensiones).
*   **Algoritmo:** BERT (Bidirectional Encoder Representations from Transformers) optimizado (Siamese Networks) para calcular similitud coseno.
*   **Magia:** Permite que el sistema entienda que "defensa proactiva" es similar a "predicting attacks", aunque no compartan ninguna palabra.

## 3. El "Conector de Conocimiento" (Grafos)
*   **Qué:** **Neo4j Graph Database**.
*   **Dónde:** En la Persistencia y Visualización.
*   **Función:** Modela la realidad como nodos interconectados `(Noticia)-[:HABLA_DE]->(Empresa)`.
*   **Algoritmo:** Aunque es una base de datos, la estructura de grafo permite algoritmos de **clustering** (ver qué empresas aparecen siempre juntas) y **centralidad** (descubrir cuál es la empresa más influyente en la narrativa actual).
*   **Visualización:** El script `graph_visualizer.py` usa algoritmos de **fuerza dirigida** (como Atlas 2) para organizar visualmente los nodos, revelando clústeres de temas de forma orgánica.

## Resumen del Flujo Inteligente
1.  **Llama 3** (Piensa y Etiqueta) ➔ 2. **SentenceTransformer** (Entiende y Vectoriza) ➔ 3. **Neo4j** (Conecta y Relaciona).
