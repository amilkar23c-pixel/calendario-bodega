import streamlit as st
import requests
import csv
import os
from datetime import datetime

st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# 1. Enlaces desde las Variables de Entorno de Render
try:
    SHEET_URL = os.environ.get("spreadsheet", "").strip()
    APPS_SCRIPT_URL = os.environ.get("apps_script_url", "").strip()
    
    # Extracción limpia del ID evitando barras diagonales extras
    if "/d/" in SHEET_URL:
        SHEET_ID = SHEET_URL.split("/d/")[1].split("/")[0]
    else:
        SHEET_ID = SHEET_URL
except Exception as e:
    st.error(f"❌ Error al procesar las variables de entorno: {e}")
    st.stop()

URL_LEER = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

def cargar_datos_seguro():
    try:
        url_fresca = f"{URL_LEER}&cache_bypass={datetime.now().timestamp()}"
        # Agregamos un timeout de 10 segundos para que no se quede congelado
        respuesta = requests.get(url_fresca, timeout=10)
        
        if respuesta.status_code != 200:
            st.error(f"⚠️ Google Sheets devolvió el código de estado: {respuesta.status_code}")
            return []
            
        lineas = respuesta.text.splitlines()
        lector = csv.DictReader(lineas)
        datos = []
        for fila in lector:
            id_val = fila.get("ID", "0").strip()
            datos.append({
                "ID": int(id_val) if id_val.isdigit() else 0,
                "Proveedor": fila.get("Proveedor", "").strip(),
                "OC": fila.get("OC", "").strip(),
                "Fecha Sugerida": fila.get("Fecha Sugerida", "").strip(),
                "Hora Sugerida": fila.get("Hora Sugerida", "").strip(),
                "Volumen": fila.get("Volumen", "").strip(),
                "Estado": fila.get("Estado", "Pendiente").strip() if fila.get("Estado") else "Pendiente",
                "Notas Bodega": fila.get("Notas Bodega", "").strip()
            })
        return datos
    except requests.exceptions.Timeout:
        st.error("⏳ La conexión con Google Sheets tardó demasiado tiempo (Timeout). Reintenta recargando la página.")
        return []
    except Exception as e:
        st.error(f"❌ Error al leer los datos de Google: {e}")
        return []

lista_datos = cargar_datos_seguro()
rol = st.sidebar.selectbox("Selecciona tu Rol:", ["Compras (Tú)", "Bodega"])

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
                st.error("Falta configurar la URL de Apps Script en Render.")
            else:
                max_id = max([fila["ID"] for fila in lista_datos]) if lista_datos else 0
                nuevo_id = max_id + 1
                payload = {
                    "accion": "crear", "id": nuevo_id, "proveedor": proveedor, "oc": str(oc),
                    "fecha": str(fecha), "hora": hora.strftime("%I:%M %p"), "volumen": volumen,
                    "estado": "Pendiente", "notas": ""
                }
                try:
                    res = requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.success(f"Propuesta para {proveedor} enviada.")
                        st.rerun()
                    else:
                        st.error(f"Error del servidor de Google al guardar: {res.status_code}")
                except Exception as e:
                    st.error(f"No se pudo conectar con el Apps Script: {e}")

    st.subheader("📋 Historial en Tiempo Real")
    if lista_datos:
        st.dataframe(lista_datos)
    else:
        st.info("No hay registros disponibles en la hoja.")

else:
    st.header("📦 Panel de Control de Bodega")
    pendientes = [f for f in lista_datos if f["Estado"] == "Pendiente"]
    confirmados = [f for f in lista_datos if f["Estado"] != "Pendiente"]

    if not pendientes:
        st.info("🎉 No hay entregas pendientes.")
    else:
        for row in pendientes:
            with st.container():
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
                        if st.button("✔️ Aprobar", key=f"app_{row['ID']}", type="primary"):
                            payload = {"accion": "actualizar", "id": int(row["ID"]), "estado": "Aprobado", "notas": nota_bodega}
                            try:
                                requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
                                st.success("Aprobado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al conectar: {e}")
                    with cb2:
                        if st.button("❌ Rechazar", key=f"rej_{row['ID']}"):
                            payload = {"accion": "actualizar", "id": int(row["ID"]), "estado": "Reprogramar", "notas": "Solicita cambio de hora"}
                            try:
                                requests.post(APPS_SCRIPT_URL, json=payload, timeout=10)
                                st.warning("Rechazado.")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error al conectar: {e}")

    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado")
    if confirmados:
        st.dataframe(confirmados)
    else:
        st.info("Aún no hay entregas procesadas.")
