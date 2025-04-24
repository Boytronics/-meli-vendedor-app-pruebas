import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import json

st.set_page_config(page_title="Perfil completo del vendedor - Mercado Libre")
st.title("🔍 Perfil completo del vendedor en Mercado Libre")
st.write("Pega la URL de un producto para ver todos los datos públicos del vendedor.")

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
                data = response.json()
                return data.get("seller_id")
        soup = BeautifulSoup(r.text, "html.parser")
        vendedor_tag = soup.find("a", href=lambda h: h and "/perfil/" in h)
        if vendedor_tag:
            return vendedor_tag['href'].split("/perfil/")[-1]
        script_tags = soup.find_all("script")
        for tag in script_tags:
            if tag.string and "seller_id" in tag.string:
                match = re.search(r'"seller_id":\s*(\d+)', tag.string)
                if match:
                    return match.group(1)
        return None
    except Exception as e:
        st.error(f"Error accediendo a la URL: {e}")
        return None

def obtener_datos_completos_vendedor(seller_id):
    try:
        url = f"https://api.mercadolibre.com/users/{seller_id}"
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"Error al obtener los datos del vendedor: {e}")
        return None

if url_producto:
    seller_id = obtener_seller_id(url_producto)
    if seller_id:
        datos_vendedor = obtener_datos_completos_vendedor(seller_id)
        if datos_vendedor:
            st.success(f"👤 Vendedor encontrado: **{datos_vendedor.get('nickname', 'Desconocido')}**")
            st.markdown(f"[🔗 Ver perfil del vendedor](https://www.mercadolibre.com.mx/perfil/{datos_vendedor.get('nickname', '')})", unsafe_allow_html=True)
            st.subheader("📄 Datos completos del vendedor:")
            st.json(datos_vendedor)
        else:
            st.warning("No se pudo obtener la información del vendedor.")
    else:
        st.warning("No se encontró el vendedor.")
