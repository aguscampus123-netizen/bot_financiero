import os
import pandas as pd
import streamlit as st
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Bot Analista Financiero - Sincronizado", page_icon="📈", layout="wide"
)

st.title("📊 Panel de Análisis Fundamental - Sincronizado con Google Sheet")
st.write("Leyendo tus activos guardados y buscando métricas en tiempo real.")

@st.cache_data(ttl=600)
def cargar_y_analizar_activos():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    # 1. Conexión a tus credenciales (Secrets o local)
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
    
    # 2. Leer la planilla de Google Sheets
    client = gspread.authorize(creds)
    sheet = client.open("Analisis_Fundamental_Mercado").sheet1
    data = sheet.get_all_records()
    df_sheet = pd.DataFrame(data)
    
    # Verificamos si la planilla tiene una columna de Tickers (ej: 'Ticker' o 'Simbolo')
    columna_ticker = None
    for col in df_sheet.columns:
        if any(k in col.lower() for k in ["ticker", "simbolo", "activo"]):
            columna_ticker = col
            break
            
    if not columna_ticker:
        return df_sheet, "No se encontró una columna llamada 'Ticker' o 'Simbolo' en tu Sheet, mostrando datos originales."

    # 3. Extraer datos automáticos de yfinance para cada ticker de la planilla
    datos_enriquecidos = []
    for index, row in df_sheet.iterrows():
        t = str(row[columna_ticker]).strip()
        fila_actual = row.to_dict()
        
        try:
            stock = yf.Ticker(t)
            info = stock.info
            
            # Agregamos o actualizamos métricas clave automáticamente
            fila_actual["Precio Actual ($)"] = info.get("currentPrice", info.get("regularMarketPrice", "N/D"))
            roe = info.get("returnOnEquity", None)
            roa = info.get("returnOnAssets", None)
            fila_actual["ROE (%)"] = round(roe * 100, 2) if roe else fila_actual.get("ROE (%)", "N/D")
            fila_actual["ROA (%)"] = round(roa * 100, 2) if roa else fila_actual.get("ROA (%)", "N/D")
            fila_actual["P/B"] = round(info.get("priceToBook", 0), 2) if info.get("priceToBook") else fila_actual.get("P/B", "N/D")
        except Exception:
            pass # Si falla un ticker particular, mantiene lo que tenía la planilla
            
        datos_enriquecidos.append(fila_actual)
        
    return pd.DataFrame(datos_enriquecidos), "¡Datos sincronizados y enriquecidos con éxito!"

try:
    df_final, mensaje = cargar_y_analizar_activos()
    st.success(mensaje)
    st.subheader(f"Total de Activos en la Lista: {len(df_final)}")
    st.dataframe(df_final, use_container_width=True)
    
except Exception as e:
    st.error(f"Error al conectar con la planilla o procesar los activos: {e}")