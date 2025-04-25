
import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")

st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

# Guardar la cantidad de links agregados en el estado de sesión
if "num_links" not in st.session_state:
    st.session_state.num_links = 1

# Botón para agregar nuevos campos
if st.button("➕ Agregar otro link") and st.session_state.num_links < 10:
    st.session_state.num_links += 1

# Mostrar campos dinámicos
links = []
st.subheader("🔗 Links de productos de Mercado Libre")
for i in range(st.session_state.num_links):
    link = st.text_input(f"Link #{i+1}", key=f"link_{i}")
    if link:
        links.append(link)

# Función para extraer seller_id
def obtener_seller_id(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True)
        if r.status_code != 200:
            return None
        match = re.search(r"MLM\d+", r.url)
        if not match:
            return None
        product_id = match.group(0)
        item_data = requests.get(f"https://api.mercadolibre.com/items/{product_id}").json()
        return item_data.get("seller_id")
    except:
        return None

# Función para obtener info del vendedor
def obtener_info_vendedor(seller_id):
    try:
        user = requests.get(f"https://api.mercadolibre.com/users/{seller_id}").json()
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
            "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2),
        }
    except:
        return None

# Procesamiento al presionar el botón
if st.button("🔍 Comparar vendedores"):
    vendedores = []
    errores = []
    for link in links:
        seller_id = obtener_seller_id(link)
        if not seller_id:
            errores.append(link)
            continue
        info = obtener_info_vendedor(seller_id)
        if info:
            vendedores.append(info)

    if vendedores:
        df = pd.DataFrame(vendedores)
        st.subheader("📋 Comparativa de Vendedores")
        st.dataframe(df)

    if errores:
        st.error("❌ No se pudo extraer seller_id de los siguientes enlaces:")
        for e in errores:
            st.markdown(f"- {e}")
