import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(
    page_title="Bot Analista Financiero Automático", page_icon="🤖", layout="wide"
)

st.title("🤖 Bot Inteligente de Análisis Financiero - Bancos & Activos")
st.write(
    "Este bot extrae automáticamente los datos y calcula métricas clave del"
    " mercado en tiempo real."
)

# 1. Lista de activos financieros que quieres analizar (puedes agregar los que quieras)
tickers_por_defecto = [
    "JPM",
    "BAC",
    "GS",
    "MS",
    "GGAL.BA",
    "BMA",
]  # Bancos de EE.UU. y Argentina

st.sidebar.header("⚙️ Configuración")
tickers_seleccionados = st.sidebar.multiselect(
    "Selecciona los activos a escanear:",
    options=tickers_por_defecto,
    default=tickers_por_defecto,
)


# 2. Función para buscar y calcular automáticamente los datos fundamentales
@st.cache_data(ttl=3600)
def obtener_datos_financieros(tickers):
  datos_lista = []

  for t in tickers:
    try:
      stock = yf.Ticker(t)
      info = stock.info

      # Extraemos datos fundamentales clave (manejando valores vacíos por seguridad)
      nombre = info.get("longName", t)
      precio = info.get("currentPrice", info.get("regularMarketPrice", 0))
      cap_mercado = info.get("marketCap", 0)
      roe = info.get("returnOnEquity", 0)
      roa = info.get("returnOnAssets", 0)
      pb = info.get("priceToBook", 0)
      pe = info.get("trailingPE", 0)

      datos_lista.append({
          "Ticker": t,
          "Institución": nombre,
          "Precio ($)": precio,
          "Cap. de Mercado": cap_mercado,
          "ROE (%)": round(roe * 100, 2) if roe else "N/D",
          "ROA (%)": round(roa * 100, 2) if roa else "N/D",
          "P/B (Precio/Libros)": round(pb, 2) if pb else "N/D",
          "P/E (Precio/Utilidad)": round(pe, 2) if pe else "N/D",
      })
    except Exception as e:
      print(f"Error al traer datos de {t}: {e}")

  return pd.DataFrame(datos_lista)


# 3. Mostrar la tabla en la aplicación web
if tickers_seleccionados:
  with st.spinner("Buscando información financiera actualizada en la web..."):
    df_resultado = obtener_datos_financieros(tickers_seleccionados)

  st.subheader(f"Resultados del Análisis ({len(df_resultado)} activos)")
  st.dataframe(df_resultado, use_container_width=True)
else:
  st.warning("Por favor, selecciona al menos un activo en la barra lateral.")