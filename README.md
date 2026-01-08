# Google Trends Analysis - pyTrends

Análisis de tendencias de búsqueda en Google usando Python con múltiples métodos (pytrends y SERPAPI).

## Descripción

Este proyecto permite analizar tendencias de búsqueda en Google para los términos "Inteligencia Artificial" y "Crypto" durante los últimos 5 años en España.

## Características

- 📊 Visualización con matplotlib (gráficos estáticos)
- 🌐 Visualización interactiva con Plotly (gráficos web)
- 💾 Exportación de datos a CSV
- 🔑 Soporte para SERPAPI con variables de entorno
- 🆓 Opción gratuita con pytrends

## Archivos

### Scripts principales:

1. **import pandas as pd.py** - Versión con pytrends (gratuita)
2. **from serpapi import GoogleSearch.py** - Versión con SERPAPI (requiere API key)
3. **from serpapi import GoogleTrends.py** - Versión con gráficos interactivos Plotly

## Instalación

```bash
# Instalar dependencias
pip install pandas pytrends matplotlib plotly python-dotenv serpapi
```

## Configuración

1. Crea un archivo `.env` en la raíz del proyecto:
```
SERPAPI_API_KEY=tu_api_key_aqui
```

2. Obtén tu API key gratis en: https://serpapi.com/

## Uso

### Opción 1: PyTrends (Gratis)
```bash
python "import pandas as pd.py"
```

### Opción 2: SERPAPI con matplotlib
```bash
python "from serpapi import GoogleSearch.py"
```

### Opción 3: SERPAPI con gráficos interactivos
```bash
python "from serpapi import GoogleTrends.py"
```

## Salida

Los scripts generan:
- 📈 Gráficos PNG (alta resolución 300 dpi)
- 📄 Archivo CSV con los datos
- 🌐 HTML interactivo (versión Plotly)

## Tecnologías

- Python 3.x
- pandas
- matplotlib
- plotly
- pytrends
- serpapi
- python-dotenv

## Licencia

MIT

## Autor

Análisis de tendencias de Google Trends
