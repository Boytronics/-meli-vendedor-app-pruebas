
import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Comparador de Vendedores", layout="wide")

st.title("🔍 Comparador de Vendedores desde Links de Productos")
st.write("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

# Contenedor dinámico
if "urls" not in st.session_state:
    st.session_state.urls = [""]

def add_url_input():
    st.session_state.urls.append("")

st.button("➕ Agregar otro link", on_click=add_url_input)

with st.expander("🔗 Links de productos de Mercado Libre", expanded=True):
    for i, url in enumerate(st.session_state.urls):
        st.session_state.urls[i] = st.text_input(f"Link #{i+1}", value=url, key=f"url_{i}")

# Función para extraer item_id desde la URL
def obtener_item_id(url):
    patrones = [
        r"/MLM(\d+)",
        r"/MLA(\d+)",
        r"items/(\d+)"
    ]
    for patron in patrones:
        match = re.search(patron, url)
        if match:
            return f"MLM{match.group(1)}" if 'MLM' in patron else f"MLA{match.group(1)}"
    return None

# Función para obtener el seller_id desde item_id
def obtener_seller_id(item_id):
    res = requests.get(f"https://api.mercadolibre.com/items/{item_id}")
    if res.status_code == 200:
        return res.json().get("seller_id")
    return None

# Función para obtener datos del vendedor
def obtener_datos_vendedor(seller_id):
    res = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
    if res.status_code == 200:
        return res.json()
    return None

# Procesamiento
if st.button("🔍 Comparar vendedores"):
    datos_vendedores = []
    errores = []
    for url in st.session_state.urls:
        if not url.strip():
            continue
        item_id = obtener_item_id(url)
        if not item_id:
            errores.append(f"❌ No se pudo extraer item_id del link: {url}")
            continue
        seller_id = obtener_seller_id(item_id)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id del item: {url}")
            continue
        datos = obtener_datos_vendedor(seller_id)
        if datos:
            reputacion = datos.get("seller_reputation", {})
            trans = reputacion.get("transactions", {})
            metrics = reputacion.get("metrics", {})
            datos_vendedores.append({
                "Vendedor": datos.get("nickname"),
                "Reputación": reputacion.get("level_id", "N/A"),
                "MercadoLíder": reputacion.get("power_seller_status", "N/A"),
                "Ventas totales": trans.get("total", 0),
                "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
                "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
                "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2),
            })
        else:
            errores.append(f"❌ No se pudo obtener datos del vendedor: {seller_id}")

    if errores:
        st.error("Se encontraron errores:")
        for e in errores:
            st.markdown(f"- {e}")

    if datos_vendedores:
        st.subheader("📊 Comparativa de Vendedores")
        df = pd.DataFrame(datos_vendedores)
        st.dataframe(df)
