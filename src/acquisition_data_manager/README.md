# Acquisition Data Manager

Este módulo es el responsable de la **ingesta unificada de datos** para el sistema `reflexivity_trends`. Su objetivo es abstraer las diferentes fuentes de información (Google News, Google Trends, Redes Sociales, etc.) y proporcionar una salida estandarizada para el análisis posterior.

## 🏗️ Arquitectura

El sistema utiliza el patrón de diseño **Strategy/Adapter** para gestionar múltiples fuentes de datos de manera modular.

### Componentes Principales

1.  **`main_news_fetcher.py` (Entry Point)**:
    *   Es el script ejecutable (CLI).
    *   Inicializa el Manager, lee la configuración y orquesta la ejecución.
    *   **Uso**: `python src/acquisition_data_manager/main_news_fetcher.py`

2.  **`acquisition_manager.py` (The Manager)**:
    *   Clase `UnifiedAcquisitionManager`.
    *   Lee `config.py` de la raíz del proyecto para determinar qué adaptadores activar.
    *   Itera sobre todos los adaptadores habilitados, ejecuta las búsquedas y consolida los resultados en una única lista.

3.  **`base_source.py` (The Contract)**:
    *   Clase abstracta `BaseSource` y definición de tipo `StandardArticle`.
    *   Define la interfaz obligatoria que debe cumplir cualquier nueva fuente de datos.
    *   Asegura que todos los datos salgan con el mismo formato JSON (título, url, abstract, etc.).

4.  **`source_adapters/` (The Adapters)**:
    *   Contiene las implementaciones específicas para cada API o servicio.
    *   `gnews_adapter.py`: Conecta con librería `gnews` (gratuita).
    *   `serpapi_adapter.py`: Conecta con la API de SerpApi para obtener Google Trends (Time Series) y lo convierte a formato "noticia" (resumen textual).

## ⚙️ Configuración

El comportamiento se controla desde el archivo `config.py` en la raíz del proyecto:

```python
# config.py

# Feature Flags: Activa/Desactiva fuentes
ENABLE_USE_GNEWS = True
ENABLE_USE_SERPAPI_TRENDS = True  # Requiere API Key en .env
ENABLE_USE_TWITTER = False

# Configuración de Búsqueda
DEFAULT_SEARCH_TERMS = ["AI Threat Detection", "CTEM", ...]
```

## 📝 Formato de Salida (Standard JSON)

Independientemente de la fuente, el sistema genera un archivo JSON unificado en `data/` con la siguiente estructura por artículo:

```json
{
  "source_id": "gnews",
  "source_name": "Google News",
  "title": "Titulo de la noticia",
  "url": "https://...",
  "published_date": "2024-01-01T10:00:00",
  "abstract": "Resumen o snippet del contenido...",
  "full_text": "Texto completo (opcional)",
  "metadata": { ... }
}
```

## 🚀 Cómo añadir una nueva fuente

1.  Crea un nuevo archivo en `source_adapters/` (ej: `twitter_adapter.py`).
2.  Crea una clase que herede de `BaseSource` e implementa el método `fetch(query)`.
3.  Asegúrate de devolver una lista de objetos `StandardArticle`.
4.  Añade un flag en `config.py` (ej: `ENABLE_USE_TWITTER`).
5.  Registra el nuevo adaptador en `acquisition_manager.py` dentro de `_initialize_sources()`.
