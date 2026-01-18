"""
Análisis de Noticias de Ciberseguridad con Llama 3 (Groq)
Basado en la Teoría de la Reflexividad de George Soros

Analiza las noticias extraídas para detectar:
- Sentimiento del mercado
- Nivel de subjetividad/especulación
- Fase del ciclo de hype
- Entidades clave mencionadas
"""

import pandas as pd
from groq import Groq
import json
import time
import os
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Ruta del archivo de entrada (el más reciente de SerpAPI)
INPUT_FILE = r"D:\PYTHON\ALGOS\pyTrends\cybersecurity_news_20260118_184923.csv"

# Configuración del Modelo
MODEL_ID = "llama-3.3-70b-versatile"  # Modelo potente y rápido

# Inicializar Cliente
client = Groq(api_key=GROQ_API_KEY)


def analizar_noticia_reflexividad(texto):
    """
    Envía el texto a Llama 3 para análisis bajo la Teoría de la Reflexividad.
    """
    system_prompt = """
    Eres un analista experto en la Teoría de la Reflexividad de George Soros aplicada a tendencias tecnológicas y de ciberseguridad.
    Tu objetivo no es solo resumir, sino detectar la divergencia entre la realidad (hechos) y la percepción (sentimiento/hype).

    Analiza la noticia y extrae la siguiente información en formato JSON estricto:

    1. "sentimiento": Float entre -1.0 (Pánico/Muy Negativo) y 1.0 (Euforia/Muy Positivo).

    2. "subjetividad": Float entre 0.0 (Datos puros/Hechos verificables) y 1.0 (Especulación/Rumores/Opinión marketing).
       *Nota: Una tecnología con mucho hype y alta subjetividad puede ser una burbuja.*

    3. "fase_hype": String. Elige una según el Gartner Hype Cycle:
       - "Lanzamiento" (Innovation Trigger)
       - "Expectativas Infladas" (Peak of Inflated Expectations)
       - "Abismo de Desilusión" (Trough of Disillusionment)
       - "Consolidación" (Slope of Enlightenment)
       - "Madurez" (Plateau of Productivity)

    4. "categoria_cyber": String. Clasifica en una de estas categorías:
       - "AI Threat Detection"
       - "CTEM" (Continuous Threat Exposure Management)
       - "DSPM" (Data Security Posture Management)
       - "ITDR" (Identity Threat Detection and Response)
       - "Human Risk Management"
       - "AI-SPM" (AI Security Posture Management)
       - "Passkeys/Passwordless"
       - "General Cybersecurity"
       - "Vendor News"
       - "Otro"

    5. "entidades": Lista de strings. Empresas, productos o tecnologías clave mencionadas (máximo 5).

    6. "razonamiento": Breve explicación (máximo 20 palabras) de tu análisis.

    7. "relevancia_tendencia": Float entre 0.0 y 1.0. Qué tan relevante es para las tendencias emergentes de ciberseguridad 2025-2026.

    IMPORTANTE: Responde SOLO con el JSON, sin texto adicional.
    """

    user_prompt = f"Analiza el siguiente texto de noticia de ciberseguridad:\n\n{texto}"

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,  # Bajo para respuestas consistentes
            response_format={"type": "json_object"}  # Forzar salida JSON
        )
        return json.loads(completion.choices[0].message.content)
    except json.JSONDecodeError as e:
        print(f"  Error parseando JSON: {e}")
        return None
    except Exception as e:
        print(f"  Error en la API: {e}")
        return None


