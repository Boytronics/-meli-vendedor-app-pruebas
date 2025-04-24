import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt

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
        return requests.get(f"https://api.mercadolibre.com/users/{seller_id}").json()
    except:
        return {}

def obtener_productos(seller_id):
    url = f"https://api.mercadolibre.com/sites/MLM/search?seller_id={seller_id}&limit=100"
    return requests.get(url).json().get("results", [])

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

def mostrar_datos(datos):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📄 Datos básicos")
        texto_personalizado("👤 Nickname:", datos.get("nickname", "N/A"))
        texto_personalizado("🗓️ Registro:", datos.get("registration_date", "")[:10])
        texto_personalizado("🌎 País:", datos.get("country_id", ""))
        texto_personalizado("📍 Estado/Ciudad:", f"{datos.get('address', {}).get('state', '')} / {datos.get('address', {}).get('city', '')}")
        texto_personalizado("🏆 Puntos:", datos.get("points", "N/D"))
        texto_personalizado("🟢 Estado cuenta:", datos.get("status", {}).get("site_status", "Desconocido"))
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
        trans = rep.get("transactions", {})
        ratings = trans.get("ratings", {})
        texto_personalizado("🏅 Nivel reputación:", rep.get("level_id", "N/A"))
        texto_personalizado("💼 MercadoLíder:", rep.get("power_seller_status", "N/A"))
        texto_personalizado("📦 Ventas totales:", trans.get("total", 0))
        texto_personalizado("✅ Completadas:", trans.get("completed", 0))
        texto_personalizado("❌ Canceladas:", trans.get("canceled", 0))
        texto_personalizado("👍 Positivas:", f"{round(ratings.get('positive', 0)*100, 2)}%" if ratings else "N/A")
        texto_personalizado("😐 Neutrales:", f"{round(ratings.get('neutral', 0)*100, 2)}%" if ratings else "N/A")
        texto_personalizado("👎 Negativas:", f"{round(ratings.get('negative', 0)*100, 2)}%" if ratings else "N/A")

        st.markdown("#### 📊 Métricas últimas 60 días:")
        metrics = rep.get("metrics", {})
        texto_personalizado("🛑 Reclamos:", f"{round(metrics.get('claims', {}).get('rate', 0)*100, 2)}%")
        texto_personalizado("⏳ Demoras:", f"{round(metrics.get('delayed_handling_time', {}).get('rate', 0)*100, 2)}%")
        texto_personalizado("❌ Cancelaciones:", f"{round(metrics.get('cancellations', {}).get('rate', 0)*100, 2)}%")

        # Gráfico de barras
        st.markdown("##### 📉 Gráfico:")
        fig, ax = plt.subplots()
        labels = ['Reclamos', 'Demoras', 'Cancelaciones']
        valores = [
            metrics.get("claims", {}).get("rate", 0) * 100,
            metrics.get("delayed_handling_time", {}).get("rate", 0) * 100,
            metrics.get("cancellations", {}).get("rate", 0) * 100
        ]
        ax.bar(labels, valores, color='limegreen')
        ax.set_ylabel('%')
        ax.set_ylim(0, 100)
        st.pyplot(fig)

def mostrar_productos(productos):
    st.subheader("🛒 Productos Activos")
    if not productos:
        st.write("Este vendedor no tiene productos activos.")
        return

    df = pd.DataFrame([{
        "Título": p["title"],
        "Precio": p["price"],
        "Stock": p.get("available_quantity", 0),
        "Categoría": p["category_id"],
        "Link": p["permalink"]
    } for p in productos])

    st.dataframe(df)

    st.markdown("#### 💰 Productos extremos")
    st.write("Más barato:", df.sort_values("Precio").head(1))
    st.write("Más caro:", df.sort_values("Precio", ascending=False).head(1))

    st.markdown("#### 🏷️ Categorías más comunes")
    cat_counts = df["Categoría"].value_counts().head(5)
    st.write(cat_counts)

# 🔄 EJECUCIÓN
if url_producto:
    seller_id = obtener_seller_id(url_producto)
    if seller_id:
        datos = obtener_datos_vendedor(seller_id)
        productos = obtener_productos(seller_id)
        promos = obtener_promos(seller_id)
        st.success("✅ Vendedor encontrado")
        mostrar_datos(datos)
        mostrar_productos(productos)
        st.subheader("💸 Promociones pagadas")
        if promos.get("available"):
            st.markdown("✅ Este vendedor **usa promociones pagadas** en sus publicaciones.")
        else:
            st.markdown("❌ Este vendedor **no está usando promociones pagadas**.")
    else:
        st.warning("No se encontró el vendedor.")
