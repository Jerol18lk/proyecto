import pandas as pd
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
        match = re.search(r'(\d+\.\d+)', str(r))
        if match:
            return float(match.group(1))
        return 0.0

    df['Rating_Clean'] = df['Rating'].apply(parsear_rating)
    
    return df[['Match_ID', 'Player', 'Bounty_USD', 'Kills', 'Deaths', 'Rating_Clean']]
