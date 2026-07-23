# Plan de I+D — Fuentes de Datos No Estructurados para un Sistema de Trading Reflexivo

> **Proyecto:** reflexivity_trends
> **Fecha:** Julio 2026
> **Objetivo:** Identificar, evaluar y priorizar fuentes de datos no estructurados que actúen como *precursoras* de tendencias reflexivas (burbujas narrativas al estilo Tesla, Bitcoin, NVIDIA), y definir una metodología científica para convertirlas en señal operable.

---

## 1. Marco teórico: qué estamos midiendo exactamente

La teoría de la reflexividad de Soros no dice "el sentimiento mueve precios". Dice algo más preciso y más medible:

1. Los participantes actúan sobre una **percepción sesgada** de la realidad (no sobre los fundamentales).
2. Sus acciones **alteran los fundamentales** que decían estar interpretando (feedback positivo: la subida del precio de Tesla le permitió financiarse barato, lo que mejoró sus fundamentales, lo que justificó la subida...).
3. La burbuja madura cuando los participantes **se sincronizan en una única narrativa** y la divergencia entre narrativa y hechos se hace insostenible.

De aquí se derivan **tres magnitudes observables** que deben guiar toda la selección de fuentes:

| Magnitud | Definición operativa | Qué fuente la captura |
|---|---|---|
| **Divergencia** | Distancia entre lo que dice la multitud desinformada y lo que dicen los hechos/los informados | Comparar capa retail vs. capa insider/fundamental |
| **Sincronización** | Colapso de la diversidad narrativa: todo el mundo cuenta la misma historia con las mismas palabras | Entropía de tópicos, similitud entre embeddings de distintas fuentes |
| **Contagio** | Velocidad y aceleración de propagación de la narrativa entre poblaciones (nicho → mainstream) | Series temporales de menciones/atención por fuente, modelos epidémicos |

**Principio rector:** ninguna fuente aislada es señal. La señal reflexiva es siempre **relacional** — una divergencia entre capas o una sincronización entre poblaciones. Esto es lo que distingue este enfoque de un simple "sentiment trading".

Base académica de partida (leer antes de escribir código):

- Shiller, *Narrative Economics* (NBER w23075, 2017): las narrativas se propagan como epidemias → justifica modelos SIR sobre menciones.
- Da, Engelberg & Gao, *In Search of Attention* (2011) y el índice *FEARS* (2015): el volumen de búsqueda de Google predice picos de atención retail y reversiones.
- Moat et al. (2013): visitas a Wikipedia como precursor de movimientos de mercado.
- Tetlock (2007): tono de medios y presión de precios.
- Baker & Wurgler (2006): índice de sentimiento del inversor como predictor de retornos en acciones "difíciles de valorar" (exactamente el universo Tesla/BTC/NVDA).
- Sornette, modelo **LPPLS** (log-periodic power law singularity): detección de burbujas por superexponencialidad del precio. Aunque es una señal de precio, sirve como **capa de confirmación independiente**, no como análisis técnico clásico. Trabajo reciente (2025) integra hype textual en LPPLS ("Hyped LPPLS").
- Literatura GameStop/WSB (2021-2023): evidencia empírica de sincronización retail medible en Reddit antes del squeeze.

---

## 2. Taxonomía de fuentes evaluadas

Cada fuente se evalúa en 5 ejes: **Señal esperada** (¿precursora o coincidente?), **Población que representa**, **Latencia**, **Coste/Acceso 2026**, **Riesgo** (manipulación, sesgo, supervivencia de la API).

### Capa A — La multitud desinformada (el corazón del sistema Soros)

Estos son los agentes que se sincronizan y empujan la tendencia más allá de lo razonable. Es la capa **precursora** por excelencia.

