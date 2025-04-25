import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

if "links" not in st.session_state:
    st.session_state.links = [""]

def agregar_link():
    st.session_state.links.append("")

st.button("➕ Agregar otro link", on_click=agregar_link)

st.subheader("🔗 Links de productos de Mercado Libre")

inputs = []
for i, link in enumerate(st.session_state.links):
    new_val = st.text_input(f"Link #{i+1}", value=link, key=f"link_{i}")
    inputs.append(new_val)

def extraer_seller_id_desde_link(url):
    try:
        match = re.search(r"/(MLM\d+)", url)
        if not match:
            return None, "❌ No se pudo extraer item_id"
        product_id = match.group(1)
        r = requests.get(f"https://api.mercadolibre.com/items/{product_id}")
        if r.status_code != 200:
            return None, f"❌ No se pudo consultar API para {product_id}"
        data = r.json()
        seller_id = data.get("seller_id")
        nickname = data.get("seller_nickname", "")
        return seller_id, nickname
    except Exception as e:
        return None, str(e)

def obtener_datos_vendedor(seller_id):
    res = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
    if res.status_code != 200:
        return None
    user = res.json()
    rep = user.get("seller_reputation", {})
    metrics = rep.get("metrics", {})
    trans = rep.get("transactions", {})
    return {
        "Vendedor": user.get("nickname"),
        "Reputación": rep.get("level_id", "N/A"),
        "MercadoLíder": rep.get("power_seller_status", "N/A"),
        "Estado": user.get("status", {}).get("site_status", "N/D"),
        "Ventas totales": trans.get("total", 0),
        "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
        "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
        "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
    }

if st.button("🔍 Comparar vendedores"):
    errores = []
    datos_vendedores = []

    for link in inputs:
        if not link.strip():
            continue
        seller_id, msg = extraer_seller_id_desde_link(link)
        if not seller_id:
            errores.append(f"{msg}: {link}")
            continue
        datos = obtener_datos_vendedor(seller_id)
        if datos:
            datos_vendedores.append(datos)
        else:
            errores.append(f"❌ No se pudo obtener datos del vendedor con seller_id {seller_id}")

    st.subheader("📊 Comparativa de Vendedores")
    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(f"- {err}")

    if datos_vendedores:
        df = pd.DataFrame(datos_vendedores)
        st.dataframe(df)

        st.markdown("### 📈 Gráfico de Ventas Totales")
        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas totales"], color='skyblue')
        ax.set_ylabel("Ventas totales")
        ax.set_xticklabels(df["Vendedor"], rotation=45, ha="right")
        st.pyplot(fig)
