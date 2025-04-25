
import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

# Estado para campos dinámicos
if "links" not in st.session_state:
    st.session_state.links = [""]

def agregar_link():
    st.session_state.links.append("")

st.button("➕ Agregar otro link", on_click=agregar_link)

inputs = []
for i, val in enumerate(st.session_state.links):
    link = st.text_input(f"Link #{i+1}", value=val, key=f"link_{i}")
    inputs.append(link)

st.subheader("🔗 Links de productos de Mercado Libre")
procesar = st.button("🔍 Comparar vendedores")

def extraer_item_id(url):
    match = re.search(r"(MLM\d+)", url)
    return match.group(1) if match else None

def extraer_seller_id(item_id):
    url = f"https://api.mercadolibre.com/items/{item_id}"
    r = requests.get(url)
    if r.status_code == 200:
        return r.json().get("seller_id")
    return None

def obtener_datos_vendedor(seller_id):
    r = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
    if r.status_code != 200:
        return None
    user = r.json()
    rep = user.get("seller_reputation", {})
    metrics = rep.get("metrics", {})
    trans = rep.get("transactions", {})
    return {
        "Vendedor": user.get("nickname"),
        "Reputación": rep.get("level_id", "N/A"),
        "MercadoLíder": rep.get("power_seller_status", "N/A"),
        "Ventas totales": trans.get("total", 0),
        "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
        "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
        "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
    }

if procesar:
    st.subheader("📊 Comparativa de Vendedores")
    errores = []
    datos = []

    for link in inputs:
        if not link.strip():
            continue
        item_id = extraer_item_id(link)
        if not item_id:
            errores.append(f"❌ No se pudo extraer item_id del link: {link}")
            continue
        seller_id = extraer_seller_id(item_id)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id de: {link}")
            continue
        info = obtener_datos_vendedor(seller_id)
        if info:
            datos.append(info)
        else:
            errores.append(f"❌ No se pudo obtener datos de vendedor con ID: {seller_id}")

    if datos:
        df = pd.DataFrame(datos)
        st.dataframe(df)

        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas totales"], color='orange')
        ax.set_ylabel("Ventas totales")
        ax.set_xticklabels(df["Vendedor"], rotation=45, ha="right")
        st.pyplot(fig)

    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(err)