| Fuente | Señal | Acceso 2026 | Veredicto |
|---|---|---|---|
| **StockTwits** | Mensajes auto-etiquetados Bullish/Bearish por ticker → sentimiento retail sin necesidad de NLP propio. El *volumen* de mensajes y su aceleración es más predictivo que el sentimiento en sí | API pública con límites razonables | ⭐⭐⭐⭐⭐ **Prioridad 1.** Es la fuente académicamente más validada para retail |
| **Reddit** (r/wallstreetbets, r/stocks, subreddits temáticos) | Sincronización retail, lenguaje de manada ("to the moon", "diamond hands"), aparición de tickers nuevos en conversación | ⚠️ API oficial: $0.24/1k llamadas, mínimo $12k/año comercial; registro cerrado a autoaprobación. Alternativas de terceros (Xpoz, etc.) desde $0-20/mes | ⭐⭐⭐⭐ Alta señal, acceso degradado. Usar terceros o scraping de baja frecuencia sobre subreddits concretos |
| **X/Twitter** | Velocidad de propagación, influencers financieros, cashtags | ⚠️ Sin tier gratuito desde feb 2026; pay-per-use ($5/1k lecturas) o terceros ($0.05-0.20/1k) | ⭐⭐⭐ Cara para lo que aporta hoy. Postponer; cubrir la señal con StockTwits + Reddit |
| **YouTube** | Métrica infravalorada: nº de vídeos nuevos/semana sobre un tema, velocidad de views, ratio de canales "genéricos" (no financieros) que empiezan a cubrir el tema = señal de contagio nicho→mainstream | YouTube Data API gratuita (cuota diaria) | ⭐⭐⭐⭐ **Precursor de fase tardía**: cuando los canales de lifestyle hablan de NVDA, la burbuja está madura |
| **TikTok/Instagram** | Último eslabón del contagio (máximo desinformado) | Sin API práctica; terceros | ⭐⭐ Señal de "fase terminal" pero acceso frágil. Opcional, fase avanzada |

### Capa B — Atención agregada (proxy pasivo de la multitud)

No es opinión, es **comportamiento de búsqueda** — más difícil de manipular que las redes sociales y con literatura sólida detrás.

| Fuente | Señal | Acceso | Veredicto |
|---|---|---|---|
| **Wikipedia Pageviews API** | Visitas diarias a artículos (empresa, tecnología, persona). Precursor validado académicamente. Gratuita, histórica desde 2015, sin límites serios | Gratis, REST simple | ⭐⭐⭐⭐⭐ **Prioridad 1.** Coste cero, señal probada, nadie la manipula |
| **Google Trends** (ya parcialmente en el proyecto vía pytrends/SerpAPI) | Interés de búsqueda; el índice FEARS demuestra su valor. Limitación: datos normalizados 0-100, no absolutos | Gratis (frágil) / SerpAPI (ya integrado) | ⭐⭐⭐⭐ Ya tenéis el adapter. Sistematizarlo por tema |
| **App Store / Google Play rankings** (Robinhood, Coinbase, brokers) | El ranking de descargas de apps de brokers es un termómetro directo de entrada retail (validado en BTC 2021) | Scraping o APIs de terceros (SensorTower caro; scraping de rankings públicos viable) | ⭐⭐⭐⭐ Muy específico de burbujas retail. Barato de mantener |

### Capa C — Los informados (el contraste contra el que se mide la divergencia)

Sin esta capa no hay reflexividad medible: solo hype. Aquí es donde el proyecto se diferencia de un sentiment tracker cualquiera.

| Fuente | Señal | Acceso | Veredicto |
|---|---|---|---|
| **SEC EDGAR full-text search** | 8-K, S-1, 10-K, y sobre todo **Form 4 (ventas de insiders)**. Cuando la narrativa retail sube y los insiders venden → divergencia reflexiva de libro | Gratis, API oficial JSON | ⭐⭐⭐⭐⭐ **Prioridad 1.** Gratis, estructurado + no estructurado, imposible de manipular |
| **Transcripciones de earnings calls** | El lenguaje del management (evasividad, cambio de tono, densidad de buzzwords) vs. lo que la narrativa retail cree que dijeron. Literatura 2025 muestra que las narrativas de las calls predicen revisiones de analistas | Gratis con retardo (Motley Fool, Seeking Alpha scraping) o APIs (FinancialModelingPrep ~barato) | ⭐⭐⭐⭐ Encaja perfecto con vuestro pipeline LLM existente |
| **Ofertas de empleo** (LinkedIn/Indeed/Greenhouse scraping) | ¿La empresa contrata lo que la narrativa dice que hace? (Ej.: si el hype es "IA" y no contratan ML engineers → narrativa hueca) | Scraping medio | ⭐⭐⭐ Diferencial y original, pero laborioso. Fase 2-3 |
| **arXiv / patentes (Google Patents, USPTO)** | Sustancia técnica real detrás del hype tecnológico. Ratio papers-reales/menciones-en-prensa | Gratis (arXiv API, USPTO API) | ⭐⭐⭐ Para temas tech (como vuestro tema cybersecurity_ai actual) |

