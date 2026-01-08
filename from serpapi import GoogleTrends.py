from serpapi import GoogleSearch
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from dotenv import load_dotenv
import os

# Cargar variables de entorno
load_dotenv()

params = {
  "engine": "google_trends",
  "q": "Inteligencia Artificial, Crypto",
  "date": "today 5-y",
  "tz": "420",
  "data_type": "TIMESERIES",
  "api_key": os.getenv("SERPAPI_API_KEY")
}

print("Consultando Google Trends...")
search = GoogleSearch(params)
results = search.get_dict()

if "interest_over_time" in results:
    timeline = results["interest_over_time"]["timeline_data"]

    # Extraer datos
    fechas = []
    valores_ia = []
    valores_crypto = []

    for point in timeline:
        fechas.append(point["date"])
        valores_ia.append(point["values"][0]["extracted_value"])
        valores_crypto.append(point["values"][1]["extracted_value"])

    # Crear gráfico interactivo con Plotly
    fig = go.Figure()

    # Añadir línea de Inteligencia Artificial
    fig.add_trace(go.Scatter(
        x=fechas,
        y=valores_ia,
        mode='lines+markers',
        name='Inteligencia Artificial',
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6),
        hovertemplate='<b>IA</b><br>Fecha: %{x}<br>Interés: %{y}<extra></extra>'
    ))

    # Añadir línea de Crypto
    fig.add_trace(go.Scatter(
        x=fechas,
        y=valores_crypto,
        mode='lines+markers',
        name='Crypto',
        line=dict(color='#ff7f0e', width=3),
        marker=dict(size=6),
        hovertemplate='<b>Crypto</b><br>Fecha: %{x}<br>Interés: %{y}<extra></extra>'
    ))

    # Diseño del gráfico
    fig.update_layout(
        title={
            'text': 'Tendencias de Búsqueda en Google - Últimos 5 años',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 24, 'color': '#2c3e50'}
        },
        xaxis_title='Fecha',
        yaxis_title='Interés de búsqueda (0-100)',
        hovermode='x unified',
        template='plotly_white',
        font=dict(size=14),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=600,
        margin=dict(l=50, r=50, t=100, b=50)
    )

    # Guardar como HTML interactivo
    fig.write_html("tendencias_interactivo.html")
    print(f"\n✓ Gráfico interactivo guardado como 'tendencias_interactivo.html'")
    print(f"✓ Total de registros: {len(fechas)}")
    print(f"✓ Período: {fechas[0]} hasta {fechas[-1]}")
    print("\nAbre el archivo HTML en tu navegador para ver el gráfico interactivo!")

    # Mostrar en navegador automáticamente
    fig.show()

else:
    print("Error: No se encontraron datos")
    print(results)
