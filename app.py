import streamlit as st
import requests
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Perfil de Vendedor - Mercado Libre", layout="wide")
st.title("🔍 Perfil Completo del Vendedor en Mercado Libre")
st.write("Pega la URL de un producto para ver toda la información del vendedor.")

url_producto = st.text_input("URL del producto de Mercado Libre")

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
        vendedor_tag = soup.find("a", href=lambda h: h and "/perfil/" in h)
        if vendedor_tag:
            return vendedor_tag['href'].split("/perfil/")[-1]
        for tag in soup.find_all("script"):
            if tag.string and "seller_id" in tag.string:
                match = re.search(r'"seller_id":\s*(\d+)', tag.string)
                if match:
                    return match.group(1)
    except Exception as e:
        st.error(f"Error accediendo a la URL: {e}")
    return None

def obtener_datos_vendedor(seller_id):
    try:
        url = f"https://api.mercadolibre.com/users/{seller_id}"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Error al obtener los datos del vendedor: {e}")
        return None

def texto_personalizado(label, valor):
    st.markdown(f"""
    <div style='font-size:18px; color:white; margin-bottom:4px;'>
        {label}
        <span style='color:#00FF00; font-family:monospace; font-size:22px;'> {valor}</span>
    </div>
    """, unsafe_allow_html=True)

def mostrar_datos(datos):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Datos básicos")
        texto_personalizado("👤 Nickname:", datos.get("nickname", "N/A"))
        fecha = datos.get("registration_date", "")
        texto_personalizado("🗓️ Registro:", fecha[:10] if fecha else "No disponible")
        texto_personalizado("🌎 País:", datos.get("country_id", ""))
        texto_personalizado("📍 Estado/Ciudad:",
                     f"{datos.get('address', {}).get('state', '')} / {datos.get('address', {}).get('city', '')}")
        st.markdown(f"<a href='https://www.mercadolibre.com.mx/perfil/{datos.get('nickname')}' target='_blank'>🔗 Ver perfil</a>", unsafe_allow_html=True)

        if datos.get("eshop"):
            texto_personalizado("🏪 Tiene E-Shop:", "✅ Sí")
            texto_personalizado("🛍️ Nombre E-Shop:", datos["eshop"].get("nick_name"))
            logo = datos["eshop"].get("eshop_logo_url")
            if logo:
                st.image(logo, width=100)
        else:
            texto_personalizado("🏪 Tiene E-Shop:", "❌ No")

    with col2:
        st.subheader("📈 Reputación y desempeño")
        rep = datos.get("seller_reputation", {})
        texto_personalizado("🏅 Nivel reputación:", rep.get("level_id", "N/A"))
        texto_personalizado("💼 MercadoLíder:", rep.get("power_seller_status", "N/A"))

        trans = rep.get("transactions", {})
        texto_personalizado("📦 Ventas totales:", trans.get("total", 0))
        texto_personalizado("✅ Completadas:", trans.get("completed", 0))
        texto_personalizado("❌ Canceladas:", trans.get("canceled", 0))

        ratings = trans.get("ratings", {})
        texto_personalizado("👍 Positivas:", f"{round(ratings.get('positive', 0) * 100, 2)}%" if ratings else "No disponible")
        texto_personalizado("😐 Neutrales:", f"{round(ratings.get('neutral', 0) * 100, 2)}%" if ratings else "No disponible")
        texto_personalizado("👎 Negativas:", f"{round(ratings.get('negative', 0) * 100, 2)}%" if ratings else "No disponible")

        metrics = rep.get("metrics", {})
        if metrics:
            st.markdown("<h5 style='margin-top:20px; color:white;'>📊 Últimos 60 días:</h5>", unsafe_allow_html=True)
            texto_personalizado("🕒 Ventas completadas:", metrics.get("sales", {}).get("completed", 0))
            texto_personalizado("🛑 Reclamos:", f"{round(metrics.get('claims', {}).get('rate', 0) * 100, 2)}%")
            texto_personalizado("⏳ Demoras:", f"{round(metrics.get('delayed_handling_time', {}).get('rate', 0) * 100, 2)}%")
            texto_personalizado("❌ Cancelaciones:", f"{round(metrics.get('cancellations', {}).get('rate', 0) * 100, 2)}%")

# Ejecución principal
if url_producto:
    seller_id = obtener_seller_id(url_producto)
    if seller_id:
        datos = obtener_datos_vendedor(seller_id)
        if datos:
            st.success("✅ Vendedor encontrado")
            mostrar_datos(datos)
        else:
            st.warning("No se pudo obtener la información del vendedor.")
    else:
        st.warning("No se encontró el vendedor.")
