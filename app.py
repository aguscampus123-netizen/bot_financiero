import os
import pandas as pd
import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Bot Analista Financiero", page_icon="📈", layout="wide"
)

st.title("📊 Panel de Análisis Fundamental - Mercado Global")
st.write("Visualización sincronizada directamente desde tu Google Sheet.")

# Función para conectar y leer los datos de Google Sheets
@st.cache_data(ttl=600) # Caché de 10 minutos para optimizar lecturas
def cargar_datos_desde_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = [f for f in os.listdir(current_dir) if "credentials" in f][0]
    cred_path = os.path.join(current_dir, filename)

    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
    client = gspread.authorize(creds)
    
    # Abre la planilla exacta
    sheet = client.open("Analisis_Fundamental_Mercado").sheet1
    
    # Trae todos los registros a un DataFrame de Pandas
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Intentar mostrar los datos en la app
try:
    df = cargar_datos_desde_sheet()
    
    st.subheader(f"Total de Activos Escaneados: {len(df)}")
    
    # Muestra la tabla completa interactiva con todas las columnas y empresas
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error al conectar con la planilla: {e}")
    st.info("Asegúrate de que el archivo credentials.json esté en la misma carpeta.")