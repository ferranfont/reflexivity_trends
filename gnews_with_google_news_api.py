"""
Google News Scraper usando GNews Library
Para tendencias de Ciberseguridad 2025-2026

Usa la librería GNews (gratuita, sin API key) para obtener noticias.
Incluye extracción de contenido completo de los artículos.

Términos:
- AI Threat Detection
- CTEM (Continuous Threat Exposure Management)
- DSPM (Data Security Posture Management)
- ITDR (Identity Threat Detection and Response)
- Human Risk Management (HRM)
- AI-SPM
- Passkeys / FIDO2
"""

from gnews import GNews
import pandas as pd
from datetime import datetime
import time
import requests
from bs4 import BeautifulSoup
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

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

# Headers para web scraping
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
}


def extract_article_content(url, timeout=10):
    """
    Extrae el contenido principal de un artículo web.
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

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            result['meta_description'] = meta_desc['content'].strip()

        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc and og_desc.get('content') and not result['meta_description']:
            result['meta_description'] = og_desc['content'].strip()

        # Eliminar elementos no deseados
        for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer',
                                       'aside', 'form', 'iframe', 'noscript']):
            element.decompose()

        # Buscar contenido del artículo
        article_selectors = [
            'article', '[role="main"]', '.article-content', '.article-body',
            '.post-content', '.entry-content', '.content-body', '.story-body',
            '#article-body', '.article__body', '.ArticleBody', 'main', '.main-content',
        ]

        article_text = ""

        for selector in article_selectors:
            article = soup.select_one(selector)
            if article:
                paragraphs = article.find_all(['p', 'h1', 'h2', 'h3'])
                if paragraphs:
                    article_text = '\n\n'.join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
                    if len(article_text) > 200:
                        break

        if not article_text or len(article_text) < 200:
            all_paragraphs = soup.find_all('p')
            good_paragraphs = [p.get_text().strip() for p in all_paragraphs if len(p.get_text().strip()) > 50]
            article_text = '\n\n'.join(good_paragraphs)

        # Limpiar texto
        article_text = re.sub(r'\s+', ' ', article_text)
        article_text = re.sub(r'\n\s*\n', '\n\n', article_text)

        result['full_text'] = article_text[:10000]

        # Crear abstract
        if result['meta_description']:
            result['abstract'] = result['meta_description']
        elif article_text:
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


def extract_content_batch(news_df, max_workers=10):
    """
    Extrae contenido de múltiples artículos en paralelo.
    """
    total = len(news_df)
    completed = 0

    print(f"\nExtrayendo contenido de {total} artículos...")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {
            executor.submit(extract_article_content, row['link']): idx
            for idx, row in news_df.iterrows()
        }

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

    # Convertir resultados a columnas
    abstracts, full_texts, meta_descriptions, statuses = [], [], [], []
    for idx in news_df.index:
        result = results[idx]
        abstracts.append(result['abstract'])
        full_texts.append(result['full_text'])
        meta_descriptions.append(result['meta_description'])
        statuses.append(result['extraction_status'])

    news_df['abstract'] = abstracts
    news_df['full_text'] = full_texts
    news_df['meta_description'] = meta_descriptions
    news_df['extraction_status'] = statuses

    return news_df


def search_gnews(query, google_news, max_results=100):
    """
    Busca noticias usando GNews library.

    Args:
        query: Término de búsqueda
        google_news: Instancia de GNews configurada
        max_results: Número máximo de resultados

    Returns:
        Lista de diccionarios con las noticias
    """
    all_news = []

    try:
        # Buscar noticias
        news_results = google_news.get_news(query)

        if news_results:
            for news in news_results[:max_results]:
                news_item = {
                    "search_term": query,
                    "title": news.get("title", ""),
                    "link": news.get("url", ""),
                    "source": news.get("publisher", {}).get("title", "") if isinstance(news.get("publisher"), dict) else str(news.get("publisher", "")),
                    "date": news.get("published date", ""),
                    "snippet": news.get("description", ""),
                    "thumbnail": "",
                    "fetched_at": datetime.now().isoformat()
                }
                all_news.append(news_item)

    except Exception as e:
        print(f"  Error buscando '{query}': {e}")

    return all_news


def search_gnews_by_topic(google_news, topic_name):
    """
    Busca noticias por tópico predefinido de Google News.
    """
    all_news = []
    topics = {
        'technology': 'TECHNOLOGY',
        'business': 'BUSINESS',
        'science': 'SCIENCE',
    }

    topic_code = topics.get(topic_name.lower())
    if not topic_code:
        return all_news

    try:
        news_results = google_news.get_news_by_topic(topic_code)
        if news_results:
            for news in news_results:
                news_item = {
                    "search_term": f"[TOPIC:{topic_name}]",
                    "title": news.get("title", ""),
                    "link": news.get("url", ""),
                    "source": news.get("publisher", {}).get("title", "") if isinstance(news.get("publisher"), dict) else str(news.get("publisher", "")),
                    "date": news.get("published date", ""),
                    "snippet": news.get("description", ""),
                    "thumbnail": "",
                    "fetched_at": datetime.now().isoformat()
                }
                all_news.append(news_item)
    except Exception as e:
        print(f"  Error en topic '{topic_name}': {e}")

    return all_news


def main(extract_content=True, max_workers=10):
    """
    Función principal que ejecuta todas las búsquedas usando GNews.
    """

    print("=" * 70)
    print("GNEWS SCRAPER - Tendencias Ciberseguridad 2025-2026")
    print("=" * 70)
    print(f"Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total de términos a buscar: {len(SEARCH_TERMS)}")
    print(f"Extracción de contenido: {'Activada' if extract_content else 'Desactivada'}")
    print("Librería: GNews (gratuita, sin API key)")
    print("=" * 70)

    # Configurar GNews
    google_news = GNews(
        language='en',
        country='US',
        period='1m',  # Último mes
        max_results=100,
        exclude_websites=['youtube.com', 'facebook.com', 'twitter.com']
    )

    all_news = []

    # Buscar por cada término
    for i, term in enumerate(SEARCH_TERMS, 1):
        print(f"\n[{i}/{len(SEARCH_TERMS)}] Buscando: '{term}'...")

        news = search_gnews(term, google_news)
        print(f"  -> GNews: {len(news)} resultados")
        all_news.extend(news)

        # Pausa para evitar rate limiting
        time.sleep(2)

    # También buscar en topics de tecnología
    print(f"\n[Extra] Buscando en topics de Technology...")
    topic_news = search_gnews_by_topic(google_news, 'technology')
    print(f"  -> Topic Technology: {len(topic_news)} resultados")
    all_news.extend(topic_news)

    # Crear DataFrame
    df = pd.DataFrame(all_news)

    if len(df) == 0:
        print("\nNo se encontraron noticias. GNews puede tener rate limiting.")
        return None

    # Eliminar duplicados basados en el link
    df_unique = df.drop_duplicates(subset=['link'], keep='first').reset_index(drop=True)

    print("\n" + "=" * 70)
    print("RESUMEN DE BÚSQUEDA")
    print("=" * 70)
    print(f"Total de noticias obtenidas: {len(all_news)}")
    print(f"Noticias únicas (sin duplicados): {len(df_unique)}")

    # Extraer contenido si está habilitado
    if extract_content and len(df_unique) > 0:
        print("\n" + "=" * 70)
        print("EXTRACCIÓN DE CONTENIDO")
        print("=" * 70)
        df_unique = extract_content_batch(df_unique, max_workers=max_workers)

        success_count = (df_unique['extraction_status'] == 'success').sum()
        print(f"\nExtracción exitosa: {success_count}/{len(df_unique)} ({100*success_count/len(df_unique):.1f}%)")

    # Guardar CSV completo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"gnews_cybersecurity_{timestamp}.csv"
    df_unique.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\nArchivo guardado: {output_file}")

    # Estadísticas por término de búsqueda
    print("\n" + "-" * 50)
    print("NOTICIAS POR TÉRMINO DE BÚSQUEDA:")
    print("-" * 50)
    stats = df_unique['search_term'].value_counts()
    for term, count in stats.head(30).items():
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
    stats_file = f"gnews_cybersecurity_stats_{timestamp}.csv"
    stats_df.to_csv(stats_file, index=False)
    print(f"\nEstadísticas guardadas: {stats_file}")

    return df_unique


if __name__ == "__main__":
    df = main(extract_content=True, max_workers=10)
