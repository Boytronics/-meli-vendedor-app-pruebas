
import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador Vendedores por Links", layout="wide")
st.title("📦 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por campo):")

urls = []
for i in range(10):
    url = st.text_input(f"Ingreso del producto #{i+1}", key=f"url_{i}")
    if url:
        urls.append(url)

def obtener_seller_id(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True)
        match = re.search(r"/MLM(\d+)", r.url)
        if not match:
            return None
        product_id = f"MLM{match.group(1)}"
        item_res = requests.get(f"https://api.mercadolibre.com/items/{product_id}")
        if item_res.status_code != 200:
            return None
        return item_res.json().get("seller_id")
    except:
        return None

def obtener_info_seller(seller_id):
    try:
        res = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
        if res.status_code != 200:
            return None
        data = res.json()
        rep = data.get("seller_reputation", {})
        trans = rep.get("transactions", {})
        return {
            "Nickname": data.get("nickname"),
            "Reputación": rep.get("level_id", "N/A"),
            "MercadoLíder": rep.get("power_seller_status", "N/A"),
            "Ventas Totales": trans.get("total", 0),
            "Estado": data.get("status", {}).get("site_status", "N/A")
        }
    except:
        return None

if st.button("🔍 Comparar vendedores"):
    resultados = []
    errores = []

    for url in urls:
        seller_id = obtener_seller_id(url)
        if not seller_id:
            errores.append(f"No se pudo extraer seller_id de: {url}")
            continue
        datos = obtener_info_seller(seller_id)
        if datos:
            resultados.append(datos)
        else:
            errores.append(f"No se pudo obtener datos del seller_id: {seller_id}")

    if resultados:
        df = pd.DataFrame(resultados)
        st.subheader("📊 Comparativa de Vendedores")
        st.dataframe(df)

        fig, ax = plt.subplots()
        ax.bar(df["Nickname"], df["Ventas Totales"], color='skyblue')
        ax.set_ylabel("Ventas Totales")
        ax.set_title("Comparación de Ventas por Vendedor")
        ax.set_xticklabels(df["Nickname"], rotation=45, ha="right")
        st.pyplot(fig)

    if errores:
        st.warning("⚠️ Se encontraron errores:")
        for e in errores:
            st.markdown(f"❌ {e}")
