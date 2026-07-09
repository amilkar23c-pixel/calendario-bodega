import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

# 1. Simulación de la Base de Datos (Esto se reemplazaría con la lectura de tu Excel)
if 'entregas_db' not in st.session_state:
    st.session_state.entregas_db = pd.DataFrame([
        {
            "ID": 1, "Proveedor": "Distribuidora X", "OC": "10023", 
            "Fecha Sugerida": "2026-07-10", "Hora Sugerida": "08:00 AM", 
            "Volumen": "4 Pallets", "Estado": "Pendiente", "Notas Bodega": ""
        },
        {
            "ID": 2, "Proveedor": "Logística Global", "OC": "10024", 
            "Fecha Sugerida": "2026-07-10", "Hora Sugerida": "10:30 AM", 
            "Volumen": "10 Pallets", "Estado": "Pendiente", "Notas Bodega": ""
        }
    ])

st.title("📅 Sistema de Programación de Entregas")
st.markdown("---")

# 2. Selector de Rol (En producción esto puede ser automático o por login simple)
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
            volumen = st.text_input("Volumen Estimado (Ej: 3 Pallets, 50 Cajas)")
            
        submit = st.form_submit_button("Enviar a Bodega")
        
        if submit and proveedor and oc:
            # Añadir a la base de datos
            nueva_fila = {
                "ID": len(st.session_state.entregas_db) + 1,
                "Proveedor": proveedor, "OC": oc,
                "Fecha Sugerida": str(fecha), "Hora Sugerida": hora.strftime("%I:%M %p"),
                "Volumen": volumen, "Estado": "Pendiente", "Notas Bodega": ""
            }
            st.session_state.entregas_db = pd.concat([st.session_state.entregas_db, pd.DataFrame([nueva_fila])], ignore_index=True)
            st.success(f"Propuesta para {proveedor} enviada con éxito.")
            st.rerun()

    st.subheader("📋 Estado Actual de las Entregas")
    st.dataframe(st.session_state.entregas_db, use_container_width=True)

# ==========================================
# VISTA DE BODEGA
# ==========================================
else:
    st.header("📦 Panel de Control de Bodega")
    st.markdown("Revise las propuestas de compras y confirme el horario para preparar devoluciones.")

    # Filtrar solo lo pendiente
    pendientes = st.session_state.entregas_db[st.session_state.entregas_db["Estado"] == "Pendiente"]

    if pendientes.empty:
        st.info("🎉 No hay entregas pendientes por aprobar para esta semana.")
    else:
        for idx, row in pendientes.iterrows():
            # Crear una tarjeta visual para cada entrega pendiente
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 2, 2, 2])
                with c1:
                    st.markdown(f"**Proveedor:** {row['Proveedor']}")
                    st.markdown(f"**OC:** {row['OC']}")
                with c2:
                    st.markdown(f"**Fecha Propuesta:** {row['Fecha Sugerida']}")
                    st.markdown(f"**Hora:** {row['Hora Sugerida']}")
                with c3:
                    st.markdown(f"**Volumen:** {row['Volumen']}")
                    nota_bodega = st.text_input("Notas de devolución / mermas:", key=f"nota_{row['ID']}")
                with c4:
                    st.write("") # Espaciador
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✔️ Aprobar", key=f"app_{row['ID']}", type="primary"):
                            st.session_state.entregas_db.at[idx, "Estado"] = "Aprobado"
                            st.session_state.entregas_db.at[idx, "Notas Bodega"] = nota_bodega
                            st.success("Entrega aprobada.")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Rechazar", key=f"rej_{row['ID']}"):
                            st.session_state.entregas_db.at[idx, "Estado"] = "Reprogramar"
                            st.session_state.entregas_db.at[idx, "Notas Bodega"] = "Solicita cambio de hora"
                            st.warning("Se ha notificado el rechazo.")
                            st.rerun()

    # Mostrar historial de lo ya procesado abajo
    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado")
    confirmados = st.session_state.entregas_db[st.session_state.entregas_db["Estado"] != "Pendiente"]
    st.dataframe(confirmados, use_container_width=True)
