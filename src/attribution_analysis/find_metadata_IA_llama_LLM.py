"""
Análisis de Noticias Temático con Llama 3 (Groq)
Basado en la Teoría de la Reflexividad de George Soros

Analiza las noticias extraídas para detectar:
- Sentimiento del mercado
- Nivel de subjetividad/especulación
- Fase del ciclo de hype
- Entidades clave mencionadas
"""

import os
import sys
import json
import time
import glob
import pandas as pd
from datetime import datetime
from groq import Groq
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import config

# Cargar variables de entorno
load_dotenv()

# --- CONFIGURACIÓN ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Configuración del Modelo
MODEL_ID = "llama-3.3-70b-versatile" 

# Inicializar Cliente
client = Groq(api_key=GROQ_API_KEY)


def analizar_noticia_reflexividad(texto, context_prompt, categories):
    """
    Envía el texto a Llama 3 para análisis bajo la Teoría de la Reflexividad,
    adaptado al contexto del tema.
    """
    categories_str = "\n".join([f"       - \"{c}\"" for c in categories])
    
    system_prompt = f"""
    {context_prompt}
    Tu objetivo no es solo resumir, sino detectar la divergencia entre la realidad (hechos) y la percepción (sentimiento/hype) bajo la Teoría de la Reflexividad de Soros.

    Analiza la noticia y extrae la siguiente información en formato JSON estricto:

    1. "sentimiento": Float entre -1.0 (Pánico/Muy Negativo) y 1.0 (Euforia/Muy Positivo).

    2. "subjetividad": Float entre 0.0 (Datos puros/Hechos verificables) y 1.0 (Especulación/Rumores/Opinión marketing).
       *Nota: Una tecnología o activo con mucho hype y alta subjetividad puede ser una burbuja.*

    3. "fase_hype": String. Elige una según el Gartner Hype Cycle:
       - "Lanzamiento" (Innovation Trigger)
       - "Expectativas Infladas" (Peak of Inflated Expectations)
       - "Abismo de Desilusión" (Trough of Disillusionment)
       - "Consolidación" (Slope of Enlightenment)
       - "Madurez" (Plateau of Productivity)

    4. "categoria_cyber": String. (Aunque diga 'categoria_cyber', usa la categoría que mejor encaje de esta lista):
{categories_str}
       - "Otro"

    5. "entidades": Lista de strings. Empresas, activos, productos o personas clave mencionadas (máximo 5).

    6. "razonamiento": Breve explicación (máximo 20 palabras) de tu análisis.

    7. "relevancia_tendencia": Float entre 0.0 y 1.0. Qué tan relevante es para las tendencias emergentes en este sector para 2025-2026.

    IMPORTANTE: Responde SOLO con el JSON, sin texto adicional.
    """

    user_prompt = f"Analiza el siguiente texto de noticia:\n\n{texto}"

    try:
        completion = client.chat.completions.create(
            model=MODEL_ID,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        print(f"  Error en API/JSON: {e}")
        return None


def main(theme_id, max_articles=None, sample_mode=False):
    print("=" * 70)
    print(f"ANALISIS DE REFLEXIVIDAD: {theme_id}")
    print("=" * 70)
    
    # 1. Validar Configuración
    if theme_id not in config.INVESTING_THEMES:
        print(f"Error: Tema '{theme_id}' no encontrado en config.")
        return

    theme_config = config.INVESTING_THEMES[theme_id]
    theme_dirs = config.get_theme_dirs(theme_id)
    data_dir = theme_dirs["DATA"]
    
    print(f"Directorio de datos: {data_dir}")
    
    # 2. Encontrar input file (JSON)
    pattern = os.path.join(data_dir, "unified_data_*.json")
    files = glob.glob(pattern)
    
    # Filtrar solo archivos RAW (evitar procesar archivos ya analizados si comparten patron, aunque estos se llamaran analyzed_)
    # Mejor buscamos los que NO empiezan por analyzed_ (que ahora se guardaran aqui)
    raw_files = [f for f in files if "analyzed_" not in os.path.basename(f)]
    
    if not raw_files:
        print(f"ERROR: No hay archivos de datos raw en {data_dir}")
        return
        
    input_file = max(raw_files, key=os.path.getmtime)
    print(f"Cargando archivo más reciente: {input_file}")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            articles_data = json.load(f)
        
        # Convertir a DataFrame para facilitar manejo
        df = pd.DataFrame(articles_data)
        print(f"Artículos cargados: {len(df)}")
    except Exception as e:
        print(f"Error leyendo JSON: {e}")
        return

    # 3. Filtrar / Muestrear
    if sample_mode:
        df = df.head(5)
        print("MODO SAMPLE: Procesando solo 5 artículos")
    elif max_articles:
        df = df.head(max_articles)
        print(f"Limitado a {max_articles} artículos")

    # 4. Procesar
    resultados_lista = []
    
    context_prompt = theme_config.get("system_prompt_context", "Eres un analista financiero experto.")
    categories = theme_config.get("categories", ["General", "Other"])

    print("\n" + "-" * 100)
    print(f"{'#':<5} | {'SENT':>5} | {'SUBJ':>5} | {'CATEGORIA':<25} | TITULO")
    print("-" * 100)

    start_time = time.time()
    errores = 0

    for index, row in df.iterrows():
        # Construir texto
        titular = row.get('title', '')
        contenido = row.get('full_text') or row.get('abstract') or row.get('snippet') or ""
        
        texto_completo = f"TITULO: {titular}\n\nCONTENIDO: {contenido}"[:3000]

        # LLM Call
        analisis = analizar_noticia_reflexividad(texto_completo, context_prompt, categories)

        item = row.to_dict() # Copiar datos originales

        if analisis:
            # Inject Analysis
            item['sentimiento'] = analisis.get('sentimiento', 0)
            item['subjetividad'] = analisis.get('subjetividad', 0)
            item['fase_hype'] = analisis.get('fase_hype', 'Unknown')
            # Fallback for category key name compatibility
            item['categoria_theme'] = analisis.get('categoria_cyber', 'Other') 
            # Mantener compatibilidad con dashboard antiguo que busca 'categoria_cyber'
            item['categoria_cyber'] = item['categoria_theme']
            
            item['entidades'] = analisis.get('entidades', [])
            item['razonamiento'] = analisis.get('razonamiento', '')
            item['relevancia'] = analisis.get('relevancia_tendencia', 0)
            
            # Print status
            print(f"{index+1:<5} | {item['sentimiento']:>5.2f} | {item['subjetividad']:>5.2f} | {item['categoria_theme'][:25]:<25} | {titular[:40]}...")
            
        else:
            print(f"{index+1:<5} | ERROR  |       |                           | {titular[:40]}...")
            errores += 1
            # Default values for failed analysis
            item['sentimiento'] = 0
            item['subjetividad'] = 0
            item['fase_hype'] = 'Error'
            item['categoria_theme'] = 'Error'
            item['categoria_cyber'] = 'Error'
        
        # Add metadata flag
        item['is_analyzed'] = True
        item['analysis_date'] = datetime.now().isoformat()
        
        resultados_lista.append(item)
        
        # Rate limit
        time.sleep(0.5)

    # 5. Guardar Resultados Enriquecidos
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"analyzed_reflexivity_{timestamp}.json"
    output_path = os.path.join(data_dir, output_filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(resultados_lista, f, indent=2, ensure_ascii=False)
        
    print("\n" + "=" * 70)
    print(f"PROCESO COMPLETADO")
    print(f"Archivo guardado: {output_path}")
    print(f"Total procesados: {len(resultados_lista)}")
    print("=" * 70)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Analyze news with LLM for a specific theme")
    parser.add_argument("--theme", type=str, required=True, help="Theme ID from config.py")
    parser.add_argument("--sample", action="store_true", help="Run only on a few articles for testing")
    parser.add_argument("--max", type=int, default=None, help="Max articles to process")
    
    args = parser.parse_args()
    
    main(theme_id=args.theme, sample_mode=args.sample, max_articles=args.max)
