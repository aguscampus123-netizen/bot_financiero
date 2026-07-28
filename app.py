import os
import pandas as pd
import streamlit as st
import gspread
import yfinance as yf
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(
    page_title="Bot Analista Financiero Automático", page_icon="📈", layout="wide"
)

st.title("📊 Panel de Análisis Fundamental - 100% Automatizado")
st.write(
    "Escribe el Ticker en tu Google Sheet y el bot buscará y calculará toda la"
    " info solo."
)


@st.cache_data(ttl=600)
def cargar_y_buscar_automatico():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]

  # Conexión a tus credenciales (Secrets o local)
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
        "universe_domain": st.secrets["universe_domain"],
    }
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
  else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    filename = [f for f in os.listdir(current_dir) if "credentials" in f][0]
    cred_path = os.path.join(current_dir, filename)
    creds = ServiceAccountCredentials.from_json_keyfile_name(cred_path, scope)

  # Conexión a Google Sheets
  client = gspread.authorize(creds)
  sheet = client.open("Analisis_Fundamental_Mercado").sheet1

  # Traemos los datos de la planilla
  data = sheet.get_all_records()
  df_sheet = pd.DataFrame(data)
  df_sheet = df_sheet.dropna(how="all")

  # Identificar en qué columna están los Tickers (ej: 'Ticker', 'Simbolo', 'Activo')
  columna_ticker = None
  for col in df_sheet.columns:
    if any(k in col.lower() for k in ["ticker", "simbolo", "activo"]):
      columna_ticker = col
      break

  if not columna_ticker:
    return (
        df_sheet,
        "No se encontró una columna de Ticker en tu Sheet. Por favor nombra"
        " una columna como 'Ticker'.",
    )

  # Recorremos cada fila, leemos el Ticker y buscamos la info fresca en internet
  resultados_automaticos = []

  for index, row in df_sheet.iterrows():
    ticker = str(row[columna_ticker]).strip()

    if ticker and ticker != "nan":
      try:
        stock = yf.Ticker(ticker)
        info = stock.info

        # Extraemos los datos clave de internet automáticamente
        nombre = info.get("longName", ticker)
        precio = info.get("currentPrice", info.get("regularMarketPrice", 0))
        cap_mercado = info.get("marketCap", 0)

        roe = info.get("returnOnEquity", None)
        roa = info.get("returnOnAssets", None)
        pb = info.get("priceToBook", None)
        pe = info.get("trailingPE", None)

        resultados_automaticos.append({
            "Ticker": ticker,
            "Empresa / Institución": nombre,
            "Precio Actual ($)": precio,
            "Cap. de Mercado": cap_mercado,
            "ROE (%)": round(roe * 100, 2) if roe else "N/D",
            "ROA (%)": round(roa * 100, 2) if roa else "N/D",
            "P/B (Precio/Libros)": round(pb, 2) if pb else "N/D",
            "P/E (Precio/Utilidad)": round(pe, 2) if pe else "N/D",
        })
      except Exception:
        # Si falla algún ticker puntual, conservamos al menos los datos de la fila original
        resultados_automaticos.append(row.to_dict())

  return (
      pd.DataFrame(resultados_automaticos),
      "¡Información de mercado descargada y sincronizada automáticamente!",
  )


try:
  df_final, mensaje = cargar_y_buscar_automatico()
  st.success(mensaje)
  st.subheader(f"Total de Activos Monitoreados: {len(df_final)}")

  # Mostramos la tabla interactiva
  st.dataframe(df_final, use_container_width=True)

except Exception as e:
  st.error(f"Error al procesar la automatización: {e}")