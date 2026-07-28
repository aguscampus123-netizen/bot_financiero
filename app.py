import os
import pandas as pd
import streamlit as st
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Bot Analista Financiero - Completo", page_icon="📈", layout="wide"
)

st.title("📊 Panel de Análisis Fundamental - Sincronizado y Completo")
st.write("Tus métricas originales intactas combinadas con actualización automática.")

@st.cache_data(ttl=600)
def cargar_y_fusionar_planilla():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
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
    df_sheet = pd.DataFrame(data)
    df_sheet = df_sheet.dropna(how="all")
    
    columna_ticker = None
    for col in df_sheet.columns:
        if any(k in col.lower() for k in ["ticker", "simbolo", "activo"]):
            columna_ticker = col
            break
            
    if not columna_ticker:
        return df_sheet, "Atención: No se detectó columna de Ticker."

    # Mantenemos todas tus columnas de la planilla y solo actualizamos/completamos precios o datos faltantes con yfinance
    filas_procesadas = []
    for index, row in df_sheet.iterrows():
        fila = row.to_dict()
        ticker = str(fila[columna_ticker]).strip()
        
        if ticker and ticker != "nan":
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Si la capitalización o el precio están vacíos en tu planilla, los completa solo
                if "Capitalizacion" in fila and (not fila["Capitalizacion"] or fila["Capitalizacion"] == 0):
                    fila["Capitalizacion"] = info.get("marketCap", "N/D")
            except Exception:
                pass
                
        filas_procesadas.append(fila)
        
    return pd.DataFrame(filas_procesadas), "¡Planilla cargada manteniendo todas tus columnas y márgenes!"

try:
    df_final, mensaje = cargar_y_fusionar_planilla()
    st.success(mensaje)
    st.subheader(f"Total de Activos Monitoreados: {len(df_final)}")
    st.dataframe(df_final, use_container_width=True)
    
except Exception as e:
    st.error(f"Error al procesar la planilla: {e}")