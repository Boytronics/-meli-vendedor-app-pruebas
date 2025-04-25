
import streamlit as st
import requests
import re
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Comparador de Vendedores desde Links de Productos", layout="wide")
st.title("🔍 Comparador de Vendedores desde Links de Productos")

st.markdown("Pega hasta 10 enlaces de productos de Mercado Libre (uno por línea):")
links_input = st.text_area("Links de productos", height=200)

if st.button("🔍 Comparar vendedores"):
    urls = [url.strip() for url in links_input.splitlines() if url.strip()]
    data = []
    errores = []

    def extraer_seller_id(url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
            r.raise_for_status()
            m = re.search(r'"seller_id":(\d+)', r.text)
            if m:
                return m.group(1)
        except:
            return None
        return None

    for url in urls[:10]:
        seller_id = extraer_seller_id(url)
        if not seller_id:
            errores.append(f"❌ No se pudo extraer seller_id de: [{url}]({url})")
            continue

        try:
            r = requests.get(f"https://api.mercadolibre.com/users/{seller_id}")
            if r.status_code != 200:
                errores.append(f"❌ No se pudo obtener datos del seller_id `{seller_id}` desde: [{url}]({url})")
                continue

            user = r.json()
            rep = user.get("seller_reputation", {})
            trans = rep.get("transactions", {})
            metrics = rep.get("metrics", {})

            data.append({
                "Vendedor": user.get("nickname"),
                "Reputación": rep.get("level_id", "N/A"),
                "MercadoLíder": rep.get("power_seller_status", "N/A"),
                "Ventas totales": trans.get("total", 0),
                "Reclamos": round(metrics.get("claims", {}).get("rate", 0) * 100, 2),
                "Demoras": round(metrics.get("delayed_handling_time", {}).get("rate", 0) * 100, 2),
                "Cancelaciones": round(metrics.get("cancellations", {}).get("rate", 0) * 100, 2)
            })

        except Exception as e:
            errores.append(f"❌ Error procesando {url}: {e}")

    if errores:
        st.error("Se encontraron errores:")
        for err in errores:
            st.markdown(err)

    if data:
        df = pd.DataFrame(data)
        st.subheader("📋 Comparativa de Vendedores")
        st.dataframe(df)

        st.subheader("📊 Gráfico de Ventas Totales")
        fig, ax = plt.subplots()
        ax.bar(df["Vendedor"], df["Ventas totales"], color='orange')
        ax.set_ylabel("Ventas")
        ax.set_xticklabels(df["Vendedor"], rotation=45, ha="right")
        st.pyplot(fig)
