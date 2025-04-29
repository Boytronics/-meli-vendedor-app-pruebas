
import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")
st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

if "inputs" not in st.session_state:
    st.session_state.inputs = [""]

def agregar_input():
    st.session_state.inputs.append("")

with st.expander("🔗 Links de productos de Mercado Libre", expanded=True):
    for i, val in enumerate(st.session_state.inputs):
        st.session_state.inputs[i] = st.text_input(f"Link #{i+1}", value=val, key=f"link_{i}")
    st.button("➕ Agregar otro link", on_click=agregar_input)

def extraer_item_id(url):
    match = re.search(r"(MLM\d+)", url)
    return match.group(1) if match else None

def obtener_seller_id(item_id):
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{item_id}")
        if r.status_code == 200:
            return r.json().get("seller_id")
    except:
        return None

def obtener_datos_vendedor(seller_id):
    r = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
    return r.json() if r.status_code == 200 else {}

def obtener_reputacion(vendedor):
    rep = vendedor.get("seller_reputation", {})
    trans = rep.get("transactions", {})
    metrics = rep.get("metrics", {})
    return {
        "Vendedor": vendedor.get("nickname", ""),
        "Reputación": rep.get("level_id", ""),
        "MercadoLíder": rep.get("power_seller_status", ""),
        "Ventas totales": trans.get("total", 0),
        "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
        "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
        "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
    }

if st.button("🔍 Comparar vendedores"):
    errores = []
    datos_vendedores = []

    for url in st.session_state.inputs:
        if not url.strip():
            continue
        item_id = extraer_item_id(url)
        if not item_id:
            errores.append(f"❌ No se pudo extraer item_id del link: {url}")
            continue

        seller_id = obtener_seller_id(item_id)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id del item: {url}")
            continue

        datos = obtener_datos_vendedor(seller_id)
        if datos:
            datos_vendedores.append(obtener_reputacion(datos))

    if datos_vendedores:
        st.subheader("📊 Comparativa de Vendedores")
        df = pd.DataFrame(datos_vendedores)
        st.dataframe(df)

    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(f"- {err}")
