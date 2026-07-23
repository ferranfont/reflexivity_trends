# Reflexivity Trends — README V2

> Documento de referencia tras la implementación del **plan de I+D** (ver [plan_I+D.md](plan_I+D.md)).
> Explica **cómo funcionaba el sistema original (V1)**, **qué añade la V2** y **cómo operarlo hoy**.
> Fecha: Julio 2026.

---

## 0. En una frase

El proyecto aplica la **Teoría de la Reflexividad de Soros** para detectar burbujas narrativas (tipo Tesla, Bitcoin, NVIDIA): momentos en que la multitud desinformada se sincroniza y empuja una tendencia más allá de lo razonable. La **V1** hacía una *foto* del sentimiento de las noticias en un instante. La **V2** añade la dimensión que faltaba para que eso sea ciencia y no anécdota: **tiempo, múltiples fuentes contrastadas y trazabilidad point-in-time**.

---

## 1. Cómo funcionaba ANTES (V1)

La V1 es un **pipeline lineal de 4 pasos**, orquestado por [main_pipeline.py](main_pipeline.py). Cada paso deja un artefacto en disco que alimenta al siguiente.

```
┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 1. ADQUISICN │──▶│ 2. ANÁLISIS  │──▶│ 3. PERSIST.  │──▶│ 4. VISUALIZ. │
│    (GNews)   │   │ (Llama 3/LLM)│   │   (Neo4j)    │   │ (dashboards) │
└──────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
 unified_data_    analyzed_          grafo +            HTML matriz +
 *.json           reflexivity_*.json embeddings         grafo + RAG
```

### Paso 1 — Adquisición de noticias
- **Script:** [main_news_fetcher.py](src/acquisition_data_manager/main_news_fetcher.py) → `UnifiedAcquisitionManager`.
- **Fuente:** Google News (`gnews`), con SerpApi opcional. Arquitectura de *adapters* (`BaseSource.fetch(query)`) que normaliza todo a un `ArticleModel` (título, url, fecha, abstract, fuente).
- **Salida:** `data/<tema>/unified_data_*.json` (artículos crudos).

### Paso 2 — Análisis de atribución con LLM
- **Script:** [find_metadata_IA_llama_LLM.py](src/attribution_analysis/find_metadata_IA_llama_LLM.py).
- **Modelo:** **Llama 3.3 70B** vía **Groq API** (`temperature=0.1`, salida JSON estricta).
- **Qué hace:** lee cada noticia y, con un prompt de analista experto en reflexividad, extrae:
  - `sentimiento` (−1 a 1): euforia vs. pánico.
  - `subjetividad` (0 a 1): hechos verificables vs. especulación/hype.
  - `fase_hype`: etapa del **Gartner Hype Cycle** (Lanzamiento → Expectativas Infladas → Abismo de Desilusión → Consolidación → Madurez).
  - `entidades`, `categoria`, `razonamiento`, `relevancia_tendencia`.
- **Salida:** `data/<tema>/analyzed_reflexivity_*.json` (noticias enriquecidas).

### Paso 3 — Persistencia en grafo de conocimiento
- **Script:** [atribution_mapping_neo4j.py](src/vector_database/atribution_mapping_neo4j.py).
- **Base de datos:** **Neo4j** (Desktop o Aura). Modela la narrativa como grafo:
  `(Noticia)-[:MENCIONA]->(Empresa)`, `-[:PERTENECE_A]->(Categoria)`, `-[:EN_FASE]->(FaseHype)`, `-[:PUBLICADO_POR]->(Fuente)`.
- **Búsqueda semántica:** genera **embeddings** con `all-MiniLM-L6-v2` (384 dim, `sentence-transformers`) y crea un **índice vectorial coseno** en Neo4j → permite "chatear" con las noticias por significado, no por palabra clave.

### Paso 4 — Visualización
- **Matriz de reflexividad** ([dashboard_generator.py](src/visualization/dashboard_generator.py)): scatter **sentimiento × subjetividad**. Zona roja (alto+alto) = riesgo de burbuja; verde (alto sentimiento + baja subjetividad) = oportunidad sólida.
- **Grafo interactivo** ([graph_visualizer.py](src/visualization/graph_visualizer.py)): clústeres de empresas/temas por fuerza dirigida.
- **Explorador RAG** ([neo4j_query_RAG_explorer.py](src/vector_database/neo4j_query_RAG_explorer.py)): búsqueda vectorial estilo chat.

### El modelo de reflexividad de la V1 y sus **límites**

La V1 clasifica cada noticia en la matriz sentimiento×subjetividad. Es útil, pero es una **foto estática y de una sola fuente**:

