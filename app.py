import os
import pandas as pd
import streamlit as st
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Bot Analista Financiero - Inteligente", page_icon="📈", layout="wide"
)

st.title("📊 Panel de Análisis Fundamental - Sincronizado y Dinámico")
st.write("Evaluación unificada para empresas industriales y sector financiero.")

@st.cache_data(ttl=600)
def cargar_y_evaluar_planilla():
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

    filas_procesadas = []
    for index, row in df_sheet.iterrows():
        fila = row.to_dict()
        ticker_raw = str(fila[columna_ticker]).strip()
        
        if ticker_raw and ticker_raw != "nan":
            try:
                stock = yf.Ticker(ticker_raw)
                info = stock.info
                
                # 1. Nombre de la empresa al lado del Ticker
                nombre_empresa = info.get("longName", info.get("shortName", ""))
                if nombre_empresa:
                    fila[columna_ticker] = f"{ticker_raw} - {nombre_empresa}"
                
                # 2. ROE y ROA automático
                roe = info.get("returnOnEquity", None)
                if roe and ("ROE (%)" not in fila or not fila["ROE (%)"] or fila["ROE (%)"] == "N/D"):
                    fila["ROE (%)"] = round(roe * 100, 2)
                    
                roa = info.get("returnOnAssets", None)
                if roa and ("ROA (%)" not in fila or not fila["ROA (%)"] == "N/D"):
                    fila["ROA (%)"] = round(roa * 100, 2)
                    
                # 3. Solución dinámica para la columna de estado/puntaje si es banco (N/A)
                columna_estado = None
                for c in fila.keys():
                    if any(k in c.lower() for k in ["puntaje", "estado", "aprobado"]):
                        columna_estado = c
                        break
                
                if columna_estado and ("N/A" in str(fila[columna_estado]) or "Sector Financiero" in str(fila[columna_estado])):
                    roe_val = fila.get("ROE (%)", 0)
                    if isinstance(roe_val, (int, float)) and roe_val > 10:
                        fila[columna_estado] = "Aprobado (Bancario Saludable)"
                    else:
                        fila[columna_estado] = "Revisión (Bancario / ROE Bajo)"
                        
            except Exception:
                pass
                
        filas_procesadas.append(fila)
        
    return pd.DataFrame(filas_procesadas), "¡Panel actualizado con evaluación inteligente para bancos e industriales!"

# Función para pintar de verde o rojo según el estado
def colorear_estados(val):
    val_str = str(val).lower()
    if "aprobado" in val_str or "saludable" in val_str:
        return 'background-color: #d4edda; color: #155724; font-weight: bold;'
    elif "rechazado" in val_str or "revisión" in val_str or "bajo" in val_str:
        return 'background-color: #f8d7da; color: #721c24; font-weight: bold;'
    return ''

try:
    df_final, mensaje = cargar_y_evaluar_planilla()
    st.success(mensaje)
    st.subheader(f"Total de Activos Monitoreados: {len(df_final)}")
    
    # Buscamos la columna de estado para aplicarle el formato condicional de colores
    columna_estado = None
    for c in df_final.columns:
        if any(k in c.lower() for k in ["puntaje", "estado", "aprobado"]):
            columna_estado = c
            break

    if columna_estado:
        df_estilizado = df_final.style.map(colorear_estados, subset=[columna_estado])
        st.dataframe(df_estilizado, use_container_width=True)
    else:
        st.dataframe(df_final, use_container_width=True)
    
except Exception as e:
    st.error(f"Error al procesar la planilla: {e}")