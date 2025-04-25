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

def mostrar_productos_desde_ids(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}/items/search?status=active&limit=50"
    res = requests.get(url).json()
    ids = res.get("results", [])
    if not ids:
        st.info("Este vendedor no tiene productos activos visibles.")
        return
    productos = []
    for pid in ids:
        try:
            item = requests.get(f"https://api.mercadolibre.com/items/{pid}").json()
            productos.append({
                "Título": item.get("title", ""),
                "Precio": item.get("price", 0),
                "Stock": item.get("available_quantity", 0),
                "Link": f"[Ver producto]({item.get('permalink', '')})"
            })
        except:
            continue
    if productos:
        st.subheader("🛒 Productos activos (por ID)")
        df = pd.DataFrame(productos)
        st.write(df.to_html(escape=False, index=False), unsafe_allow_html=True)

def analizar_productos_activos(seller_id):
    url = f"https://api.mercadolibre.com/users/{seller_id}/items/search?status=active&limit=50"
    res = requests.get(url).json()
    ids = res.get("results", [])
    if not ids:
        return
    productos = []
    for pid in ids:
        try:
            item = requests.get(f"https://api.mercadolibre.com/items/{pid}").json()
            productos.append({
                "id": pid,
                "title": item.get("title", ""),
                "price": item.get("price", 0),
                "stock": item.get("available_quantity", 0),
                "category_id": item.get("category_id", ""),
                "shipping": item.get("shipping", {}).get("free_shipping", False)
            })
        except:
            continue
    if not productos:
        return
    st.subheader("📊 Análisis general del catálogo")
    all_words = []
    for p in productos:
        title = p["title"].lower()
        title = title.translate(str.maketrans('', '', string.punctuation))
        words = title.split()
        all_words.extend([w for w in words if len(w) > 3])
    comunes = collections.Counter(all_words).most_common(10)
    st.write(pd.DataFrame(comunes, columns=["Palabra", "Repeticiones"]))

    st.markdown("#### 💰 Estadísticas de precios y stock")
    precios = [p["price"] for p in productos]
    stocks = [p["stock"] for p in productos]
    resumen = pd.DataFrame({
        "Promedio": [round(sum(precios)/len(precios), 2), round(sum(stocks)/len(stocks), 2)],
        "Mínimo": [min(precios), min(stocks)],
        "Máximo": [max(precios), max(stocks)]
    }, index=["Precio", "Stock"])
    st.table(resumen)

    st.markdown("#### 🏷️ Categorías más usadas")
    cats = collections.Counter([p["category_id"] for p in productos]).most_common(5)
    st.write(pd.DataFrame(cats, columns=["Categoría ID", "Cantidad"]))

    st.markdown("#### 🚨 Productos con stock ≤ 5")
    bajos = [p for p in productos if p["stock"] <= 5]
    if bajos:
        st.write(pd.DataFrame([{
            "Título": b["title"],
            "Stock": b["stock"],
            "Precio": b["price"]
        } for b in bajos]))
    else:
        st.success("🎉 No hay productos con stock bajo.")

# EJECUCIÓN PRINCIPAL
#if url_producto:
 #   seller_id = obtener_seller_id(url_producto)
    if seller_id:
        datos = obtener_datos_vendedor(seller_id)
        promos = obtener_promos(seller_id)
        st.success("✅ Vendedor encontrado")
        mostrar_datos(datos, seller_id)
        mostrar_productos_desde_ids(seller_id)
        analizar_productos_activos(seller_id)
        if promos.get("available"):
            st.subheader("💸 Promociones pagadas")
            st.markdown("✅ Este vendedor **usa promociones pagadas** en sus publicaciones.")
