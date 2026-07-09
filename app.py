import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# 1. Establecer conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para leer los datos frescos
def cargar_datos():
    # Lee la hoja de cálculo usando la configuración de secrets
    return conn.read(ttl="0s") # ttl="0s" obliga a leer datos en tiempo real sin caché

# Inicializar los datos del Sheet
try:
    df_actual = cargar_datos()
except Exception as e:
    st.error("Error al conectar con Google Sheets. Verifica la configuración de Secrets.")
    st.stop()

# Selector de Rol en la barra lateral
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
            # Traer datos actualizados para calcular el ID consecutivo
            df_guardar = cargar_datos()
            nuevo_id = int(df_guardar["ID"].max() + 1) if not df_guardar.empty and pd.notna(df_guardar["ID"].max()) else 1
            
            nueva_fila = {
                "ID": nuevo_id,
                "Proveedor": proveedor, 
                "OC": str(oc),
                "Fecha Sugerida": str(fecha), 
                "Hora Sugerida": hora.strftime("%I:%M %p"),
                "Volumen": volumen, 
                "Estado": "Pendiente", 
                "Notas Bodega": ""
            }
            
            # Unir y actualizar en la nube
            df_guardar = pd.concat([df_guardar, pd.DataFrame([nueva_fila])], ignore_index=True)
            conn.update(data=df_guardar)
            st.success(f"Propuesta para {proveedor} enviada con éxito a Bodega.")
            st.rerun()

    st.subheader("📋 Estado Actual en Google Sheets")
    st.dataframe(cargar_datos(), use_container_width=True)

# ==========================================
# VISTA DE BODEGA
# ==========================================
else:
    st.header("📦 Panel de Control de Bodega")
    st.markdown("Revise las propuestas de compras y confirme el horario para preparar devoluciones.")

    df_bodega = cargar_datos()
    # Asegurar filtrado correcto de pendientes
    pendientes = df_bodega[df_bodega["Estado"] == "Pendiente"]

    if pendientes.empty:
        st.info("🎉 No hay entregas pendientes por aprobar en este momento.")
    else:
        for idx, row in pendientes.iterrows():
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
                    st.write("") 
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("✔️ Aprobar", key=f"app_{row['ID']}", type="primary"):
                            df_actualizar = cargar_datos()
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Estado"] = "Aprobado"
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Notas Bodega"] = nota_bodega
                            conn.update(data=df_actualizar)
                            st.success("Entrega aprobada exitosamente.")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Rechazar", key=f"rej_{row['ID']}"):
                            df_actualizar = cargar_datos()
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Estado"] = "Reprogramar"
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Notas Bodega"] = "Solicita cambio de hora"
                            conn.update(data=df_actualizar)
                            st.warning("Estado actualizado a Reprogramar.")
                            st.rerun()

    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado")
    confirmados = df_bodega[df_bodega["Estado"] != "Pendiente"]
    st.dataframe(confirmados, use_container_width=True)
