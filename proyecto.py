import os

# 1. Crear la estructura de directorios exigida por la guía
os.makedirs('datos', exist_ok=True)
os.makedirs('src', exist_ok=True)

# Generar datos sucios de partidas en la carpeta correcta
with open('datos/esports_partidas_raw.csv', 'w', encoding='utf-8') as f:
    f.write("Match_ID,Player,Bounty,Kills,Deaths,Rating\n")
    f.write("M-01,  ViperX ,$1,500.50,24,5,8.9 MVP\n")
    f.write("M-02, ShadowZ,$900,12,0,7.2\n")
    f.write("M-02, ShadowZ,$900,12,0,7.2\n")
    f.write("M-03,  Ghost ,$450K,8,12,6.1\n")

# 2. Archivo de Dependencias
with open('requirements.txt', 'w') as f:
    f.write("pandas\nnumpy\nsqlalchemy\npyarrow\nfastparquet\n")

# 3. Control de Versiones (Excluir archivos masivos y bases de datos locales)
with open('.gitignore', 'w') as f:
    f.write("datos/\n__pycache__/\n*.db\n")

# 4. Módulo de Transformación (src/transformacion.py)
with open('src/transformacion.py', 'w', encoding='utf-8') as f:
    f.write('''import pandas as pd
import re

def limpiar_datos(df):
    # Eliminar duplicados exactos y limpiar espacios en el nombre del jugador
    df = df.drop_duplicates(subset=['Match_ID', 'Player'], keep='first').copy()
    df['Player'] = df['Player'].str.strip()
    
    def parsear_bounty(b):
        b = str(b).replace('$', '').replace(',', '').strip()
        if 'K' in b: 
            return float(b.replace('K', '')) * 1000
        try:
            return float(b)
        except:
            return 0.0
    
    df['Bounty_USD'] = df['Bounty'].apply(parsear_bounty)
    
    # Extraer únicamente el puntaje numérico del rating usando expresiones regulares
    def parsear_rating(r):
        match = re.search(r'(\\d+\\.\\d+)', str(r))
        if match:
            return float(match.group(1))
        return 0.0

    df['Rating_Clean'] = df['Rating'].apply(parsear_rating)
    
    return df[['Match_ID', 'Player', 'Bounty_USD', 'Kills', 'Deaths', 'Rating_Clean']]
''')

# 5. Módulo de Carga e Idempotencia (src/carga.py)
with open('src/carga.py', 'w', encoding='utf-8') as f:
    f.write('''import pandas as pd
import logging
from sqlalchemy import create_engine, text

motor_bd = create_engine('sqlite:///datos/esports_almacen.db')

def cargar_sqlite_idempotente(df_lote):
    with motor_bd.connect() as conexion:
        try:
            res = pd.read_sql(text("SELECT Match_ID, Player FROM partidas_dim"), con=conexion)
            existentes = set(zip(res['Match_ID'], res['Player']))
        except:
            existentes = set()
            
        # Filtrar solo registros que no existan previamente (Idempotencia)
        df_nuevos = df_lote[~df_lote.apply(lambda row: (row['Match_ID'], row['Player']) in existentes, axis=1)]
        if not df_nuevos.empty:
            df_nuevos.to_sql('partidas_dim', con=motor_bd, if_exists='append', index=False)
            logging.info(f"Cargados {len(df_nuevos)} registros nuevos en SQLite.")
''')

# 6. Orquestador Principal con Manejo Defensivo de Memoria (main.py)
with open('main.py', 'w', encoding='utf-8') as f:
    f.write('''import pandas as pd
import logging
from src.transformacion import limpiar_datos
from src.carga import cargar_sqlite_idempotente

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def ejecutar_pipeline():
    logging.info("Arrancando Pipeline Orquestador de E-Sports...")
    ruta = 'datos/esports_partidas_raw.csv'
    
    # Lectura fraccionada por bloques (chunks) para optimizar memoria
    iterador_lotes = pd.read_csv(ruta, sep=',', encoding='utf-8', chunksize=2, low_memory=False)
    
    df_completo = []
    for num, lote in enumerate(iterador_lotes):
        logging.info(f"Procesando lote {num + 1}...")
        lote_limpio = limpiar_datos(lote)
        cargar_sqlite_idempotente(lote_limpio)
        df_completo.append(lote_limpio)
        
    # Exportación final a formato analítico Parquet
    if df_completo:
        df_final = pd.concat(df_completo)
        df_final.to_parquet('datos/esports_analitica.parquet', index=False)
        logging.info("Pipeline de E-Sports completado exitosamente.")

if __name__ == "__main__":
    ejecutar_pipeline()
''')

print("¡Listo! Proyecto de E-Sports estructurado con éxito. Ya puedes ejecutar 'python main.py'.")