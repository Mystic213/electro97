import csv
import os
import unicodedata
import streamlit as st
from datetime import datetime
from twilio.rest import Client

# Ruta al archivo CSV
# Asegúrate de que este archivo esté en el mismo directorio que app_tienda.py
CSV_PATH = "tiendanube-5596407-17488304521762340069.csv"

def normalizar(texto):
    """Normaliza el texto eliminando acentos y convirtiéndolo a mayúsculas."""
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    return texto.upper()

def generar_iniciales(nombre):
    """Genera las iniciales de un nombre de producto."""
    nombre = normalizar(nombre)
    palabras = nombre.strip().split()
    return ''.join([p[0] for p in palabras if p and p[0].isalpha()]).upper()

def cargar_productos_desde_csv(path):
    """Carga los productos desde un archivo CSV."""
    productos = {}
    if not os.path.exists(path):
        st.error(f"Error: El archivo CSV no se encontró en la ruta: {path}")
        return productos
    with open(path, encoding="latin-1", newline='') as csvfile:
        try:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                if not row: # Saltar filas vacías
                    continue
                nombre = row.get("Nombre", "").strip()
                precio = row.get("Precio", "").strip()
                if not nombre or not precio: # Saltar filas sin nombre o precio
                    continue
                iniciales = generar_iniciales(nombre)
                if iniciales not in productos:
                    productos[iniciales] = []
                productos[iniciales].append((nombre, precio))
        except Exception as e:
            st.error(f"Error al leer el archivo CSV: {e}. Asegúrate de que el delimitador es ';' y la codificación es 'latin-1'.")
    return productos

def buscar_por_prefijo(productos, prefijo):
    """Busca productos que comienzan con un prefijo dado."""
    prefijo = normalizar(prefijo)
    resultados = []
    for lista in productos.values():
        for nombre, precio in lista:
            if normalizar(nombre).startswith(prefijo):
                resultados.append((nombre, precio))
    return resultados

def buscar_por_prefijo_o_contenido(productos, texto):
    """Busca productos que contienen el texto dado en su nombre."""
    texto = normalizar(texto)
    resultados = []
    for lista in productos.values():
        for nombre, precio in lista:
            nombre_norm = normalizar(nombre)
            if texto in nombre_norm:
                resultados.append((nombre, precio))
    return resultados

