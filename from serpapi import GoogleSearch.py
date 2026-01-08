from serpapi import GoogleSearch
import json
import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

# 1. Configuración de la búsqueda
params = {
  "engine": "google_trends",       # Motor específico de Trends
  "q": "Inteligencia Artificial, Crypto",  # Lo que quieres comparar (separado por coma)
  "data_type": "TIMESERIES",       # Tipo de datos: Serie temporal (gráfico)
  "geo": "ES",                     # Geografía: España (o 'US', 'MX', etc.)
  "date": "today 5-y",             # Tiempo: Últimos 5 años
  "api_key": os.getenv("SERPAPI_API_KEY")  # API Key desde .env
}

print("Consultando a Google Trends vía SerpApi...")

# 2. Hacer la petición
search = GoogleSearch(params)
results = search.get_dict()

# 3. Procesar los resultados
# Google Trends devuelve una estructura anidada. Vamos a buscar "interest_over_time"
if "interest_over_time" in results:
    timeline = results["interest_over_time"]["timeline_data"]

    print(f"\nResultados encontrados: {len(timeline)} puntos de datos.\n")
    print(f"{'FECHA':<15} | {'IA':<10} | {'CRYPTO':<10}")
    print("-" * 40)

    # Preparar datos para el gráfico
    fechas = []
    valores_ia = []
    valores_crypto = []

    # Mostramos los primeros 5 resultados como ejemplo y recopilamos todos los datos
    for i, point in enumerate(timeline):
        fecha = point["date"]
        # Extraemos los valores. Nota: values es una lista de diccionarios
        valor_ia = point["values"][0]["extracted_value"]
        valor_crypto = point["values"][1]["extracted_value"]

        fechas.append(fecha)
        valores_ia.append(valor_ia)
        valores_crypto.append(valor_crypto)

        if i < 5:
            print(f"{fecha:<15} | {valor_ia:<10} | {valor_crypto:<10}")

    # Crear DataFrame para mejor manipulación
    df = pd.DataFrame({
        'Fecha': fechas,
        'Inteligencia Artificial': valores_ia,
        'Crypto': valores_crypto
    })

    # Guardar datos en CSV
    df.to_csv("tendencias_5_años.csv", index=False)
    print(f"\nDatos desde: {fechas[0]} hasta: {fechas[-1]}")
    print(f"Total de registros: {len(fechas)}")
    print("Archivo CSV guardado como 'tendencias_5_años.csv'")

    # Crear visualización
    plt.figure(figsize=(14, 7))
    plt.plot(range(len(fechas)), valores_ia, label='Inteligencia Artificial', linewidth=2, marker='o', markersize=3)
    plt.plot(range(len(fechas)), valores_crypto, label='Crypto', linewidth=2, marker='s', markersize=3)

    plt.title('Tendencias de búsqueda en Google - Últimos 5 años (SERPAPI)', fontsize=16, fontweight='bold')
    plt.xlabel('Fecha', fontsize=12)
    plt.ylabel('Interés de búsqueda (0-100)', fontsize=12)
    plt.legend(fontsize=11)
    plt.grid(True, alpha=0.3)

    # Mostrar solo algunas etiquetas en el eje X para no saturar
    step = max(len(fechas) // 10, 1)
    plt.xticks(range(0, len(fechas), step), [fechas[i] for i in range(0, len(fechas), step)], rotation=45)
    plt.tight_layout()

    # Guardar y mostrar
    plt.savefig('tendencias_5_años_serpapi.png', dpi=300, bbox_inches='tight')
    print("\nGráfico guardado como 'tendencias_5_años_serpapi.png'")
    plt.show()

else:
    print("Error: No se encontraron datos de series temporales.")
    # Imprime el error si algo falla para depurar
    print(results)