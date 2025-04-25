
import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import collections
import string

st.set_page_config(page_title="Análisis de Vendedores", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")
input_links = st.text_area("Links de productos", height=200)
boton = st.button("🔍 Comparar vendedores")

def obtener_seller_id(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        r.raise_for_status()
        final_url = r.url
        match = re.search(r"/MLM(\d+)", final_url)
        if match:
            product_id = f"MLM{match.group(1)}"
            item_data = requests.get(f"https://api.mercadolibre.com/items/{product_id}").json()
            return item_data.get("seller_id")
    except:
        return None

def obtener_datos_vendedor(seller_id):
    try:
        r = requests.get(f"https://api.mercadolibre.com/users/{seller_id}", timeout=10)
        return r.json()
    except:
        return {}

def mostrar_datos(datos, seller_id, link):
    st.success(f"✅ Vendedor encontrado para link: {link}")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Datos básicos")
        st.markdown(f"**👤 Nickname:** {datos.get('nickname', 'N/A')}")
        st.markdown(f"**🌎 País:** {datos.get('country_id', '')}")
        if "address" in datos:
            st.markdown(f"**📍 Estado/Ciudad:** {datos['address'].get('state', '')} / {datos['address'].get('city', '')}")
        st.markdown(f"**🟢 Estado cuenta:** {datos.get('status', {}).get('site_status', '')}")
        st.markdown(f"[🔗 Ver perfil](https://www.mercadolibre.com.mx/perfil/{datos.get('nickname', '')})")

    with col2:
        rep = datos.get("seller_reputation", {})
        st.subheader("📈 Reputación y desempeño")
        st.markdown(f"**🏅 Nivel reputación:** {rep.get('level_id', 'N/A')}")
        st.markdown(f"**💼 MercadoLíder:** {rep.get('power_seller_status', 'N/A')}")
        trans = rep.get("transactions", {})
        if trans:
            st.markdown(f"**📦 Ventas totales:** {trans.get('total', 0)}")
            st.markdown(f"**✅ Completadas:** {trans.get('completed', 0)}")
            st.markdown(f"**❌ Canceladas:** {trans.get('canceled', 0)}")

if boton and input_links:
    links = [line.strip() for line in input_links.splitlines() if line.strip()]
    for link in links[:10]:
        seller_id = obtener_seller_id(link)
        if seller_id:
            datos = obtener_datos_vendedor(seller_id)
            mostrar_datos(datos, seller_id, link)
        else:
            st.error(f"❌ No se pudo extraer seller_id de: {link}")
