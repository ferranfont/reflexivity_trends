import pandas as pd
from pytrends.request import TrendReq
import matplotlib.pyplot as plt

# Conexión con Google (hl = idioma, tz = zona horaria)
pytrends = TrendReq(hl='es-ES', tz=360)

# Definir palabras clave (máximo 5 por petición)
kw_list = ["Inteligencia Artificial", "Crypto"]

# Crear la carga de trabajo (últimos 5 años)
pytrends.build_payload(kw_list, cat=0, timeframe='today 5-y', geo='ES', gprop='')

# Obtener interés a lo largo del tiempo
data = pytrends.interest_over_time()

# Limpiar datos (eliminar columna 'isPartial')
data = data.drop(labels=['isPartial'], axis='columns')

print(data.head())
print(f"\nDatos desde: {data.index.min()} hasta: {data.index.max()}")
print(f"Total de registros: {len(data)}")

# Crear visualización
plt.figure(figsize=(14, 7))
plt.plot(data.index, data['Inteligencia Artificial'], label='Inteligencia Artificial', linewidth=2, marker='o', markersize=3)
plt.plot(data.index, data['Crypto'], label='Crypto', linewidth=2, marker='s', markersize=3)

plt.title('Tendencias de búsqueda en Google - Últimos 5 años', fontsize=16, fontweight='bold')
plt.xlabel('Fecha', fontsize=12)
plt.ylabel('Interés de búsqueda (0-100)', fontsize=12)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# Guardar y mostrar
plt.savefig('tendencias_5_años.png', dpi=300, bbox_inches='tight')
print("\nGráfico guardado como 'tendencias_5_años.png'")
plt.show()