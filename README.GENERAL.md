# Reflexivity Trends - Project Overview

## Arquitectura de Datos y Flujo de Información

Este documento explica cómo fluyen los datos a través del sistema y qué función cumple cada componente principal.

### 🔄 Flujo del Pipeline (`run_pipeline.py`)

1.  **Adquisición de Datos (Raw Data)**
    *   **Script:** `src/acquisition_data_manager/main_news_fetcher.py`
    *   **Fuente:** Google News, SerpApi, RSS.
    *   **Salida:** Archivos JSON con noticias crudas en `data/<theme>/unified_data_*.json`.
    *   **Contenido:** Título, enlace, fecha, fuente, texto completo/snippet.

2.  **Análisis de Atribución (IA / LLM)**
    *   **Script:** `src/attribution_analysis/find_metadata_IA_llama_LLM.py`
    *   **Proceso:** Lee las noticias crudas y las envía a Llama 3 (Groq) con un prompt de experto.
    *   **Salida:** Archivos JSON enriquecidos en `data/<theme>/analyzed_reflexivity_*.json`.
    *   **Datos Generados:**
        *   `sentimiento` (-1 a 1): Positividad/Negatividad del mercado.
        *   `subjetividad` (0 a 1): Nivel de especulación o hype.
        *   `fase_hype`: Etapa del ciclo (Lanzamiento, Pico, Desilusión, etc.).
        *   `entidades`: Lista de empresas o tecnologías clave mencionadas.

3.  **Persistencia (Base de Datos & Vectores)**
    *   **Script:** `src/vector_database/atribution_mapping_neo4j.py`
    *   **Proceso:** Lee el JSON enriquecido (analizado) y crea nodos y relaciones en **Neo4j**.
    *   **Esquema:** `(Tema) <-[RELATED]- (Noticia) -[MENTIONS]-> (Entidad)`.

4.  **Visualización (Salidas al Usuario)**

    *   **A. Dashboard Estratégico** (`src/visualization/dashboard_generator.py`)
        *   **Fuente de Datos:** Lee directamente los archivos **JSON Analizados** (`analyzed_reflexivity_*.json`).
        *   **Objetivo:** Análisis métrico, matrices de riesgo vs. oportunidad y lectura rápida.
        *   **Salida:** `outputs/<theme>/charts_html/dashboard_*.html`.

    *   **B. Grafo de Conocimiento** (`src/visualization/graph_visualizer.py`)
        *   **Fuente de Datos:** Consulta la base de datos **Neo4j**.
        *   **Objetivo:** Exploración interactiva de relaciones y conexiones entre empresas y noticias.
        *   **Salida:** `outputs/<theme>/visualization/graph_network.html`.
        *   **Leyenda de Colores:**
            *   🟠 **Naranja**: Tema de Inversión.
            *   🟢 **Verde**: Noticia Positiva.
            *   🔴 **Rojo**: Noticia Negativa.
            *   🔵 **Azul**: Entidad/Empresa.

    *   **C. Búsqueda Vectorial (RAG)** (`src/vector_database/neo4j_query_RAG_explorer.py`)
        *   **Fuente de Datos:** Embbedings vectoriales en Neo4j.
        *   **Tecnología IA:** Utiliza el modelo pre-entrenado **`all-MiniLM-L6-v2`** de Hugging Face (vía librería `sentence-transformers`).
        *   **Funcionamiento:** 
            1.  El modelo actúa como un "traductor" que convierte el texto humano (preguntas y noticias) en vectores matemáticos de 384 dimensiones.
            2.  Neo4j compara estos vectores numéricos para encontrar similitud conceptual.
            3.  Esto permite encontrar noticias relacionadas semánticamente aunque no compartan las mismas palabras clave exactas.
        *   **Objetivo:** Permitir al usuario "chatear" con la base de datos para encontrar noticias por significado conceptual, no solo por palabras clave.
        *   **Lógica Inteligente:** La búsqueda se realiza sobre la **Data Procesada**, aprovechando el sentimiento, razonamiento y fase de hype generados por la IA en el paso 2.

5.  **Exploración de la Base de Datos** (`src/vector_database/neo4j_query_explorer.py`)
    *   **Función:** Una herramienta estilo CLI/Menú para ver qué tablas (Nodos) existen en la base de datos y ver su contenido crudo en formato tabla. Útil para depuración y verificación rápida.

## Estructura de Directorios Clave

*   `src/`
    *   `acquisition_data_manager/`: Scripts de descarga de noticias.
    *   `attribution_analysis/`: Scripts de IA (LangChain/LLM) para enriquecer datos.
    *   `vector_database/`: Scripts de carga a Neo4j.
    *   `visualization/`: Generadores de Dashboards y Grafos.
*   `data/`: Almacena los JSONs crudos y analizados por tema.
*   `outputs/`: Almacena los reportes HTML y gráficos generados.
*   `config.py`: Configuración global de temas, claves y rutas.