| Limitación V1 | Consecuencia |
|---|---|
| **Sin dimensión temporal** | No se puede ver si una narrativa *acelera* o cuánto *precede* al pico de precio. La reflexividad es un fenómeno dinámico; una foto no lo captura. |
| **Una sola población (noticias)** | Mide *hype*, no *divergencia*. Sin contrastar la multitud contra los informados, no hay señal reflexiva real, solo sentimiento. |
| **Sin point-in-time** | No se puede reconstruir "qué se sabía en la fecha X" → cualquier backtest tendría *look-ahead bias* (miraría el futuro). |

La V2 ataca exactamente estas tres carencias.

---

## 2. Qué añade la V2

La idea central del plan: **la señal reflexiva es relacional**, no un score de sentimiento. Se construye sobre tres magnitudes observables, y para medirlas hacen falta **varias capas de fuentes contrastadas a lo largo del tiempo**.

| Magnitud (Soros) | Qué mide | Cómo se captura |
|---|---|---|
| **Divergencia** | Distancia entre la multitud desinformada y los hechos/informados | Comparar capa retail vs. capa insider/fundamental |
| **Sincronización** | Todo el mundo cuenta la misma historia (muere la diversidad narrativa) | Entropía de tópicos, similitud entre fuentes |
| **Contagio** | Velocidad de propagación nicho → mainstream | Series temporales de menciones, modelos epidémicos |

### Las 5 capas de fuentes (todas gratuitas, sin API key)

```
Capa A · Multitud retail      → StockTwits        (el que se sincroniza)
Capa B · Atención agregada    → Wikipedia         (comportamiento, no opinión)
Capa C · Los informados       → SEC EDGAR         (insiders: Form 4, 8-K)
Capa D · Consenso informado   → Polymarket        (probabilidad con dinero real)
Capa E · Contagio mediático   → GDELT             (amplitud mundial de la narrativa)
```

La **divergencia** entre Capa A (retail entusiasta) y Capa C (insiders vendiendo) es la señal de burbuja de manual de Soros.

### Novedades técnicas

1. **Point-in-time (doble timestamp).** Cada dato guarda `event_date` (cuándo ocurrió) e `ingestion_time` (cuándo lo supimos). Ver [models.py](src/models.py). Sin esto no hay backtest honesto posible.
2. **Almacén de series temporales** append-only en SQLite: [metrics_store.py](src/timeseries_store/metrics_store.py). Guarda cada snapshot sin sobreescribir → se puede reconstruir el pasado tal como se veía en vivo.
3. **Snapshot diario** [snapshot_daily.py](snapshot_daily.py): el "cron" que acumula el dataset. **Este es el activo diferencial del proyecto**: el histórico point-in-time solo se construye viviendo hacia delante.
4. **Adapters de métricas** en [metric_adapters/](src/acquisition_data_manager/metric_adapters/) (5 fuentes).
5. **Adapters de artículos nuevos** (GDELT global + SEC EDGAR full-text) que entran **solos** en el pipeline LLM de la V1 sin tocarlo.
6. **Dashboard de series temporales** [timeseries_dashboard.py](src/visualization/timeseries_dashboard.py): un panel por capa, con paleta de color validada como accesible (daltonismo).

> La V1 **no se ha tocado ni roto**: sigue funcionando igual. La V2 es una capa nueva y paralela que reutiliza su arquitectura de adapters y su pipeline LLM.

---

## 3. Estado real por fuente (prueba en vivo, 23-07-2026)

Se ejecutó el snapshot real: **370 puntos almacenados** en la primera corrida.

| Capa | Fuente | Estado | Notas |
|---|---|---|---|
| B | **Wikipedia Pageviews** | ✅ Funciona | 248 puntos/día, 8 páginas. Gratis, histórica desde 2015, no manipulable. **La joya.** |
| C | **SEC EDGAR** (Form 4 + 8-K) | ✅ Funciona | 18 puntos, 6 tickers. Sin fricción. Cuando el retail compra y los insiders venden → reflexividad medible. |
| E | **GDELT** | ✅ Funciona | Con *backoff*: su API gratuita limita fuerte (~1 req/5s), por eso pausa entre keywords. En un cron 1×/día no molesta. |
| D | **Polymarket** | ✅ Correcto, ⚠️ sin datos aquí | El código funciona (verificado contra la API). Los mercados top son política/cripto/macro; **ciberseguridad es categoría fina**. Se activará solo en temas cripto/macro. Es lo previsto en el plan. |
| A | **StockTwits** | ⚠️ Bloqueado | Su endpoint gratuito quedó **detrás de Cloudflare** (devuelve un desafío JS, no datos). No es un bug del código: es un cierre suyo, la misma tendencia que Reddit/X en 2023-26. El adapter lo detecta y corta limpio. |

