
import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")
links_input = st.text_area("Links de productos", height=200)
comparar = st.button("🔍 Comparar vendedores")

def extraer_product_id(url):
    match = re.search(r"MLM\d{8}", url)
    return match.group(0) if match else None

def obtener_seller_id_desde_producto(product_id):
    try:
        res = requests.get(f"https://api.mercadolibre.com/items/{product_id}")
        if res.status_code == 200:
            return res.json().get("seller_id")
    except:
        return None
    return None

def obtener_datos_vendedor(seller_id):
    res = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
    return res.json() if res.status_code == 200 else None

if comparar and links_input:
    links = [l.strip() for l in links_input.splitlines() if l.strip()]
    links = links[:10]

    errores = []
    resultados = []

    for link in links:
        product_id = extraer_product_id(link)
        if not product_id:
            errores.append(f"❌ No se pudo extraer product_id de: {link}")
            continue
        seller_id = obtener_seller_id_desde_producto(product_id)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id de: {link}")
            continue
        datos = obtener_datos_vendedor(seller_id)
        if not datos:
            errores.append(f"❌ No se pudieron obtener datos del vendedor desde: {link}")
            continue

        rep = datos.get("seller_reputation", {})
        trans = rep.get("transactions", {})
        metrics = rep.get("metrics", {})

        resultados.append({
            "Nickname": datos.get("nickname", "N/A"),
            "Ventas": trans.get("total", 0),
            "Reputación": rep.get("level_id", "N/A"),
            "Líder": rep.get("power_seller_status", "N/A"),
            "Reclamos": round(metrics.get("claims", {}).get("rate", 0)*100, 2),
            "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0)*100, 2),
            "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0)*100, 2)
        })

    if resultados:
        df = pd.DataFrame(resultados)
        st.subheader("📊 Comparativa de Vendedores")
        st.dataframe(df)

        fig, ax = plt.subplots()
        ax.bar(df["Nickname"], df["Ventas"], color='orange')
        ax.set_ylabel("Ventas Totales")
        ax.set_xticklabels(df["Nickname"], rotation=45, ha="right")
        st.pyplot(fig)

    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(err)
