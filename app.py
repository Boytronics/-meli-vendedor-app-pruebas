import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")

st.title("🔍 Comparador de Vendedores desde Links de Productos")
st.write("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

# Estado para campos dinámicos
if "num_links" not in st.session_state:
    st.session_state.num_links = 1

def agregar_otro_link():
    if st.session_state.num_links < 10:
        st.session_state.num_links += 1

st.button("➕ Agregar otro link", on_click=agregar_otro_link)

# Entradas dinámicas
st.markdown("### 🔗 Links de productos de Mercado Libre")
links = []
for i in range(st.session_state.num_links):
    link = st.text_input(f"Link #{i+1}", key=f"link_{i}")
    if link:
        links.append(link)

def extraer_item_id(url):
    """Extrae el MLM ID desde el link"""
    match = re.search(r"/(MLM[-_]?\d+)", url)
    if match:
        return match.group(1).replace("-", "").replace("_", "")
    return None

def obtener_seller_id(item_id):
    """Consulta el seller_id desde el item_id"""
    try:
        r = requests.get(f"https://api.mercadolibre.com/items/{item_id}")
        if r.status_code == 200:
            return r.json().get("seller_id")
    except:
        pass
    return None

def obtener_datos_vendedor(seller_id):
    r = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
    if r.status_code == 200:
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
            "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2),
        }
    return None

if st.button("🔍 Comparar vendedores"):
    resultados = []
    errores = []

    for url in links:
        item_id = extraer_item_id(url)
        if not item_id:
            errores.append(f"❌ No se pudo extraer item_id de: {url}")
            continue

        seller_id = obtener_seller_id(item_id)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id del item: {url}")
            continue

        datos = obtener_datos_vendedor(seller_id)
        if datos:
            resultados.append(datos)
        else:
            errores.append(f"❌ No se pudo obtener datos del vendedor para: {url}")

    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(f"- {err}")

    if resultados:
        st.markdown("## 📊 Comparativa de Vendedores")
        df = pd.DataFrame(resultados)
        st.dataframe(df)

        # Gráfico
        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas totales"], color='orange')
        ax.set_ylabel("Ventas totales")
        ax.set_xticklabels(df["Vendedor"], rotation=45, ha="right")
        st.pyplot(fig)

