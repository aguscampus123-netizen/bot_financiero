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

@st.cache_data(ttl=600)
def cargar_datos_desde_sheet():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # Lee las variables directas de los Secrets
    if "private_key" in st.secrets:
        creds_dict = {
            "type": st.secrets["type"],
            "project_id": st.secrets["project_id"],
            "private_key_id": st.secrets["private_key_id"],
            "private_key": st.secrets["private_key"],
            "client_email": st.secrets["client_email"],
            "client_id": st.secrets["client_id"],
            "auth_uri": st.secrets["auth_uri"],
            "token_uri": st.secrets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["client_x509_cert_url"],
            "universe_domain": st.secrets["universe_domain"]
        }
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        filename = [f for f in os.listdir(current_dir) if "credentials" in f][0]
        cred_path = os.path.join(current_dir, filename)
        creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)
    
    client = gspread.authorize(creds)
    sheet = client.open("Analisis_Fundamental_Mercado").sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

try:
    df = cargar_datos_desde_sheet()
    st.subheader(f"Total de Activos Escaneados: {len(df)}")
    st.dataframe(df, use_container_width=True)
except Exception as e:
    st.error(f"Error al conectar con la planilla: {e}")