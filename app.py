import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# 1. Configuración de enlaces directos (No requiere Cuenta de Servicio)
# Extraemos el ID de tu Google Sheet desde los Secrets para no exponerlo
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    # Extraer el ID único del documento entre '/d/' y '/edit'
    SHEET_ID = SHEET_URL.split("/d/")[1].split("/edit")[0]
except Exception:
    st.error("Error al obtener el enlace del Google Sheet desde Secrets. Asegúrate de tener guardado el parámetro [connections.gsheets].")
    st.stop()

# Enlaces para leer y escribir mediante peticiones Web (Web Apps)
URL_LEER = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
URL_FORM = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/formResponse"

# Función para leer datos en tiempo real
def cargar_datos():
    try:
        # Forzar a Google a enviar datos frescos agregando un parámetro aleatorio al final
        url_fresca = f"{URL_LEER}&cache_bypass={datetime.now().timestamp()}"
        df = pd.read_csv(url_fresca, dtype={'OC': str})
        
        # Rellenar vacíos y forzar textos
        if not df.empty:
            df["Notas Bodega"] = df["Notas Bodega"].fillna("").astype(str)
            df["Estado"] = df["Estado"].fillna("Pendiente").astype(str)
            df["Proveedor"] = df["Proveedor"].fillna("").astype(str)
            df["OC"] = df["OC"].fillna("").astype(str)
            df["ID"] = pd.to_numeric(df["ID"], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        st.error(f"Error al leer la hoja de cálculo: {e}")
        return pd.DataFrame(columns=["ID", "Proveedor", "OC", "Fecha Sugerida", "Hora Sugerida", "Volumen", "Estado", "Notas Bodega"])

# Función para enviar o actualizar datos mediante simulación de envío HTML
def enviar_datos_web(df_completo):
    # Dado que no usamos API con credenciales, la forma de guardar los cambios 
    # de manera masiva o por fila de forma ultra-simple es avisarte si la hoja requiere cambios manuales
    # o usar un script intermedio. Para garantizar la edición interactiva de Bodega sin servidores:
    pass

# Inicializar los datos
df_actual = cargar_datos()

# Selector de Rol en la barra lateral
rol = st.sidebar.selectbox("Selecciona tu Rol:", ["Compras (Tú)", "Bodega"])

# ==========================================
# VISTA DE COMPRAS (TÚ)
# ==========================================
if rol == "Compras (Tú)":
    st.header("🛒 Registrar Nueva Sugerencia de Entrega")
    st.info("Nota: Para registrar y modificar los datos de forma directa sin restricciones de red, añade las filas directamente a tu archivo de Google Sheets o usa un formulario conectado.")
    
    with st.form("nuevo_registro"):
        col1, col2, col3 = st.columns(3)
        with col1:
            proveedor = st.text_input("Proveedor")
            oc = st.text_input("Número de Orden de Compra (OC)")
        with col2:
            fecha = st.date_input("Fecha Sugerida", min_value=datetime.today())
            hora = st.time_input("Hora Sugerida")
        with col3:
            volumen = st.text_input("Volumen Estimado (Ej: 3 Pallets, 50 Cajas)")
            
        submit = st.form_submit_button("Enviar a Bodega")
        
        if submit and proveedor and oc:
            st.warning("🔄 Para guardar los datos en tiempo real de forma directa con seguridad perimetral de red, abre tu Google Sheet y añade la fila.")

    st.subheader("📋 Visualización de Entregas Registradas (Tiempo Real)")
    st.dataframe(df_actual, use_container_width=True)

# ==========================================
# VISTA DE BODEGA
# ==========================================
else:
    st.header("📦 Panel de Control de Bodega")
    st.markdown("Visualice el cronograma de entregas enviadas por Compras desde el Google Sheet.")

    # Mostrar cronograma interactivo basado en los datos de la hoja
    pendientes = df_actual[df_actual["Estado"] == "Pendiente"]

    if pendientes.empty:
        st.info("🎉 No hay entregas pendientes por aprobar registradas en este momento.")
    else:
        st.dataframe(pendientes, use_container_width=True)

    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado")
    confirmados = df_actual[df_actual["Estado"] != "Pendiente"]
    st.dataframe(confirmados, use_container_width=True)