### Capa D — Mercados de predicción (Polymarket, Kalshi, PredictIt, Metaculus)

**Respuesta directa a tu pregunta:** sí, pero con un rol distinto al que probablemente imaginas.

- Un mercado de predicción **no es la multitud desinformada**: es una multitud con dinero en juego e incentivos a estar en lo cierto. Su precio es lo más parecido a una "probabilidad objetiva de consenso" que existe en tiempo real.
- Por tanto su uso correcto en un sistema reflexivo es como **capa C (contraste)**, no como capa A: cuando la narrativa mediática/retail sobre un evento diverge de la probabilidad que cotiza Polymarket/Kalshi, esa divergencia ES la señal reflexiva.
- Segundo uso: **resolución de eventos catalizadores**. Mercados sobre "¿aprobará la Fed X?", "¿ganará N el contrato Y?", "¿superará NVDA $Z de revenue?" (Kalshi tiene mercados de earnings) dan fechas y probabilidades para los catalizadores que pinchan o inflan burbujas.
- Estado 2026: **Polymarket** (líder de volumen, API CLOB gratuita para datos, order book + historial de trades + top holders), **Kalshi** (regulado CFTC, API REST limpia, datos accesibles sin KYC), **PredictIt** casi irrelevante ya — descártalo. Existen SDKs unificados open-source (PMXT, Python) y APIs unificadas (Tatum, Prediction Hunt).
- Limitación honesta: cobertura de single-stocks aún escasa; fuerte en macro, política, crypto y grandes tech. Para el tema BTC/macro es excelente; para una small-cap en burbuja no habrá mercado.

**Veredicto: ⭐⭐⭐⭐ Incorporar en Fase 3** como capa de consenso-informado y calendario de catalizadores, con la métrica explícita `divergencia = P(narrativa implícita) − P(mercado de predicción)`.

### Capa E — Medios estructurados a escala (mejora de lo que ya hay)

| Fuente | Señal | Acceso | Veredicto |
|---|---|---|---|
| **GDELT 2.0 (GKG)** | Todo el flujo mundial de noticias cada 15 min, con tono, temas y entidades ya extraídos. Escala que GNews no puede dar; permite medir *amplitud* del contagio (nº de outlets distintos, países, idiomas) | Gratis (BigQuery / ficheros CSV) | ⭐⭐⭐⭐⭐ **Prioridad 1.** Sustituye/complementa GNews para medir contagio geográfico y entre tipos de medio |
| **Common Crawl News / RSS masivo** | Texto completo cuando GDELT solo da metadatos | Gratis, pesado | ⭐⭐ Solo si GDELT se queda corto |
| **Podcasts (transcripciones vía Whisper)** | El contagio a podcasts generalistas es señal de fase tardía, análoga a YouTube | RSS de podcasts gratis + Whisper local | ⭐⭐⭐ Original, coste de cómputo moderado. Fase 3-4 |

### Qué NO incluir (y por qué)

- **Análisis técnico clásico** (medias, RSI...): excluido por diseño del proyecto. La única excepción admisible es **LPPLS** como test estadístico de superexponencialidad para *confirmar* que la narrativa detectada está ya reflejada en precio — es econofísica de burbujas, no chartismo.
- **Dark web / Telegram de pump&dump**: señal de manipulación más que de reflexividad orgánica; riesgo legal y de calidad de datos.
- **News sentiment comercial** (RavenPack, etc.): resuelve lo que ya resolvéis con Llama 3 + Groq, a precio institucional.

