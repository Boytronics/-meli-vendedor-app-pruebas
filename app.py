import streamlit as st
import requests
import re
from bs4 import BeautifulSoup

st.set_page_config(page_title="Perfil de Vendedor - Mercado Libre")
st.title("🔍 Buscar perfil del vendedor en Mercado Libre")
st.write("Pega la URL del producto y abre el perfil del vendedor.")

url_producto = st.text_input("URL del producto de Mercado Libre")

def obtener_seller_id(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        # Paso 1: redireccionar a la URL final
        r = requests.get(url, headers=headers, allow_redirects=True)
        r.raise_for_status()
        final_url = r.url

        # Paso 2: intentar extraer ID tipo MLM123456789
        match = re.search(r"/MLM(\d+)", final_url)
        real_id = f"MLM{match.group(1)}" if match else None

        # Paso 3: intentar por API
        if real_id:
            api_url = f"https://api.mercadolibre.com/items/{real_id}"
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                return data.get("seller_id", None)

        # Paso 4: fallback — rascar del HTML
        soup = BeautifulSoup(r.text, "html.parser")
        vendedor_tag = soup.find("a", href=lambda h: h and "/perfil/" in h)
        if vendedor_tag:
            return vendedor_tag['href'].split("/perfil/")[-1]

        # Paso 5: buscar en los scripts
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

def obtener_nombre_vendedor(seller_id):
    try:
        url = f"https://api.mercadolibre.com/users/{seller_id}"
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        return data.get("nickname", str(seller_id))
    except:
        return str(seller_id)

# Ejecución
if url_producto:
    seller_id = obtener_seller_id(url_producto)
    if seller_id:
        nickname = obtener_nombre_vendedor(seller_id)
        perfil_url = f"https://www.mercadolibre.com.mx/perfil/{nickname}"
        st.success(f"Vendedor encontrado: **{nickname}**")
        st.markdown(f"[🔗 Ver perfil del vendedor]({perfil_url})", unsafe_allow_html=True)
    else:
        st.warning("No se encontró el vendedor.")
