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

def obtener_promos(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}/classifieds_promotion_data"
    return requests.get(url).json()

def texto_personalizado(label, valor):
    st.markdown(f"""
    <div style='font-size:18px; color:white; margin-bottom:4px;'>
        {label}
        <span style='color:#00FF00; font-family:monospace; font-size:22px;'> {valor}</span>
    </div>
    """, unsafe_allow_html=True)

def obtener_datos_por_seller(seller):
    try:
        user = None
        if seller.isdigit():
            user = requests.get(f"https://api.mercadolibre.com/users/{seller}").json()
        else:
            r = requests.get(f"https://api.mercadolibre.com/users/search?nickname={seller}").json()
            if r and r.get("seller", {}).get("id"):
                user = requests.get(f"https://api.mercadolibre.com/users/{r['seller']['id']}").json()
        if not user:
            return None

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

    for linea in líneas[:10]:
        resultado = obtener_datos_por_seller(linea)
        if resultado:
            datos.append(resultado)

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
    else:
        st.warning("No se pudo obtener información de los vendedores ingresados.")