---

## 3. De fuentes a señal: las métricas que hay que construir

El error habitual es acumular fuentes y hacer "un score de sentimiento medio". Las métricas deben mapear 1:1 con las tres magnitudes del marco teórico:

### 3.1 Índice de Divergencia Reflexiva (RDI)
```
RDI(tema, t) = z_score(narrativa_retail) − z_score(señal_informada)
```
- `narrativa_retail`: compuesto de capa A+B (volumen StockTwits + pageviews Wikipedia + trends, normalizado).
- `señal_informada`: compuesto de capa C+D (insider selling invertido, tono de earnings call, probabilidad de mercado de predicción).
- Hipótesis H1: RDI alto y creciente precede a la fase final de la burbuja; el pico de RDI precede al pico de precio.

### 3.2 Índice de Sincronización Narrativa (NSI)
- Entropía de Shannon sobre la distribución de tópicos (BERTopic sobre vuestros embeddings existentes): cuando la entropía **colapsa** (todas las noticias cuentan la misma historia), la narrativa se ha sincronizado.
- Correlación media rodante entre las series de menciones de las distintas fuentes (¿Reddit, YouTube y prensa se mueven juntos?).
- Similitud coseno media entre embeddings de documentos de fuentes distintas en la misma ventana — ya tenéis `all-MiniLM-L6-v2` en producción para esto.
- Hipótesis H2: NSI alto = burbuja madura; la diversidad narrativa muere antes que la burbuja.

### 3.3 Índice de Contagio (R₀ narrativo)
- Ajustar un modelo epidémico **SIR** a la serie de menciones acumuladas por población (nicho financiero → prensa generalista → YouTube/TikTok), siguiendo a Shiller.
- Métrica derivada: **aceleración** (segunda derivada del volumen de menciones) y **lead-lag entre poblaciones** (¿Wikipedia lidera a la prensa? ¿Reddit lidera a Wikipedia?) vía correlación cruzada o *transfer entropy*.
- Hipótesis H3: la secuencia de contagio nicho→mainstream es medible y su fase indica el tiempo restante de la burbuja.

### 3.4 Métricas auxiliares
- **Novedad vs. reciclaje**: distancia de embeddings entre noticias nuevas y el corpus previo del tema. Las burbujas maduras *reciclan* narrativa (novedad baja, volumen alto).
- **Ratio hype**: subjetividad/sentimiento que ya calculáis con Llama 3 — se mantiene, pero pasa de ser LA señal a ser UN componente.
- **Confirmación de precio (opcional)**: test LPPLS sobre el activo asociado al tema.

---

## 4. Metodología científica: cómo hacer el camino

Esta es la parte más importante. El riesgo nº 1 del proyecto no es la falta de fuentes: es construir un sistema no falsable que "explique" cualquier cosa a posteriori.

### Regla 0 — Datos point-in-time o nada
Todo dato debe guardarse con **dos timestamps**: cuándo ocurrió y **cuándo lo supiste** (`event_time` vs `ingestion_time`). Sin esto, cualquier backtest tendrá look-ahead bias y los resultados serán ficción. Esto implica:
- Empezar a **acumular snapshots diarios ya** (las APIs dan el presente; el histórico point-in-time solo se construye viviendo hacia delante). Cada día de retraso es un día menos de dataset.
- Para el histórico: Wikipedia pageviews y GDELT sí tienen archivo real; StockTwits/Reddit parcialmente; Google Trends es re-normalizado (cuidado).

### Regla 1 — Casos de estudio retrospectivos antes que señal en vivo
Construir un **dataset etiquetado de burbujas conocidas** y validar que las métricas las habrían detectado:
- GameStop (ene 2021), Bitcoin (2017 y 2021), Tesla (2020), NVIDIA/IA (2023-24), SPACs (2021), cannabis (2018), hidrógeno (2020).
- Y —imprescindible— **contra-ejemplos**: subidas fuertes NO reflexivas (recuperación post-COVID de empresas value) y falsas alarmas (temas con hype que no llegaron a burbuja). Sin negativos no hay ciencia, solo confirmación.
- Para cada caso: reconstruir las series (Wikipedia y GDELT lo permiten hacia atrás), calcular RDI/NSI/R₀, y medir el **lead time**: ¿cuántos días antes del pico de precio picó cada métrica?

