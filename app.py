import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

if "links" not in st.session_state:
    st.session_state.links = [""]

def agregar_link():
    st.session_state.links.append("")

st.subheader("🔗 Links de productos de Mercado Libre")
for i, link in enumerate(st.session_state.links):
    st.session_state.links[i] = st.text_input(f"Link #{i+1}", value=link, key=f"link_{i}")

st.button("➕ Agregar otro link", on_click=agregar_link)

def extraer_item_id(url):
    match = re.search(r"/(MLM\d+)", url)
    return match.group(1) if match else None

def obtener_seller_id_desde_item(item_id):
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{item_id}")
        if r.status_code == 200:
            return r.json().get("seller_id")
    except:
        return None

def obtener_datos_vendedor(seller_id):
    try:
        res = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
        if res.status_code == 200:
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
    except:
        return None

if st.button("🔍 Comparar vendedores"):
    resultados = []
    errores = []

    for link in st.session_state.links:
        if not link.strip():
            continue
        item_id = extraer_item_id(link)
        if not item_id:
            errores.append(f"❌ No se pudo extraer item_id del link: {link}")
            continue

        seller_id = obtener_seller_id_desde_item(item_id)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id del item: {link}")
            continue

        datos = obtener_datos_vendedor(seller_id)
        if datos:
            resultados.append(datos)
        else:
            errores.append(f"❌ No se pudo obtener datos del vendedor con seller_id {seller_id} para: {link}")

    if resultados:
        st.subheader("📊 Comparativa de Vendedores")
        df = pd.DataFrame(resultados)
        st.dataframe(df)

        st.subheader("📈 Gráfico de Ventas Totales")
        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas totales"], color='orange')
        ax.set_ylabel("Ventas")
        st.pyplot(fig)

    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(f"- {err}")
