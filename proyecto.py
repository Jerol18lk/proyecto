import pandas as pd
import sqlite3
import numpy as np
import os

# 1. GENERACIÓN DEL DATASET SUCIO (La extracción)
def generar_datos_crudos():
    datos = {
        'Match_ID': ['M01', 'M02', 'M02', 'M03', 'M04', 'M05', 'M06'],
        'Equipo': ['Halcones', 'Lobos', 'Lobos', 'Tigres', 'Halcones', 'Tigres', 'Panteras'],
        'Kills': [25, 12, 12, 30, 5, 18, 22],
        'Deaths': [10, 0, 0, 15, 20, 0, 2], # Peligro matemático: división por cero
        'Duracion': ['15 min', '20m 30s', '20m 30s', '18 min', 'ERROR_SV', '12m', '45 mins'],
        'Ping_ms': [45, 120, 120, np.nan, 999, 30, np.nan] # Datos vacíos y lag falso
    }
    df_crudo = pd.DataFrame(datos)
    os.makedirs('datos', exist_ok=True)
    df_crudo.to_csv('datos/esports_raw.csv', index=False)
    print("1. Archivo crudo 'esports_raw.csv' generado.")

# 2. MÓDULO DE LIMPIEZA Y TRANSFORMACIÓN
def limpiar_partidas(ruta_csv):
    df = pd.read_csv(ruta_csv)
    
    # A. Eliminar registros duplicados idénticos
    df = df.drop_duplicates()
    
    # B. Limpiar la columna de tiempo (Extraer solo los números)
    # Busca el primer grupo de números en textos como "20m 30s" o "15 min"
    df['Minutos_Jugados'] = df['Duracion'].astype(str).str.extract(r'(\d+)').astype(float)
    
    # Filtrar partidas que no se jugaron por errores de servidor
    df = df.dropna(subset=['Minutos_Jugados'])
    
    # C. Arreglar el Ping (Lag)
    # Si no hay dato de ping, o el ping es absurdamente alto (>500), le ponemos el promedio
    ping_promedio = df.loc[df['Ping_ms'] < 500, 'Ping_ms'].mean()
    df['Ping_ms'] = df['Ping_ms'].fillna(ping_promedio)
    df.loc[df['Ping_ms'] > 500, 'Ping_ms'] = ping_promedio
    
    # D. Calcular métrica de rendimiento: K/D Ratio (Bajas / Muertes)
    # np.where evita que el programa colapse al intentar dividir por cero
    df['KD_Ratio'] = np.where(df['Deaths'] == 0, df['Kills'], df['Kills'] / df['Deaths'])
    df['KD_Ratio'] = df['KD_Ratio'].round(2)
    
    # Ordenar las columnas finales
    return df[['Match_ID', 'Equipo', 'Kills', 'Deaths', 'KD_Ratio', 'Minutos_Jugados', 'Ping_ms']]

# 3. ORQUESTADOR Y CARGA
def ejecutar_pipeline():
    generar_datos_crudos()
    
    df_limpio = limpiar_partidas('datos/esports_raw.csv')
    print("\n2. Datos transformados con éxito:")
    print(df_limpio)
    
    # Cargar a SQLite
    conexion = sqlite3.connect('datos/torneo.db')
    df_limpio.to_sql('rendimiento_equipos', conexion, if_exists='replace', index=False)
    conexion.close()
    print("\n3. Base de datos 'torneo.db' creada y actualizada.")

if __name__ == "__main__":
    ejecutar_pipeline()