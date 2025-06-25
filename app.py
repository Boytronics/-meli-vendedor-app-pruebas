
import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
import collections
import string

st.set_page_config(page_title="Perfil de Vendedor - Mercado Libre", layout="wide")
st.title("🔍 Perfil Completo del Vendedor en Mercado Libre")
st.write("Pega la URL de un producto para ver toda la información del vendedor.")

url_producto = st.text_input("URL del producto de Mercado Libre")

def obtener_seller_id(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        r.raise_for_status()
        final_url = r.url
        match = re.search(r"/MLM(\d+)", final_url)
        real_id = f"MLM{match.group(1)}" if match else None
        if real_id:
            api_url = f"https://api.mercadolibre.com/items/{real_id}"
            response = requests.get(api_url, timeout=10)
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
    r = requests.get(f"https://api.mercadolibre.com/users/{seller_id}", timeout=10)
    return r.json() if r.status_code == 200 else {}

def obtener_total_productos_activos(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}/items/search?status=active&limit=0"
    res = requests.get(url, timeout=10).json()
    return res.get("paging", {}).get("total", 0)

def obtener_promos(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}/classifieds_promotion_data"
    return requests.get(url, timeout=10).json()

def texto_personalizado(label, valor):
    st.markdown(f'''
    <div style="font-size:18px; color:white; margin-bottom:4px;">
        {label}
        <span style="color:#00FF00; font-family:monospace; font-size:22px;"> {valor}</span>
    </div>
    ''', unsafe_allow_html=True)

def mostrar_datos(datos, seller_id):
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📄 Datos básicos")
        texto_personalizado("👤 Nickname:", datos.get("nickname", "N/A"))
        if datos.get("registration_date"):
            texto_personalizado("🗓️ Registro:", datos["registration_date"][:10])
        texto_personalizado("🌎 País:", datos.get("country_id", ""))
        if isinstance(datos.get("address"), dict):
            texto_personalizado("📍 Estado/Ciudad:",
                f"{datos['address'].get('state', '')} / {datos['address'].get('city', '')}")
        if "points" in datos:
            texto_personalizado("🏆 Puntos:", datos["points"])
        # ---- FIX HERE ----
        estado_dict = datos.get("status") or {}
        texto_personalizado("🟢 Estado cuenta:", estado_dict.get("site_status", "N/A"))
        # ------------------
        total_activos = obtener_total_productos_activos(seller_id)
        if total_activos:
            texto_personalizado("🛒 Productos activos:", total_activos)
        st.markdown(f"<a href='https://www.mercadolibre.com.mx/perfil/{datos.get('nickname')}' target='_blank'>🔗 Ver perfil</a>", unsafe_allow_html=True)
        if datos.get("eshop"):
            texto_personalizado("🏪 Tiene E-Shop:", "✅ Sí")
            texto_personalizado("🛍️ Nombre E-Shop:", datos["eshop"].get("nick_name"))
            logo = datos["eshop"].get("eshop_logo_url")
            if logo:
                st.image(logo, width=100)

    with col2:
        rep = datos.get("seller_reputation", {}) or {}
        st.subheader("📈 Reputación y desempeño")
        texto_personalizado("🏅 Nivel reputación:", rep.get("level_id", "N/A"))
        texto_personalizado("💼 MercadoLíder:", rep.get("power_seller_status", "N/A"))
        trans = rep.get("transactions", {}) or {}
        texto_personalizado("📦 Ventas totales:", trans.get("total", 0))
        texto_personalizado("✅ Completadas:", trans.get("completed", 0))
        texto_personalizado("❌ Canceladas:", trans.get("canceled", 0))
        ratings = trans.get("ratings", {}) or {}
        texto_personalizado("👍 Positivas:", f"{round(ratings.get('positive',0)*100,2)}%")
        texto_personalizado("😐 Neutrales:", f"{round(ratings.get('neutral',0)*100,2)}%")
        texto_personalizado("👎 Negativas:", f"{round(ratings.get('negative',0)*100,2)}%")
        metrics = rep.get("metrics", {}) or {}
        if metrics:
            st.markdown("#### 📊 Métricas últimas 60 días:")
            if metrics.get("sales", {}).get("completed"):
                texto_personalizado("📈 Ventas en 60 días:", metrics["sales"]["completed"])
            tasas = {
                "🛑 Reclamos": metrics.get("claims", {}).get("rate", 0),
                "⏳ Demoras": metrics.get("delayed_handling_time", {}).get("rate", 0),
                "❌ Cancelaciones": metrics.get("cancellations", {}).get("rate", 0)
            }
            if any(tasas.values()):
                fig, ax = plt.subplots()
                ax.bar(tasas.keys(), [v*100 for v in tasas.values()], color='limegreen')
                ax.set_ylabel('%')
                ax.set_ylim(0, 100)
                st.pyplot(fig)
