import pandas as pd
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
