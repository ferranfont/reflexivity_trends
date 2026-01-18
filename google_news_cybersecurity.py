"""
Google News Scraper para tendencias de Ciberseguridad 2025-2026
Usa SerpAPI para obtener noticias de Google News sobre temas trending:
- AI Threat Detection
- CTEM (Continuous Threat Exposure Management)
- DSPM (Data Security Posture Management)
- ITDR (Identity Threat Detection and Response)
- Human Risk Management (HRM)
- AI-SPM
- Passkeys / FIDO2

NUEVO: Extrae el contenido/abstract de cada artículo mediante web scraping
"""

from serpapi import GoogleSearch
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

# Cargar variables de entorno
load_dotenv()

# Configuración de términos de búsqueda
SEARCH_TERMS = [
    # AI Threat Detection (+733% growth)
    "AI Threat Detection",
    "AI threat detection cybersecurity",
    "artificial intelligence threat detection",

    # CTEM - Continuous Threat Exposure Management (Gartner trending)
    "CTEM",
    "Continuous Threat Exposure Management",
    "CTEM cybersecurity",
    "CTEM Gartner",

    # DSPM - Data Security Posture Management
    "DSPM",
    "Data Security Posture Management",
    "DSPM cloud security",

    # ITDR - Identity Threat Detection and Response
    "ITDR",
    "Identity Threat Detection and Response",
    "ITDR cybersecurity",

    # Human Risk Management (HRM)
    "Human Risk Management cybersecurity",
    "HRM security awareness",
    "human risk management security",

    # AI-SPM - AI Security Posture Management
    "AI-SPM",
    "AI Security Posture Management",
    "AI model security",
    "prompt injection security",

    # Passkeys / Passwordless
    "Passkeys authentication",
    "FIDO2 passwordless",
    "passwordless authentication 2025",

    # Empresas/Vendors líderes en estos campos
    "CrowdStrike AI threat",
    "Palo Alto XSIAM",
    "Microsoft Defender AI",
    "Wiz DSPM",
    "Varonis DSPM",
    "SentinelOne AI",
    "Cybereason AI",
]

# Headers para simular un navegador real
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}


def extract_article_content(url, timeout=10):
    """
    Extrae el contenido principal de un artículo web.

    Args:
        url: URL del artículo
        timeout: Tiempo máximo de espera en segundos

    Returns:
        dict con 'abstract' (primeros párrafos) y 'full_text' (texto completo)
    """
    result = {
        'abstract': '',
        'full_text': '',
        'meta_description': '',
        'extraction_status': 'pending'
    }

    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # 1. Intentar obtener meta description (suele ser un buen resumen)
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result['meta_description'] = meta_desc['content'].strip()

        # También buscar og:description
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content') and not result['meta_description']:
            result['meta_description'] = og_desc['content'].strip()

        # 2. Eliminar elementos no deseados
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                       'aside', 'form', 'iframe', 'noscript',
                                       'advertisement', 'ads', 'sidebar']):
            element.decompose()

        # 3. Buscar el contenido principal del artículo
        # Intentar diferentes selectores comunes para artículos
        article_selectors = [
            'article',
            '[role="main"]',
            '.article-content',
            '.article-body',
            '.post-content',
            '.entry-content',
            '.content-body',
            '.story-body',
            '#article-body',
            '.article__body',
            '.ArticleBody',
            'main',
            '.main-content',
        ]

        article_text = ""

        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                # Obtener todos los párrafos
                paragraphs = article.find_all(['p', 'h1', 'h2', 'h3'])
                if paragraphs:
                    article_text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(article_text) > 200:  # Si encontramos contenido sustancial
                        break

        # Si no encontramos con selectores, buscar todos los párrafos
        if not article_text or len(article_text) < 200:
            all_paragraphs = soup.find_all('p')
            # Filtrar párrafos muy cortos o que parecen navegación
            good_paragraphs = [p.get_text().strip() for p in all_paragraphs
                              if len(p.get_text().strip()) > 50]
            article_text = '\n\n'.join(good_paragraphs)

        # 4. Limpiar el texto
        article_text = re.sub(r'\s+', ' ', article_text)  # Normalizar espacios
        article_text = re.sub(r'\n\s*\n', '\n\n', article_text)  # Normalizar saltos de línea

        result['full_text'] = article_text[:10000]  # Limitar a 10000 caracteres

        # 5. Crear abstract (primeros 500-1000 caracteres o 2-3 párrafos)
        if result['meta_description']:
            result['abstract'] = result['meta_description']
        elif article_text:
            # Tomar los primeros párrafos hasta ~500 caracteres
            paragraphs = article_text.split('\n\n')
            abstract = ""
            for p in paragraphs[:3]:
                if len(abstract) + len(p) < 800:
                    abstract += p + " "
                else:
                    break
            result['abstract'] = abstract.strip()[:800]

        result['extraction_status'] = 'success'

    except requests.exceptions.Timeout:
        result['extraction_status'] = 'timeout'
    except requests.exceptions.RequestException as e:
        result['extraction_status'] = f'error: {str(e)[:50]}'
    except Exception as e:
        result['extraction_status'] = f'error: {str(e)[:50]}'

    return result