def main():
    """Función principal de la aplicación Streamlit."""
    # --- CONFIGURACIÓN DE PÁGINA (DEBE SER LA PRIMERA LLAMADA DE STREAMLIT) ---
    st.set_page_config(page_title="Tienda IA", page_icon="🛒", layout="wide")

    # --- CONFIGURACIÓN E INICIALIZACIÓN DE TWILIO (AHORA DENTRO DE MAIN) ---
    # Es crucial reemplazar los valores de ejemplo con tus credenciales reales obtenidas de tu cuenta de Twilio.
    # ADVERTENCIA: Incluir estas credenciales directamente en el código de Streamlit no es seguro para aplicaciones públicas.
    # Para aplicaciones desplegadas, se recomienda usar variables de entorno o un backend separado (como Flask).
    TWILIO_ACCOUNT_SID = "AC3a9ca0321d899d0c606d72299f6b6357"
    TWILIO_AUTH_TOKEN = "d9b615d87dd91dbabab82bc572aa0104"
    TWILIO_WHATSAPP_NUMBER = "whatsapp:+14155238886"  # WhatsApp Sandbox de Twilio
    RECIPIENT_WHATSAPP_NUMBER = "whatsapp:+5491133702819" # Número destino (cliente/local)

    # Inicializa el cliente de Twilio solo una vez y solo si no existe ya (para evitar problemas de recarga en Streamlit)
    if "twilio_client" not in st.session_state:
        try:
            st.session_state.twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        except Exception as e:
            st.error(f"ERROR: No se pudo inicializar el cliente de Twilio. Revisa tus credenciales. Error: {e}")
            st.session_state.twilio_client = None
    twilio_client = st.session_state.twilio_client


    # --- Estilos CSS y animaciones ---
    st.markdown("""
        <style>
        body, .stApp {
            background: linear-gradient(120deg, #f9f6f2 0%, #f6ede7 100%) !important;
            color: #7d5c3a !important;
            transition: background 0.7s;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(120deg, #f7e7d7 0%, #f9f6f2 100%); !important;
            border-right: 2px solid #ecd9c6;
            transition: background 0.7s;
        }
        .central-card {
            background: linear-gradient(120deg, #fdf8f4 60%, #f7e7d7 100%);
            border-radius: 32px;
            box-shadow: 0 8px 32px #ecd9c6aa;
            padding: 2.7rem 2.7rem 1.7rem 2.7rem;
            margin: 2.7rem auto;
            max-width: 900px;
            border: 2.5px solid #ecd9c6;
            transition: box-shadow 0.3s, border 0.3s;
            animation: fadein 1.2s;
        }
        @keyframes fadein {
            from { opacity: 0; transform: translateY(30px);}
            to { opacity: 1; transform: translateY(0);}
        }
        .carrito-box {
            background: linear-gradient(90deg, #f9f3ea 60%, #fdf8f4 100%);
            border-radius: 26px;
            padding: 1.7rem 2.2rem;
            box-shadow: 0 4px 18px #ecd9c6aa;
            margin-bottom: 1.7rem;
            color: #7d5c3a;
            border: 2px solid #ecd9c6;
            transition: box-shadow 0.3s, border 0.3s;
        }
        .carrito-row {
            border-bottom: 1.5px dashed #ecd9c6;
            padding-bottom: 0.8rem;
            margin-bottom: 0.8rem;
            font-size: 1.18rem;
            color: #7d5c3a;
            background: linear-gradient(90deg, #fcf7ee 80%, #fdf8f4 100%);
            border-radius: 12px;
            transition: background 0.2s, box-shadow 0.2s;
        }
        .carrito-row:hover {
            background: linear-gradient(90deg, #f7e7d7 80%, #fdf8f4 100%);
            box-shadow: 0 2px 12px #ecd9c6bb;
        }
        .sidebar-product-list {
            max-height: 360px;
            overflow-y: auto;
            background: linear-gradient(120deg, #fcf5ea 60%, #fdf8f4 100%);
            border-radius: 20px;
            box-shadow: 0 4px 18px #ecd9c6bb;
            margin-bottom: 1.2rem;
            padding: 1.2rem 1.5rem;
            color: #a98a6a;
            border: 2px solid #ecd9c6;
        }
        .sidebar-title {
            color: #e6bc8a;
            font-weight: bold;
            font-size: 1.38rem;
            margin-bottom: 1.2rem;
            letter-spacing: 1.7px;
            text-align: center;
            background: linear-gradient(90deg, #fcf7e3 60%, #fdf8f4 100%);
            border-radius: 18px;
            padding: 1.1rem 0;
            box-shadow: 0 2px 14px #ffd6b2cc;
        }
        .sidebar-product-inicial {
            color: #e6bc8a;
            font-weight: bold;
            margin-top: 0.8em;
            margin-bottom: 0.3em;
            font-size: 1.22rem;
            letter-spacing: 2.5px;
            text-shadow: 0 1px 8px #ecd9c6;
        }
        .sidebar-product-nombre {
            color: #fff;
            font-size: 1.12rem;
            margin-left: 1em;
            margin-bottom: 0.13em;
            transition: color 0.12s, font-size 0.12s, transform 0.12s, background 0.12s;
            cursor: pointer;
            text-shadow: 0 1px 8px #e6bc8a, 0 0 2px #7d5c3a;
            border-radius: 8px;
            padding: 4px 14px;
            display: inline-block;
        }
        .sidebar-product-nombre:hover, .sidebar-product-nombre.selected {
            color: #fff;
            font-weight: bold;
            font-size: 1.17rem;
            background: linear-gradient(90deg, #e6d3b3 40%, #ecd9c6 100%);
            border-radius: 12px;
            padding-left: 0.7em;
            text-shadow: 0 0 8px #e6bc8a;
            box-shadow: 0 2px 8px #ecd9c6;
        }
        .producto-row {
            border-bottom: 1px solid #ecd9c6;
            padding-bottom: 0.5rem;
            margin-bottom: 0.5rem;
            font-size: 1.13rem;
            color: #fff;
            text-shadow: 0 1px 8px #e6bc8a, 0 0 2px #7d5c3a;
        }
        .stButton>button {
            background: linear-gradient(90deg, #ecd9c6 0%, #fdf8f4 100%);
            color: #e6bc8a;
            font-weight: bold;
            border-radius: 18px;
            border: 2px solid #ecd9c6;
            padding: 0.8rem 1.7rem;
            font-size: 1.13rem;
            box-shadow: 0 2px 12px #ecd9c6;
            transition: 0.18s, transform 0.18s, box-shadow 0.18s;
            font-family: 'Quicksand', Arial, sans-serif !important;
        }
        .stButton>button:hover {
            background: linear-gradient(90deg, #fdf8f4 0%, #ecd9c6 100%);
            color: #b88b4a;
            border-color: #e6bc8a;
            transform: scale(1.08);
            box-shadow: 0 4px 16px #ecd9c6;
        }
        .stTextInput>div>div>input, .stNumberInput>div>input {
            border-radius: 14px;
            border: 2px solid #ecd9c6;
            font-size: 1.13rem;
            padding: 0.8rem;
            background: #fdf8f4;
            color: #7d5c3a;
            box-shadow: 0 2px 10px #ecd9c6;
        }
        .stTextInput>div>div>input:focus, .stNumberInput>div>input:focus {
            border-color: #e6bc8a;
            box-shadow: 0 4px 18px #ecd9c6;
        }
        .result-card {
            background: linear-gradient(90deg, #f9f3ea 60%, #fdf8f4 100%);
            border-radius: 22px;
            box-shadow: 0 2px 14px #ecd9c6;
            margin-bottom: 1.3rem;
            padding: 1.3rem 1.9rem 1.1rem 1.9rem;
            border: 2px solid #ecd9c6;
            transition: box-shadow 0.2s;
            animation: fadein 1.2s;
        }
        .main-title {
            font-size: 2.9rem;
            font-weight: bold;
            color: #e6bc8a;
            letter-spacing: 2.7px;
            margin-bottom: 1.1rem;
            text-shadow: 0 0 18px #ecd9c6;
            font-family: 'Quicksand', Arial, sans-serif !important;
        }
        .subtitle {
            font-size: 1.28rem;
            color: #b88b4a;
            margin-bottom: 2.2rem;
        }
        .price-soft {
            color: #c9a063 !important;
            font-weight: bold;
            background: #f7e7d7;
            border-radius: 8px;
            padding: 0.2em 0.7em;
            display: inline-block;
            margin-left: 0.3em;
        }
        .total-soft {
            color: #c9a063 !important;
            background: #f7e7d7;
            border-radius: 12px;
            padding: 0.5em 1.2em;
            display: inline-block;
            margin: 0.7em 0;
            font-size: 1.35rem;
            font-weight: bold;
            box-shadow: 0 2px 8px #ecd9c655;
        }
        .no-products-message {
            color: #b08a62;
            font-weight: bold;
            font-size: 1.13rem;
            background: linear-gradient(90deg, #fcf7ee 60%, #fdf8f4 100%);
            border-radius: 14px;
            padding: 1.2em 0.9em;
            margin: 1.3em 0;
            text-align: center;
            box-shadow: 0 2px 10px #ecd9c655;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.8em;
            animation: fadein 1.2s;
        }
        </style>
        <link href="https://fonts.googleapis.com/css2?family=Quicksand:wght@600&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"]  {
            font-family: 'Quicksand', Arial, sans-serif !important;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="main-title">🛒 Tienda Inteligente</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Buscá productos por iniciales o por las primeras letras. Elegí cantidad y armá tu compra.<br><b>¡Fachero, moderno y fácil!</b> 😎</div>', unsafe_allow_html=True)
    st.markdown('<div class="central-card">', unsafe_allow_html=True)

    productos = cargar_productos_desde_csv(CSV_PATH)
    if not productos:
        st.error("No se pudieron cargar productos. Por favor, verifica la ruta y el contenido del archivo CSV.")
        st.markdown('</div>', unsafe_allow_html=True) # Cierra central-card
        return

    if "carrito" not in st.session_state:
        st.session_state.carrito = []

    # --- Barra lateral ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/263/263142.png", width=90)
        st.markdown(
            '<div class="sidebar-title" style="background: linear-gradient(90deg, #fffbe9 60%, #fffaf3 100%); color:#ff9800; font-size:1.28rem; font-weight:bold; letter-spacing:2px; border-radius:14px; padding:0.8rem 0; margin-bottom:1.2rem; box-shadow:0 2px 12px #ffd6b2cc;">🗂️ Lista de productos</div>',
            unsafe_allow_html=True
        )
        filtro_sidebar = st.text_input(
            "Buscar en lista de productos...",
            key="sidebar_search",
            help="Filtra productos por nombre o iniciales"
        )
        mostrar_iniciales = st.checkbox("Mostrar iniciales disponibles", value=True)
        if mostrar_iniciales:
            st.markdown(
                '<div class="sidebar-product-list" style="background: linear-gradient(120deg, #fffbe9 80%, #fffaf3 100%); border: 2.5px solid #ffb366; box-shadow: 0 8px 32px #ffd6b2cc; padding-top:1.2em;">',
                unsafe_allow_html=True
            )
            for ini in sorted(productos.keys()):
                productos_filtrados = [
                    nombre for nombre, _ in productos[ini]
                    if filtro_sidebar.strip() == "" or filtro_sidebar.upper() in normalizar(nombre)
                ]
                if productos_filtrados:
                    st.markdown(
                        f"<div class='sidebar-product-inicial' style='color:#ff9800; font-size:1.22rem; letter-spacing:4px; margin-top:1.2em; margin-bottom:0.4em; text-shadow:0 2px 10px #ffd6b2;'>"
                        f"{ini}</div>",
                        unsafe_allow_html=True
                    )
                    for nombre in productos_filtrados:
                        st.markdown(
                            f"<div class='sidebar-product-nombre' style='background: linear-gradient(90deg, #ffb366 0%, #ffd6b2 100%); color:#fff; font-size:1.12rem; margin-bottom:0.22em; padding:6px 14px; border-radius:9px; display:inline-block; margin-left:1.3em; margin-right:0.2em; box-shadow:0 2px 10px #ffd6b2;'>• {nombre}</div>",
                            unsafe_allow_html=True
                        )
            st.markdown('</div>', unsafe_allow_html=True)
        st.divider()
        st.markdown(
            "<div style='color:#ff9800; font-weight:bold; font-size:1.08rem; margin-bottom:1.2em;'>"
            "¡Explorá, buscá y llevate lo mejor!<br>Hecho por Bruno</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-bottom:1.2rem;'></div>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#ff9800;'>🔎 Buscar producto</h3>", unsafe_allow_html=True)
    entrada = st.text_input("Escribí las iniciales o cualquier palabra del producto:")

    resultados = []
    if entrada:
        resultados = buscar_por_prefijo_o_contenido(productos, entrada)

    if resultados:
        st.markdown("<h4 style='color:#e6bc8a;'>Resultados encontrados:</h4>", unsafe_allow_html=True)
        for idx, (nombre, precio) in enumerate(resultados, 1):
            with st.container():
                st.markdown('<div class="result-card">', unsafe_allow_html=True)
                cols = st.columns([6, 2, 2, 2])
                with cols[0]:
                    st.markdown(f"<div class='producto-row'><b>{nombre}</b></div>", unsafe_allow_html=True)
                with cols[1]:
                    st.markdown(f"<div class='producto-row price-soft'>${precio}</div>", unsafe_allow_html=True)
                with cols[2]:
                    cantidad = st.number_input("Cantidad", min_value=1, max_value=100, value=1, key=f"cant_{idx}")
                with cols[3]:
                    agregar = st.button("Agregar", key=f"add_{idx}")
                    if agregar:
                        st.session_state.carrito.append((nombre, precio, cantidad))
                        st.success(f"Agregado: {cantidad} x {nombre} (${precio} c/u)")
                st.markdown('</div>', unsafe_allow_html=True)
    elif entrada:
        st.warning("No se encontró ningún producto con ese nombre.")

    st.divider()
    st.markdown('<div class="carrito-box">', unsafe_allow_html=True)
    st.header("🛍️ Resumen de compra")
    cantidad_total = 0
    total = 0.0

    if st.session_state.carrito:
        quitar_idx = st.session_state.get("quitar_idx", None)
        for i, (nombre, precio, cantidad) in enumerate(st.session_state.carrito):
            try:
                precio_float = float(precio)
            except ValueError:
                try:
                    precio_float = float(str(precio).replace('.', '').replace(',', '.'))
                except ValueError:
                    precio_float = 0.0
            subtotal = precio_float * cantidad
            total += subtotal
            cols = st.columns([8, 1])
            with cols[0]:
                st.markdown(
                    f"<div style='font-size:1.08rem;'><span style='color:#ff9800;'>🟢</span> <b>{cantidad} x {nombre}</b> <span style='color:#ff9800;'>(${precio} c/u)</span></div>",
                    unsafe_allow_html=True
                )
            with cols[1]:
                if st.button("❌", key=f"del_{i}"):
                    st.session_state.quitar_idx = i
        if "quitar_idx" in st.session_state:
            idx = st.session_state.quitar_idx
            if 0 <= idx < len(st.session_state.carrito):
                st.session_state.carrito.pop(idx)
            del st.session_state["quitar_idx"]
            st.rerun() # Usar st.rerun() en lugar de st.stop() para un mejor flujo

        cantidad_total = sum(cantidad for _, _, cantidad in st.session_state.carrito)
        total_str = f"{total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(f"<div class='total-soft'>TOTAL: ${total_str}</div>", unsafe_allow_html=True)
        st.markdown(f"<span class='total-soft' style='font-size:1.1rem;'>Cantidad total de productos llevados: <b>{cantidad_total}</b></span>", unsafe_allow_html=True)

        if st.button("🗑️ Vaciar carrito"):
            st.session_state.carrito = []
            st.rerun() # Usar st.rerun() en lugar de st.stop() para un mejor flujo

        # --- NUEVO: Interfaz para enviar pedido por WhatsApp ---
        if "show_whatsapp_form" not in st.session_state:
            st.session_state.show_whatsapp_form = False

        if st.button("📲 Enviar pedido por WhatsApp"):
            st.session_state.show_whatsapp_form = True

        if st.session_state.show_whatsapp_form:
            with st.form("whatsapp_form", clear_on_submit=False):
                nombre_cliente = st.text_input("Tu nombre y apellido")
                st.markdown("#### Productos seleccionados:")
                for nombre, precio, cantidad in st.session_state.carrito:
                    st.markdown(f"- {cantidad} x {nombre} (${precio} c/u)")
                st.markdown(f"**Total:** ${total_str}")
                enviar = st.form_submit_button("Enviar pedido")

                if enviar:
                    # --- LÓGICA DE ENVÍO DE WHATSAPP DIRECTAMENTE DESDE STREAMLIT ---
                    if twilio_client and RECIPIENT_WHATSAPP_NUMBER and TWILIO_WHATSAPP_NUMBER:
                        mensaje = f"🛍️ *¡NUEVO PEDIDO RECIBIDO!* 🛍️\n\n"
                        mensaje += f"👤 *Cliente:* {nombre_cliente if nombre_cliente else 'Cliente Desconocido'}\n"
                        mensaje += f"📅 *Fecha y Hora:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                        mensaje += f"*Productos:*\n"
                        productos_enviados = False
                        for nombre, precio, cantidad in st.session_state.carrito:
                            productos_enviados = True
                            try:
                                precio_float = float(str(precio).replace('.', '').replace(',', '.'))
                            except Exception:
                                precio_float = 0.0
                            subtotal = precio_float * cantidad
                            mensaje += f"- {cantidad} x {nombre} (${precio_float:,.2f} c/u) = *${subtotal:,.2f}*\n"
                        if not productos_enviados:
                            mensaje += "  _No hay productos en este pedido._\n"

                        mensaje += f"\n*Total del Pedido:* ${total:,.2f}\n"
                        mensaje += f"*Cantidad Total de Productos:* {cantidad_total}\n\n"
                        mensaje += "¡Revisa tu tienda!"

                        try:
                            message = twilio_client.messages.create(
                                from_=TWILIO_WHATSAPP_NUMBER,
                                body=mensaje,
                                to=RECIPIENT_WHATSAPP_NUMBER
                            )
                            st.success("¡Gracias por comprar! Tu pedido fue enviado correctamente por WhatsApp.")
                            st.session_state.carrito = []
                            st.session_state.show_whatsapp_form = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Tu compra no se realizó correctamente. Intenta nuevamente. Detalle: {e}")
                    else:
                        st.error("Tu compra no se realizó correctamente. Intenta nuevamente. (Twilio no inicializado)")

            if st.button("Cancelar envío por WhatsApp", key="cancelar_whatsapp_form"):
                st.session_state.show_whatsapp_form = False
                st.rerun() # Opcional: para que se actualice la vista inmediatamente
    else:
        st.markdown(
            "<div class='no-products-message'>"
            "🛒 <span>No hay productos en el carrito.</span>"
            "</div>",
            unsafe_allow_html=True
        )
    st.markdown('</div>', unsafe_allow_html=True) # Cierra carrito-box
    st.markdown('</div>', unsafe_allow_html=True) # Cierra central-card

    # --- Pie de página ---
    st.markdown(
        """
        <div style='text-align:center; color:#ff9800; margin-top:2rem; font-size:1.1rem;'>
            <span style='font-size:1.7rem;'>✨</span>
            <br>
            <span style='font-weight:bold;'>¡Gracias por visitar la Tienda Inteligente!</span>
            <br>
            <span style='font-size:1rem;'>Hecho con ❤️ para vos</span>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()