### Regla 2 — Hipótesis escritas antes de mirar los datos
Cada experimento se registra en `experiments/EXP-YYYY-NN.md` con: hipótesis, métrica de éxito predefinida (ej.: "RDI > 2σ precede al pico de precio en ≥70% de los casos con lead ≥10 días"), datos usados, resultado, decisión. Lo que no supera su criterio se descarta y se documenta. Este diario es el activo científico real del proyecto.

### Regla 3 — Validación estadística mínima
- **Causalidad de Granger / transfer entropy** entre cada métrica y los retornos: ¿la métrica lidera o solo acompaña?
- **Walk-forward**, nunca in-sample: los umbrales (2σ, etc.) se calibran en burbujas antiguas y se testean en las recientes.
- Corrección por comparaciones múltiples: con 10 fuentes y 10 métricas, algo correlacionará por azar. Bonferroni o al menos consciencia explícita del problema.
- Benchmark nulo: toda métrica nueva debe batir a la más tonta disponible (ej.: volumen bruto de menciones). La literatura advierte que a menudo el volumen simple bate al sentimiento sofisticado.

### Regla 4 — Del indicador a la operativa, al final
Solo cuando una métrica supere las reglas 1-3 se pasa a: definición de señal (entrada/salida), paper trading con registro, y evaluación por Sharpe/drawdown sobre régimen. La tentación de saltar directo aquí es la muerte del proyecto.

---

## 5. Roadmap por fases (aprovechando la arquitectura existente)

La arquitectura actual (adapters `BaseSource` → JSON unificado → LLM → Neo4j → dashboards) es correcta y extensible. No hay que rehacer nada: hay que añadir adapters y una capa de series temporales.

### Fase 0 — Fundamentos (1-2 semanas)
- Añadir `event_time` / `ingestion_time` a `src/models.py` y a todos los JSON.
- Crear un almacén de **series temporales diarias** por tema/entidad (un simple Parquet/SQLite por métrica basta; Neo4j no es el sitio para series).
- Cron diario que snapshotea todas las fuentes activas. **Empezar a acumular datos desde ya.**

### Fase 1 — Fuentes gratuitas de máxima señal (2-4 semanas)
- Adapter **Wikipedia Pageviews** (REST trivial, histórico desde 2015).
- Adapter **GDELT GKG** (tono + nº de outlets + países por tema → primera métrica de contagio).
- Adapter **SEC EDGAR** (full-text + Form 4 por entidades del tema).
- Sistematizar **Google Trends** con el adapter SerpAPI ya existente.
- Entregable: dashboard de series temporales por tema con las 4 fuentes superpuestas.

### Fase 2 — Multitud retail (3-4 semanas)
- Adapter **StockTwits** (volumen + ratio bullish/bearish por ticker).
- Adapter **Reddit** vía proveedor tercero de bajo coste (evaluar Xpoz o similar; presupuesto ~$20/mes) sobre 5-10 subreddits.
- Adapter **YouTube Data API**: vídeos/semana y velocidad de views por keywords del tema; clasificar canales financiero vs. generalista con el LLM ya integrado.
- Entregable: primera versión de RDI y NSI calculada diariamente.

### Fase 3 — Contraste informado y mercados de predicción (3-4 semanas)
- Adapter **earnings calls** (transcripciones → pipeline Llama 3 existente con prompt específico de evasividad/buzzwords).
- Adapter **Polymarket + Kalshi** (vía SDK unificado PMXT o APIs nativas): probabilidades + volumen de mercados relacionados con cada tema; calendario de catalizadores.
- Entregable: RDI completo (retail vs. informado) + panel de catalizadores.

### Fase 4 — Validación científica (4-6 semanas, en paralelo desde Fase 1)
- Reconstrucción retrospectiva de los casos etiquetados (§4 Regla 1) con Wikipedia+GDELT.
- Granger/transfer entropy, walk-forward, informe de lead-times.
- Decisión go/no-go documentada por métrica.

