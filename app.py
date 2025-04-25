
import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores", layout="wide")
st.title("📊 Comparador de Vendedores desde Links de Productos")

# Entrada de URLs
input_links = st.text_area("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):", height=200)
comparar_btn = st.button("🔍 Comparar vendedores")

# Función para extraer seller_id desde una URL de producto
def extraer_seller_id_desde_url(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True)
        match = re.search(r"/MLM(\d+)", r.url)
        if not match:
            return None
        item_id = f"MLM{match.group(1)}"
        res = requests.get(f"https://api.mercadolibre.com/items/{item_id}")
        if res.status_code != 200:
            return None
        return res.json().get("seller_id")
    except:
        return None

# Función para obtener los datos del vendedor
def obtener_datos_vendedor(seller_id):
    try:
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
            "Ventas": trans.get("total", 0),
            "Reclamos %": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
            "Demoras %": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
            "Cancelaciones %": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
        }
    except:
        return None

# Ejecución del comparador
if comparar_btn and input_links:
    urls = [line.strip() for line in input_links.splitlines() if line.strip()]
    datos = []
    errores = []

    for url in urls[:10]:
        seller_id = extraer_seller_id_desde_url(url)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id de: {url}")
            continue

        info = obtener_datos_vendedor(seller_id)
        if info:
            datos.append(info)
        else:
            errores.append(f"❌ No se pudo obtener info de vendedor: {seller_id}")

    if datos:
        df = pd.DataFrame(datos)
        st.subheader("📋 Comparación de Vendedores")
        st.dataframe(df)

        st.subheader("📊 Gráfico de Ventas Totales")
        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas"], color='orange')
        ax.set_ylabel("Ventas Totales")
        ax.set_xticklabels(df["Vendedor"], rotation=45, ha="right")
        st.pyplot(fig)

    if errores:
        st.warning("Se encontraron errores:")
        st.markdown("<br>".join(errores), unsafe_allow_html=True)
