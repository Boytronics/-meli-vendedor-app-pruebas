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
consultar_btn = st.button("🔍 Consultar vendedor")

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
    return requests.get(f"https://api.mercadolibre.com/users/{seller_id}").json()

def obtener_total_productos_activos(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}/items/search?status=active"
    res = requests.get(url).json()
    return res.get("paging", {}).get("total", 0)

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
        total_activos = obtener_total_productos_activos(seller_id)
        texto_personalizado("🛒 Productos activos:", total_activos)
        st.markdown(f"<a href='https://www.mercadolibre.com.mx/perfil/{datos.get('nickname')}' target='_blank'>🔗 Ver perfil</a>", unsafe_allow_html=True)

    with col2:
        rep = datos.get("seller_reputation", {})
        st.subheader("📈 Reputación y desempeño")
        if rep.get("level_id"):
            texto_personalizado("🏅 Nivel reputación:", rep["level_id"])
        if rep.get("power_seller_status"):
            texto_personalizado("💼 MercadoLíder:", rep["power_seller_status"])
        trans = rep.get("transactions", {})
        if trans.get("total"):
            texto_personalizado("📦 Ventas totales:", trans["total"])
        if trans.get("completed"):
            texto_personalizado("✅ Completadas:", trans["completed"])
        if trans.get("canceled"):
            texto_personalizado("❌ Canceladas:", trans["canceled"])
        ratings = trans.get("ratings", {})
        if ratings.get("positive") is not None:
            texto_personalizado("👍 Positivas:", f"{round(ratings['positive'] * 100, 2)}%")
        if ratings.get("neutral") is not None:
            texto_personalizado("😐 Neutrales:", f"{round(ratings['neutral'] * 100, 2)}%")
        if ratings.get("negative") is not None:
            texto_personalizado("👎 Negativas:", f"{round(ratings['negative'] * 100, 2)}%")

def obtener_datos_por_seller(nickname):
    try:
        # Buscar el seller_id desde perfil público
        search_url = f"https://www.mercadolibre.com.mx/perfil/{nickname}"
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(search_url, headers=headers)

        match = re.search(r'"user_id":"?(\d+)"?', r.text)
        if not match:
            return None
        seller_id = match.group(1)

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
            "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
            "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
            "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
        }
    except:
        return None

if url_producto and consultar_btn:
    seller_id = obtener_seller_id(url_producto)
    if seller_id:
        datos = obtener_datos_vendedor(seller_id)
        st.success("✅ Vendedor encontrado")
        mostrar_datos(datos, seller_id)

st.markdown("---")
st.header("📊 Comparador de Vendedores")

input_vendedores = st.text_area("Pega hasta 10 *nicknames* o *seller_id* (uno por línea):", height=200)
comparar_btn = st.button("🔍 Comparar vendedores")

if comparar_btn and input_vendedores:
    líneas = [x.strip() for x in input_vendedores.splitlines() if x.strip()]
    datos = []
    no_encontrados = []

    for linea in líneas[:10]:
        resultado = obtener_datos_por_seller(linea)
        if resultado:
            datos.append(resultado)
        else:
            no_encontrados.append(f"❌ {linea}")

    if datos:
        df = pd.DataFrame(datos)
        st.subheader("📋 Tabla comparativa")
        st.dataframe(df)

        st.subheader("📊 Gráfico: Total de Ventas por Vendedor")
        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas"], color='orange')
        ax.set_ylabel("Ventas totales")
        ax.set_xticklabels(df["Vendedor"], rotation=45, ha="right")
        st.pyplot(fig)

    if no_encontrados:
        st.warning("No se pudo obtener información de los siguientes vendedores:")
        st.markdown("<br>".join(no_encontrados), unsafe_allow_html=True)

