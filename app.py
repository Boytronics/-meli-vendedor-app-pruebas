import streamlit as st
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
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
    return requests.get(f"https://api.mercadolibre.com/users/{seller_id}").json()

def obtener_productos(seller_id):
    url = f"https://api.mercadolibre.com/sites/MLM/search?seller_id={seller_id}&limit=100"
    return requests.get(url).json().get("results", [])

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

            metrics = rep.get("metrics", {})
            if metrics:
                st.markdown("#### 📊 Métricas últimas 60 días:")
                if metrics.get("sales", {}).get("completed"):
                    texto_personalizado("📈 Ventas en 60 días:", metrics["sales"]["completed"])
                tasas = {
                    "🛑 Reclamos": metrics.get("claims", {}).get("rate", 0),
                    "⏳ Demoras": metrics.get("delayed_handling_time", {}).get("rate", 0),
                    "❌ Cancelaciones": metrics.get("cancellations", {}).get("rate", 0)
                }
                for k, v in tasas.items():
                    if v > 0:
                        texto_personalizado(k + ":", f"{round(v * 100, 2)}%")

                if any(v > 0 for v in tasas.values()):
                    st.markdown("##### 📉 Gráfico:")
                    fig, ax = plt.subplots()
                    ax.bar(tasas.keys(), [v * 100 for v in tasas.values()], color='limegreen')
                    ax.set_ylabel('%')
                    ax.set_ylim(0, 100)
                    st.pyplot(fig)

def mostrar_productos(productos):
    if not productos:
        return
    st.subheader("🛒 Productos Activos")
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
    st.write(df["Categoría"].value_counts().head(5))

# 🔄 EJECUCIÓN
if url_producto:
    seller_id = obtener_seller_id(url_producto)
    if seller_id:
        datos = obtener_datos_vendedor(seller_id)
        productos = obtener_productos(seller_id)
        promos = obtener_promos(seller_id)
        st.success("✅ Vendedor encontrado")
        mostrar_datos(datos, seller_id)
        if productos:
            mostrar_productos(productos)
        if promos.get("available"):
            st.subheader("💸 Promociones pagadas")
            st.markdown("✅ Este vendedor **usa promociones pagadas** en sus publicaciones.")