def main(max_articles=None, sample_mode=False):
    """
    Función principal para analizar las noticias.

    Args:
        max_articles: Límite de artículos a procesar (None = todos)
        sample_mode: Si True, procesa solo una muestra para testing
    """
    print("=" * 70)
    print("ANALISIS DE REFLEXIVIDAD - Ciberseguridad con Llama 3 (Groq)")
    print("=" * 70)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Modelo: {MODEL_ID}")
    print("=" * 70)

    # Verificar API Key
    if not GROQ_API_KEY:
        print("ERROR: No se encontro GROQ_API_KEY en el archivo .env")
        return

    # Verificar archivo
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: No se encuentra el archivo: {INPUT_FILE}")
        return

    # Cargar datos
    print(f"\nCargando archivo: {INPUT_FILE}...")
    try:
        df = pd.read_csv(INPUT_FILE)
        print(f"Archivo cargado. {len(df)} articulos encontrados.")
    except Exception as e:
        print(f"Error leyendo CSV: {e}")
        return

    # Filtrar solo los que tienen contenido extraído exitosamente
    if 'extraction_status' in df.columns:
        df_to_process = df[df['extraction_status'] == 'success'].copy()
        print(f"Articulos con contenido extraido: {len(df_to_process)}")
    else:
        df_to_process = df.copy()

    # Modo sample o límite
    if sample_mode:
        df_to_process = df_to_process.head(10)
        print(f"MODO SAMPLE: Procesando solo 10 articulos")
    elif max_articles:
        df_to_process = df_to_process.head(max_articles)
        print(f"Limitado a {max_articles} articulos")

    # Lista para resultados
    resultados_lista = []

    print("\n" + "-" * 100)
    print(f"{'#':<5} | {'SENT':>5} | {'SUBJ':>5} | {'REL':>5} | {'FASE HYPE':<22} | {'CATEGORIA':<25} | ENTIDADES")
    print("-" * 100)

    start_time = time.time()
    errores = 0

    for index, (idx, row) in enumerate(df_to_process.iterrows()):
        # Construir texto a analizar
        titular = str(row.get('title', ''))

        # Usar abstract si existe, sino full_text, sino snippet
        contenido = ""
        if 'abstract' in row and pd.notna(row['abstract']) and row['abstract']:
            contenido = str(row['abstract'])
        elif 'full_text' in row and pd.notna(row['full_text']) and row['full_text']:
            contenido = str(row['full_text'])[:1500]
        elif 'snippet' in row and pd.notna(row['snippet']):
            contenido = str(row['snippet'])

        # Texto completo (limitar a 2500 chars para tokens)
        texto_completo = f"TITULO: {titular}\n\nCONTENIDO: {contenido}"[:2500]

        # Analizar con Llama
        analisis = analizar_noticia_reflexividad(texto_completo)

        if analisis:
            # Extraer valores con defaults
            sentimiento = analisis.get('sentimiento', 0)
            subjetividad = analisis.get('subjetividad', 0)
            relevancia = analisis.get('relevancia_tendencia', 0)
            fase_hype = analisis.get('fase_hype', 'N/A')[:22]
            categoria = analisis.get('categoria_cyber', 'N/A')[:25]
            entidades = analisis.get('entidades', [])

            # Formatear entidades para display
            if isinstance(entidades, list):
                entidades_str = ", ".join(entidades[:3])[:40]
            else:
                entidades_str = str(entidades)[:40]

            # Imprimir en tiempo real
            print(f"{index+1:<5} | {sentimiento:>5.2f} | {subjetividad:>5.2f} | {relevancia:>5.2f} | {fase_hype:<22} | {categoria:<25} | {entidades_str}")

            # Guardar resultado
            resultados_lista.append({
                'original_index': idx,
                'sentimiento': sentimiento,
                'subjetividad': subjetividad,
                'relevancia_tendencia': relevancia,
                'fase_hype': analisis.get('fase_hype', ''),
                'categoria_cyber': analisis.get('categoria_cyber', ''),
                'entidades': json.dumps(entidades, ensure_ascii=False) if isinstance(entidades, list) else str(entidades),
                'razonamiento': analisis.get('razonamiento', ''),
                'titulo_analizado': titular[:100]
            })
        else:
            print(f"{index+1:<5} | ERROR AL PROCESAR: {titular[:50]}...")
            errores += 1
            resultados_lista.append({
                'original_index': idx,
                'sentimiento': 0,
                'subjetividad': 0,
                'relevancia_tendencia': 0,
                'fase_hype': 'ERROR',
                'categoria_cyber': 'ERROR',
                'entidades': '[]',
                'razonamiento': 'Error en API',
                'titulo_analizado': titular[:100]
            })

        # Rate Limiting para cuenta gratuita de Groq
        time.sleep(0.5)

    # Crear DataFrame de resultados
    df_resultados = pd.DataFrame(resultados_lista)

    # Unir con datos originales
    df_final = df_to_process.reset_index(drop=True)
    df_final = pd.concat([df_final, df_resultados.drop('original_index', axis=1)], axis=1)

    # Generar nombres de archivo
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_csv = f"D:\\PYTHON\\ALGOS\\pyTrends\\cybersecurity_reflexivity_{timestamp}.csv"
    output_json = f"D:\\PYTHON\\ALGOS\\pyTrends\\cybersecurity_reflexivity_{timestamp}.json"

    # Guardar CSV
    df_final.to_csv(output_csv, index=False, encoding='utf-8-sig')

    # Guardar JSON
    df_final.to_json(output_json, orient='records', indent=2, force_ascii=False)

    # Estadísticas finales
    elapsed = time.time() - start_time

    print("\n" + "=" * 70)
    print("RESUMEN DEL ANALISIS")
    print("=" * 70)
    print(f"Articulos procesados: {len(df_to_process)}")
    print(f"Errores: {errores}")
    print(f"Tiempo total: {elapsed:.2f} segundos ({elapsed/60:.1f} minutos)")
    print(f"Velocidad: {len(df_to_process)/elapsed:.2f} articulos/segundo")

    # Estadísticas de sentimiento
    if len(df_resultados) > 0:
        print("\n" + "-" * 50)
        print("ESTADISTICAS DE SENTIMIENTO:")
        print("-" * 50)
        print(f"  Promedio: {df_resultados['sentimiento'].mean():.3f}")
        print(f"  Mediana: {df_resultados['sentimiento'].median():.3f}")
        print(f"  Min/Max: {df_resultados['sentimiento'].min():.3f} / {df_resultados['sentimiento'].max():.3f}")

        print("\n" + "-" * 50)
        print("DISTRIBUCION POR FASE DE HYPE:")
        print("-" * 50)
        fase_counts = df_resultados['fase_hype'].value_counts()
        for fase, count in fase_counts.items():
            print(f"  {fase}: {count} ({100*count/len(df_resultados):.1f}%)")

        print("\n" + "-" * 50)
        print("DISTRIBUCION POR CATEGORIA:")
        print("-" * 50)
        cat_counts = df_resultados['categoria_cyber'].value_counts()
        for cat, count in cat_counts.head(10).items():
            print(f"  {cat}: {count}")

    print("\n" + "=" * 70)
    print("ARCHIVOS GUARDADOS:")
    print(f"  CSV: {output_csv}")
    print(f"  JSON: {output_json}")
    print("=" * 70)

    return df_final


if __name__ == "__main__":
    # Opciones de ejecución:
    # 1. Modo sample (10 artículos para testing rápido):
    #    df = main(sample_mode=True)

    # 2. Procesar N artículos:
    #    df = main(max_articles=100)

    # 3. Procesar todos (puede tardar mucho con cuenta gratuita):
    #    df = main()

    # Por defecto: modo sample para testing
    df = main(sample_mode=True)