### Fase 5 — Señal en vivo (continuo)
- Métricas supervivientes → alertas (umbral z-score) → paper trading con diario.
- El modelo SIR y LPPLS se añaden aquí como refinamiento, no antes.

---

## 6. Presupuesto y riesgos

**Coste mensual estimado de la configuración recomendada:** ~$0-50/mes (Wikipedia, GDELT, EDGAR, YouTube, StockTwits, Polymarket/Kalshi datos = gratis; Reddit tercero ~$20; Groq ya presupuestado). Las fuentes caras (X a $5/1k lecturas, Reddit oficial a $12k/año) quedan explícitamente fuera hasta que algo gratuito demuestre techo de señal.

**Riesgos principales:**
1. **Supervivencia de APIs** (lección Reddit/X 2023-26): mitigar con la capa de adapters ya existente — cambiar de proveedor debe costar un fichero, no una refactorización. Priorizar fuentes institucionales (Wikimedia, GDELT, SEC) que no pueden cerrar el grifo.
2. **Manipulación** (bots en redes): mitigar ponderando fuentes no manipulables (Wikipedia, EDGAR, mercados de predicción con dinero real) en el RDI.
3. **Look-ahead bias**: mitigado por Regla 0. Es el riesgo silencioso más letal.
4. **Sobreajuste a 7 burbujas históricas**: n pequeño; ser humilde con las conclusiones, usar contra-ejemplos, y tratar el sistema como generador de *hipótesis de vigilancia*, no de señales automáticas, hasta acumular años de datos propios.
5. **Coste LLM creciente** con el volumen: reservar Llama 3 para el análisis profundo; usar los campos ya estructurados (StockTwits bullish/bearish, tono GDELT) donde el LLM no aporta.

---

## 7. Resumen ejecutivo (la respuesta corta)

1. **Las 4 incorporaciones de mayor valor/coste son: Wikipedia Pageviews, GDELT, SEC EDGAR (Form 4 + full-text) y StockTwits.** Todas gratis o casi, con literatura académica detrás, y cubren las tres capas (multitud, atención, informados).
2. **Polymarket/Kalshi: sí, pero como capa de contraste** (probabilidad de consenso con dinero real contra la que medir el exceso narrativo) y calendario de catalizadores — no como termómetro retail. PredictIt: descartar.
3. **La señal reflexiva es relacional**: divergencia entre capas (RDI), sincronización narrativa (NSI) y contagio entre poblaciones (R₀). Un score de sentimiento medio no es un sistema soros-iano.
4. **El camino científico**: point-in-time desde el día uno, validación retrospectiva sobre burbujas etiquetadas CON contra-ejemplos, hipótesis y criterios de éxito escritos antes de mirar los datos, y operativa solo al final.
5. **Empezar hoy a acumular snapshots**: el activo más valioso del proyecto dentro de dos años será el dataset point-in-time que nadie más tiene.

---

## 8. Estado de implementación (Julio 2026)

Se ha implementado la **Fase 0 + Fase 1** completas y parte de la 2/3, con **solo fuentes gratuitas y sin API key** (salvo una excepción opcional). Todo encaja en la arquitectura de adapters existente.

### Qué se ha construido

| Componente | Fichero | Estado |
|---|---|---|
| Point-in-time (doble timestamp) | `src/models.py` (`ArticleModel.ingestion_time`, `MetricPointModel`) | ✅ |
| Base de adapters de métricas | `src/acquisition_data_manager/base_source.py` (`BaseMetricSource`, `StandardMetric`) | ✅ |
| Almacén de series temporales SQLite append-only | `src/timeseries_store/metrics_store.py` | ✅ |
| Adapter Wikipedia Pageviews (Capa B) | `metric_adapters/wikipedia_pageviews_adapter.py` | ✅ Funciona |
| Adapter GDELT volumen (Capa E) | `metric_adapters/gdelt_volume_adapter.py` | ✅ Funciona (con backoff) |
| Adapter SEC EDGAR insiders/Form 4 (Capa C) | `metric_adapters/edgar_insider_adapter.py` | ✅ Funciona |
| Adapter Polymarket (Capa D) | `metric_adapters/polymarket_adapter.py` | ✅ Correcto; sin datos para *este* tema |
| Adapter StockTwits (Capa A) | `metric_adapters/stocktwits_adapter.py` | ⚠️ Bloqueado por Cloudflare (ver abajo) |
| Adapter GDELT artículos (→ LLM) | `source_adapters/gdelt_adapter.py` | ✅ Registrado en el manager |
| Adapter EDGAR full-text (→ LLM) | `source_adapters/edgar_fulltext_adapter.py` | ✅ Registrado en el manager |
| Cron de snapshot diario | `snapshot_daily.py` | ✅ Probado (370 puntos) |
| Dashboard de series temporales | `src/visualization/timeseries_dashboard.py` | ✅ Probado (paleta accesible validada) |

