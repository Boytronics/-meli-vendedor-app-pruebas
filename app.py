import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import collections
import string

st.set_page_config(page_title="Perfil de Vendedor - Mercado Libre", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")
st.write("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")

links_input = st.text_area("Pega los enlaces:", height=250)
procesar_btn = st.button("🔍 Comparar vendedores")

def obtener_seller_id(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True)
        r.raise_for_status()
        final_url = r.url
        match = re.search(r"/MLM(\d+)", final_url)
        real_id = f"MLM{match.group(1)}" if match else None
        if real_id:
            api_url = f"https://api.mercadolibre.com/items/{real_id}"
            response = requests.get(api_url)
            if response.status_code == 200:
                return response.json().get("seller_id")
        soup = BeautifulSoup(r.text, "html.parser")
        for tag in soup.find_all("script"):
            if tag.string and "seller_id" in tag.string:
                match = re.search(r'"seller_id":\s*(\d+)', tag.string)
                if match:
                    return match.group(1)
    except:
        return None
    return None

def obtener_datos_vendedor(seller_id):
    return requests.get(f"https://api.mercadolibre.com/users/{seller_id}").json()

def texto_personalizado(label, valor):
    st.markdown(f"""
    <div style='font-size:18px; color:white; margin-bottom:4px;'>
        {label}
        <span style='color:#00FF00; font-family:monospace; font-size:22px;'> {valor}</span>
    </div>
    """, unsafe_allow_html=True)

def mostrar_datos(datos, seller_id):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Datos básicos")
        texto_personalizado("👤 Nickname:", datos.get("nickname", "N/A"))
        if datos.get("registration_date"):
            texto_personalizado("🗓️ Registro:", datos["registration_date"][:10])
        texto_personalizado("🌎 País:", datos.get("country_id", ""))
        if "address" in datos:
            texto_personalizado("📍 Estado/Ciudad:",
                f"{datos['address'].get('state', '')} / {datos['address'].get('city', '')}")
        if "points" in datos:
            texto_personalizado("🏆 Puntos:", datos["points"])
        if "status" in datos:
            texto_personalizado("🟢 Estado cuenta:", datos["status"].get("site_status", "N/A"))
        st.markdown(f"<a href='https://www.mercadolibre.com.mx/perfil/{datos.get('nickname')}' target='_blank'>🔗 Ver perfil</a>", unsafe_allow_html=True)
        if datos.get("eshop"):
            texto_personalizado("🏪 Tiene E-Shop:", "✅ Sí")
            texto_personalizado("🛍️ Nombre E-Shop:", datos["eshop"].get("nick_name"))
            logo = datos["eshop"].get("eshop_logo_url")
            if logo:
                st.image(logo, width=100)

    with col2:
        rep = datos.get("seller_reputation", {})
        if rep:
            st.subheader("📈 Reputación y desempeño")
            if rep.get("level_id"):
                texto_personalizado("🏅 Nivel reputación:", rep["level_id"])
            if rep.get("power_seller_status"):
                texto_personalizado("💼 MercadoLíder:", rep["power_seller_status"])
            trans = rep.get("transactions", {})
            if trans:
                if trans.get("total"): texto_personalizado("📦 Ventas totales:", trans["total"])
                if trans.get("completed"): texto_personalizado("✅ Completadas:", trans["completed"])
                if trans.get("canceled"): texto_personalizado("❌ Canceladas:", trans["canceled"])
                ratings = trans.get("ratings", {})
                if ratings:
                    if ratings.get("positive") is not None:
                        texto_personalizado("👍 Positivas:", f"{round(ratings['positive']*100, 2)}%")
                    if ratings.get("neutral") is not None:
                        texto_personalizado("😐 Neutrales:", f"{round(ratings['neutral']*100, 2)}%")
                    if ratings.get("negative") is not None:
                        texto_personalizado("👎 Negativas:", f"{round(ratings['negative']*100, 2)}%")

if procesar_btn and links_input:
    urls = [line.strip() for line in links_input.splitlines() if line.strip()]
    for url in urls[:10]:
        seller_id = obtener_seller_id(url)
        if seller_id:
            datos = obtener_datos_vendedor(seller_id)
            st.success(f"✅ Vendedor encontrado para link:
{url}")
            mostrar_datos(datos, seller_id)
        else:
            st.error(f"❌ No se pudo obtener el seller_id del producto:
{url}")