---

## 4. Cómo se ejecuta

### Requisitos
No hay dependencias nuevas: `requests`, `pandas` y `plotly` ya estaban; `sqlite3` es de la stdlib. (La V1 sigue necesitando `groq`, `neo4j` y `sentence-transformers`.)

### Comandos

```bash
# --- V2: acumulación de métricas (esto va en el cron) ---
python snapshot_daily.py --theme cybersecurity_ai

# --- V2: dashboard de las series acumuladas ---
python -m src.visualization.timeseries_dashboard --theme cybersecurity_ai

# --- V1: pipeline clásico (ahora con GDELT y EDGAR full-text incluidos) ---
python main_pipeline.py --theme cybersecurity_ai
```

### Programar el cron (Windows Task Scheduler), 1 vez al día

```powershell
schtasks /create /tn "ReflexivitySnapshot" ^
  /tr "python C:\Users\ferra\Desktop\Algos\reflexivity_trends\snapshot_daily.py" ^
  /sc daily /st 07:00
```

> **Empieza el cron hoy.** Las APIs solo dan el presente; cada día sin snapshot es un día de histórico perdido para siempre.

---

## 5. La única alta que requiere registro (opcional y gratis)

Todo lo anterior funciona **sin darse de alta en nada**. La única capa que hoy no recolecta es la **A (multitud retail)**, que es el corazón del sistema Soros. Para recuperarla hay dos vías gratuitas:

1. **API oficial de StockTwits** — token gratuito, pero requiere registrarse como developer y OAuth. El adapter ya está escrito; solo habría que añadirle la cabecera del token. **Recomendada.**
2. **Reddit vía proveedor tercero** (p. ej. Xpoz, tier gratuito hasta ~400k resultados/mes) — requiere alta y API key.

**Recomendación:** deja correr el cron unas semanas para acumular histórico con las 3 capas que ya funcionan (B, C, E). Cuando quieras cerrar la Capa A, date de alta en la **API oficial de StockTwits**. Ninguna otra fuente del plan necesita registro.

---

## 6. Estructura de ficheros (lo nuevo de la V2)

```
reflexivity_trends/
├── plan_I+D.md                         # Estudio de fuentes + metodología científica
├── README_V2.md                        # (este documento)
├── snapshot_daily.py                   # ★ Cron de acumulación point-in-time
├── config.py                           # + flags de métricas, tickers, wikipedia_pages, market_keywords por tema
├── data/
│   └── metrics/metrics.sqlite          # ★ Almacén de series temporales (append-only)
└── src/
    ├── models.py                       # + ingestion_time, MetricPointModel
    ├── timeseries_store/
    │   └── metrics_store.py            # ★ API del almacén SQLite
    ├── acquisition_data_manager/
    │   ├── base_source.py              # + BaseMetricSource, StandardMetric
    │   ├── metric_adapters/            # ★ Adapters de métricas (series temporales)
    │   │   ├── wikipedia_pageviews_adapter.py
    │   │   ├── gdelt_volume_adapter.py
    │   │   ├── stocktwits_adapter.py
    │   │   ├── polymarket_adapter.py
    │   │   └── edgar_insider_adapter.py
    │   └── source_adapters/            # + adapters de artículos nuevos (→ pipeline LLM V1)
    │       ├── gdelt_adapter.py
    │       └── edgar_fulltext_adapter.py
    └── visualization/
        └── timeseries_dashboard.py     # ★ Dashboard por capas
```

---

## 7. Próximo paso científico (Fase 4 del plan)

Los índices **RDI** (divergencia), **NSI** (sincronización) y **R₀** (contagio) del §3 del plan **todavía no se calculan a propósito**: necesitan una serie de varios días/semanas para ser significativos. El siguiente entregable natural es:

- `src/analytics/reflexivity_indices.py` — computa RDI/NSI/R₀ sobre el almacén SQLite.
- Validación retrospectiva con casos etiquetados (GME 2021, BTC, TSLA, NVDA…) **con contra-ejemplos**, midiendo el *lead time* de cada métrica frente al pico de precio.

No tiene sentido construirlo hasta tener histórico acumulado. **Por eso, hoy, lo único que importa es que el cron esté corriendo.**

---

*Reflexivity Trends · La V1 mira el presente de una fuente; la V2 acumula el pasado de muchas para poder anticipar el futuro.*