### Cómo se ejecuta

```bash
# 1. Snapshot diario de métricas (ESTO es lo que hay que poner en el cron / Task Scheduler)
python snapshot_daily.py --theme cybersecurity_ai

# 2. Dashboard de las series acumuladas
python -m src.visualization.timeseries_dashboard --theme cybersecurity_ai

# 3. Los adapters de artículos (GDELT, EDGAR) ya entran solos en el pipeline LLM existente:
python main_pipeline.py --theme cybersecurity_ai
```

**Configurar el cron (Windows Task Scheduler), una vez al día:**
```powershell
schtasks /create /tn "ReflexivitySnapshot" /tr "python C:\Users\ferra\Desktop\Algos\reflexivity_trends\snapshot_daily.py" /sc daily /st 07:00
```

### Estado real por fuente (prueba en vivo del 23-07-2026)

- **Wikipedia** ✅ — 248 puntos/día, 8 páginas. Sin fricción. La joya: gratis, histórica, no manipulable.
- **SEC EDGAR** ✅ — 18 puntos (Form 4 30d/7d + 8-K) para 6 tickers. Sin fricción.
- **GDELT** ✅ — funciona con backoff; su API gratuita limita fuerte (~1 req/5s), por eso el snapshot pausa entre keywords. En un cron 1×/día no molesta.
- **Polymarket** ✅ técnicamente, ⚠️ sin cobertura para ciberseguridad — confirmado contra la API: los mercados top por volumen son política/cripto/macro. Se activará solo cuando trabajes un tema tipo cripto o macro. **Es exactamente lo previsto en §2 Capa D.**
- **StockTwits** ⚠️ — su endpoint gratuito quedó **detrás de Cloudflare** (devuelve un desafío JS, no datos). No es un bug del código: es un cierre del lado de ellos, la misma tendencia que Reddit/X en 2023-26. El adapter lo detecta y corta limpio.

### La única decisión que requiere que te des de alta (opcional y gratis)

Para recuperar la **Capa A (multitud retail)**, que es el corazón del sistema Soros, hay dos vías gratuitas:

1. **API oficial de StockTwits** — token gratuito pero requiere registrarse como developer y OAuth. Si te das de alta, el adapter ya está escrito: solo habría que añadir la cabecera de token.
2. **Reddit vía proveedor tercero de bajo coste** (§2 Capa A) — algunos tienen tier gratuito (Xpoz hasta 400k resultados/mes). Requiere alta y una API key.

**Mi recomendación:** de momento el sistema ya acumula 3 capas sólidas (atención, informados, medios) sin que te des de alta en nada. Deja correr el cron unas semanas para tener histórico, y cuando quieras cerrar la Capa A, date de alta en la **API oficial de StockTwits** (gratis, es la fuente retail más validada). Ninguna otra fuente del plan necesita registro.

### Próximo paso científico (Fase 4, cuando haya semanas de datos)

Los índices RDI / NSI / R₀ (§3) todavía **no** se calculan: necesitan una serie de varios días para ser significativos. El siguiente entregable es un módulo `src/analytics/reflexivity_indices.py` que los compute sobre el almacén SQLite, más la validación retrospectiva con casos etiquetados (§4). No tiene sentido construirlo hasta tener histórico acumulado — por eso lo urgente hoy es el cron.
