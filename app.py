
import streamlit as st
import requests
import re
import pandas as pd

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

if "link_count" not in st.session_state:
    st.session_state.link_count = 1

def agregar_link():
    st.session_state.link_count += 1

st.button("➕ Agregar otro link", on_click=agregar_link)

links = []
with st.container():
    st.markdown("### 🔗 Links de productos de Mercado Libre")
    for i in range(st.session_state.link_count):
        link = st.text_input(f"Link #{i+1}", key=f"link_{i}")
        if link:
            links.append(link)

def extraer_item_id(url):
    match = re.search(r"/MLM(\d+)", url)
    return f"MLM{match.group(1)}" if match else None

def obtener_datos_vendedor(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    res = requests.get(url)
    return res.json() if res.status_code == 200 else None

def obtener_seller_id(item_id):
    url = f"https://api.mercadolibre.com/items/{item_id}"
    res = requests.get(url)
    if res.status_code == 200:
        return res.json().get("seller_id")
    return None

def obtener_reputacion(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}"
    res = requests.get(url)
    if res.status_code != 200:
        return None
    data = res.json()
    rep = data.get("seller_reputation", {})
    trans = rep.get("transactions", {})
    metrics = rep.get("metrics", {})
    return {
        "Vendedor": data.get("nickname"),
        "Reputación": rep.get("level_id"),
        "MercadoLíder": rep.get("power_seller_status"),
        "Estado": data.get("status", {}).get("site_status"),
        "Ventas totales": trans.get("total", 0),
        "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
        "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
        "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
    }

if st.button("🔍 Comparar vendedores"):
    st.subheader("📊 Comparativa de Vendedores")
    resultados = []
    errores = []
    for link in links:
        item_id = extraer_item_id(link)
        if not item_id:
            errores.append(f"No se pudo extraer item_id del link: {link}")
            continue
        seller_id = obtener_seller_id(item_id)
        if not seller_id:
            errores.append(f"No se pudo extraer seller_id del item: {link}")
            continue
        datos = obtener_reputacion(seller_id)
        if datos:
            resultados.append(datos)
        else:
            errores.append(f"No se pudieron obtener datos del vendedor para: {link}")

    if resultados:
        df = pd.DataFrame(resultados)
        st.dataframe(df)

    if errores:
        st.error("Se encontraron errores:")
        for e in errores:
            st.markdown(f"- ❌ {e}")
