import streamlit as st
import pandas as pd
import requests
from datetime import datetime

st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# 1. Enlaces desde Secrets
try:
    SHEET_URL = st.secrets["connections"]["gsheets"]["spreadsheet"]
    SHEET_ID = SHEET_URL.split("/d/")[1].split("/edit")[0]
    APPS_SCRIPT_URL = st.secrets["connections"]["gsheets"].get("apps_script_url", "")
except Exception:
    st.error("Verifica la configuración de tus Secrets.")
    st.stop()

URL_LEER = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def cargar_datos():
    try:
        url_fresca = f"{URL_LEER}&cache_bypass={datetime.now().timestamp()}"
        df = pd.read_csv(url_fresca, dtype={'OC': str})
        if not df.empty:
            df["Notas Bodega"] = df["Notas Bodega"].fillna("").astype(str)
            df["Estado"] = df["Estado"].fillna("Pendiente").astype(str)
            df["ID"] = pd.to_numeric(df["ID"], errors='coerce').fillna(0).astype(int)
        return df
    except Exception as e:
        return pd.DataFrame(columns=["ID", "Proveedor", "OC", "Fecha Sugerida", "Hora Sugerida", "Volumen", "Estado", "Notas Bodega"])

df_actual = cargar_datos()
rol = st.sidebar.selectbox("Selecciona tu Rol:", ["Compras (Tú)", "Bodega"])

# ==========================================
# VISTA DE COMPRAS (TÚ)
# ==========================================
if rol == "Compras (Tú)":
    st.header("🛒 Registrar Nueva Sugerencia de Entrega")
    
    with st.form("nuevo_registro"):
        col1, col2, col3 = st.columns(3)
        with col1:
            proveedor = st.text_input("Proveedor")
            oc = st.text_input("Número de Orden de Compra (OC)")
        with col2:
            fecha = st.date_input("Fecha Sugerida", min_value=datetime.today())
            hora = st.time_input("Hora Sugerida")
        with col3:
            volumen = st.text_input("Volumen Estimado")
            
        submit = st.form_submit_button("Enviar a Bodega")
        
        if submit and proveedor and oc:
            if not APPS_SCRIPT_URL:
                st.error("Falta configurar la URL de Apps Script en Secrets.")
            else:
                nuevo_id = int(df_actual["ID"].max() + 1) if not df_actual.empty else 1
                payload = {
                    "accion": "crear", "id": nuevo_id, "proveedor": proveedor, "oc": str(oc),
                    "fecha": str(fecha), "hora": hora.strftime("%I:%M %p"), "volumen": volumen,
                    "estado": "Pendiente", "notes": ""
                }
                res = requests.post(APPS_SCRIPT_URL, json=payload)
                if res.status_code == 200:
                    st.success(f"Propuesta para {proveedor} enviada con éxito.")
                    st.rerun()
                else:
                    st.error("Error al guardar los datos.")

    st.subheader("📋 Historial en Tiempo Real")
    # Corrección de use_container_width a width='stretch'
    st.dataframe(cargar_datos(), width='stretch')

# ==========================================
# VISTA DE BODEGA
# ==========================================
else:
    st.header("📦 Panel de Control de Bodega")
    pendientes = df_actual[df_actual["Estado"] == "Pendiente"]

    if pendientes.empty:
        st.info("🎉 No hay entregas pendientes.")
    else:
        for idx, row in pendientes.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                with c1:
                    st.markdown(f"**Proveedor:** {row['Proveedor']}\n**OC:** {row['OC']}")
                with c2:
                    st.markdown(f"**Fecha:** {row['Fecha Sugerida']}\n**Hora:** {row['Hora Sugerida']}")
                with c3:
                    st.markdown(f"**Volumen:** {row['Volumen']}")
                    nota_bodega = st.text_input("Notas:", key=f"nota_{row['ID']}")
                with c4:
                    st.write("")
                    cb1, cb2 = st.columns(2)
                    with cb1:
                        if st.button("✔️ ...Aprobar", key=f"app_{row['ID']}", type="primary"):
                            payload = {"accion": "actualizar", "id": int(row["ID"]), "estado": "Aprobado", "notas": nota_bodega}
                            requests.post(APPS_SCRIPT_URL, json=payload)
                            st.success("Aprobado.")
                            st.rerun()
                    with cb2:
                        if st.button("❌ Rechazar", key=f"rej_{row['ID']}"):
                            payload = {"accion": "actualizar", "id": int(row["ID"]), "estado": "Reprogramar", "notas": "Solicita cambio de hora"}
                            requests.post(APPS_SCRIPT_URL, json=payload)
                            st.warning("Rechazado.")
                            st.rerun()

    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado")
    # Corrección de use_container_width a width='stretch'
    st.dataframe(df_actual[df_actual["Estado"] != "Pendiente"], width='stretch')