def extract_content_batch(news_df, max_workers=5, progress_callback=None):
    """
    Extrae contenido de múltiples artículos en paralelo.

    Args:
        news_df: DataFrame con las noticias (debe tener columna 'link')
        max_workers: Número de threads paralelos
        progress_callback: Función para reportar progreso

    Returns:
        DataFrame con columnas adicionales de contenido
    """
    abstracts = []
    full_texts = []
    meta_descriptions = []
    extraction_statuses = []

    total = len(news_df)
    completed = 0

    print(f"\nExtrayendo contenido de {total} artículos...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Crear futures
        future_to_url = {
            executor.submit(extract_article_content, row['link']): idx
            for idx, row in news_df.iterrows()
        }

        # Inicializar listas con valores vacíos
        results = {idx: None for idx in news_df.index}

        for future in as_completed(future_to_url):
            idx = future_to_url[future]
            completed += 1

            try:
                result = future.result()
                results[idx] = result
            except Exception as e:
                results[idx] = {
                    'abstract': '',
                    'full_text': '',
                    'meta_description': '',
                    'extraction_status': f'error: {str(e)[:50]}'
                }

            if completed % 50 == 0 or completed == total:
                print(f"  Progreso: {completed}/{total} ({100*completed/total:.1f}%)")

    # Convertir resultados a listas ordenadas
    for idx in news_df.index:
        result = results[idx]
        abstracts.append(result['abstract'])
        full_texts.append(result['full_text'])
        meta_descriptions.append(result['meta_description'])
        extraction_statuses.append(result['extraction_status'])

    news_df['abstract'] = abstracts
    news_df['full_text'] = full_texts
    news_df['meta_description'] = meta_descriptions
    news_df['extraction_status'] = extraction_statuses

    return news_df


def search_google_news(query, api_key, num_results=100):
    """
    Busca noticias en Google News usando SerpAPI
    """
    all_news = []

    params = {
        "engine": "google_news",
        "q": query,
        "gl": "us",
        "hl": "en",
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        news_results = results.get("news_results", [])

        for news in news_results:
            news_item = {
                "search_term": query,
                "title": news.get("title", ""),
                "link": news.get("link", ""),
                "source": news.get("source", {}).get("name", "") if isinstance(news.get("source"), dict) else news.get("source", ""),
                "date": news.get("date", ""),
                "snippet": news.get("snippet", ""),
                "thumbnail": news.get("thumbnail", ""),
                "fetched_at": datetime.now().isoformat()
            }

            if "stories" in news:
                for story in news["stories"]:
                    story_item = {
                        "search_term": query,
                        "title": story.get("title", ""),
                        "link": story.get("link", ""),
                        "source": story.get("source", {}).get("name", "") if isinstance(story.get("source"), dict) else story.get("source", ""),
                        "date": story.get("date", ""),
                        "snippet": story.get("snippet", ""),
                        "thumbnail": story.get("thumbnail", ""),
                        "fetched_at": datetime.now().isoformat()
                    }
                    all_news.append(story_item)
            else:
                all_news.append(news_item)

        for key in ["top_stories", "highlight"]:
            if key in results:
                for item in results[key]:
                    news_item = {
                        "search_term": query,
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "source": item.get("source", {}).get("name", "") if isinstance(item.get("source"), dict) else item.get("source", ""),
                        "date": item.get("date", ""),
                        "snippet": item.get("snippet", ""),
                        "thumbnail": item.get("thumbnail", ""),
                        "fetched_at": datetime.now().isoformat()
                    }
                    all_news.append(news_item)

    except Exception as e:
        print(f"  Error buscando '{query}': {e}")

    return all_news


def search_google_regular(query, api_key, tbs="qdr:m"):
    """
    Búsqueda regular de Google filtrada por noticias/tiempo
    """
    all_results = []

    params = {
        "engine": "google",
        "q": query,
        "tbm": "nws",
        "tbs": tbs,
        "gl": "us",
        "hl": "en",
        "num": 50,
        "api_key": api_key
    }

    try:
        search = GoogleSearch(params)
        results = search.get_dict()

        news_results = results.get("news_results", [])

        for news in news_results:
            news_item = {
                "search_term": query,
                "title": news.get("title", ""),
                "link": news.get("link", ""),
                "source": news.get("source", ""),
                "date": news.get("date", ""),
                "snippet": news.get("snippet", ""),
                "thumbnail": news.get("thumbnail", ""),
                "fetched_at": datetime.now().isoformat()
            }
            all_results.append(news_item)

    except Exception as e:
        print(f"  Error en búsqueda regular '{query}': {e}")

    return all_results


def main(extract_content=True, max_workers=10):
    """
    Función principal que ejecuta todas las búsquedas

    Args:
        extract_content: Si True, extrae el contenido de cada artículo
        max_workers: Número de threads para extracción paralela
    """

    api_key = os.getenv("SERPAPI_API_KEY")

    if not api_key:
        print("ERROR: No se encontró SERPAPI_API_KEY en el archivo .env")
        return

    print("=" * 70)
    print("GOOGLE NEWS SCRAPER - Tendencias Ciberseguridad 2025-2026")
    print("=" * 70)
    print(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de términos a buscar: {len(SEARCH_TERMS)}")
    print(f"Extracción de contenido: {'Activada' if extract_content else 'Desactivada'}")
    print("=" * 70)

    all_news = []

    for i, term in enumerate(SEARCH_TERMS, 1):
        print(f"\n[{i}/{len(SEARCH_TERMS)}] Buscando: '{term}'...")

        news = search_google_news(term, api_key)
        print(f"  -> Google News: {len(news)} resultados")
        all_news.extend(news)

        regular_news = search_google_regular(term, api_key, tbs="qdr:m")
        print(f"  -> Google Search (noticias): {len(regular_news)} resultados")
        all_news.extend(regular_news)

        time.sleep(1)

    # Crear DataFrame
    df = pd.DataFrame(all_news)

    # Eliminar duplicados basados en el link
    df_unique = df.drop_duplicates(subset=['link'], keep='first').reset_index(drop=True)

    print("\n" + "=" * 70)
    print("RESUMEN DE BÚSQUEDA")
    print("=" * 70)
    print(f"Total de noticias obtenidas: {len(all_news)}")
    print(f"Noticias únicas (sin duplicados): {len(df_unique)}")

    # Extraer contenido si está habilitado
    if extract_content:
        print("\n" + "=" * 70)
        print("EXTRACCIÓN DE CONTENIDO")
        print("=" * 70)
        df_unique = extract_content_batch(df_unique, max_workers=max_workers)

        # Estadísticas de extracción
        success_count = (df_unique['extraction_status'] == 'success').sum()
        print(f"\nExtracción exitosa: {success_count}/{len(df_unique)} ({100*success_count/len(df_unique):.1f}%)")

    # Guardar CSV completo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"cybersecurity_news_{timestamp}.csv"
    df_unique.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nArchivo guardado: {output_file}")

    # Estadísticas por término de búsqueda
    print("\n" + "-" * 50)
    print("NOTICIAS POR TÉRMINO DE BÚSQUEDA:")
    print("-" * 50)
    stats = df_unique['search_term'].value_counts()
    for term, count in stats.items():
        print(f"  {term}: {count}")

    # Estadísticas por fuente
    print("\n" + "-" * 50)
    print("TOP 20 FUENTES:")
    print("-" * 50)
    source_stats = df_unique['source'].value_counts().head(20)
    for source, count in source_stats.items():
        if source:
            print(f"  {source}: {count}")

    # Guardar estadísticas
    stats_df = pd.DataFrame({
        'search_term': stats.index,
        'count': stats.values
    })
    stats_file = f"cybersecurity_news_stats_{timestamp}.csv"
    stats_df.to_csv(stats_file, index=False)
    print(f"\nEstadísticas guardadas: {stats_file}")

    return df_unique


if __name__ == "__main__":
    # Ejecutar con extracción de contenido habilitada
    # Para desactivar: main(extract_content=False)
    # Para ajustar paralelismo: main(max_workers=5)
    df = main(extract_content=True, max_workers=10)
