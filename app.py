import streamlit as st
import pandas as pd
import gspread
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# 1. Autenticación con Google Sheets usando Secrets
try:
    # Lee las credenciales de servicio guardadas de forma segura en los Secrets
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    # Abre la hoja usando la URL que guardamos antes
    sh = gc.open_by_url(st.secrets["connections"]["gsheets"]["spreadsheet"])
    worksheet = sh.get_worksheet(0) # Abrir la primera pestaña
except Exception as e:
    st.error(f"Error de conexión con Google Sheets. Verifica tus credenciales en Secrets. Detalle: {e}")
    st.stop()

# Función para leer los datos frescos y convertirlos a DataFrame limpia
def cargar_datos():
    lista_filas = worksheet.get_all_records()
    if not lista_filas:
        return pd.DataFrame(columns=["ID", "Proveedor", "OC", "Fecha Sugerida", "Hora Sugerida", "Volumen", "Estado", "Notas Bodega"])
    
    df = pd.DataFrame(lista_filas)
    
    # Asegurar tipos de datos correctos
    df["Notas Bodega"] = df["Notas Bodega"].astype(str).replace("nan", "")
    df["Estado"] = df["Estado"].astype(str).replace("nan", "Pendiente")
    df["Proveedor"] = df["Proveedor"].astype(str).replace("nan", "")
    df["OC"] = df["OC"].astype(str).replace("nan", "")
    df["ID"] = pd.to_numeric(df["ID"], errors='coerce').fillna(0).astype(int)
    return df

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
            df_guardar = cargar_datos()
            nuevo_id = int(df_guardar["ID"].max() + 1) if not df_guardar.empty else 1
            
            nueva_fila = [
                nuevo_id,
                proveedor, 
                str(oc),
                str(fecha), 
                hora.strftime("%I:%M %p"),
                volumen, 
                "Pendiente", 
                ""
            ]
            
            # Añadir fila al final de la hoja de Google Sheets
            worksheet.append_row(nueva_fila)
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
                            # Buscar la fila exacta en Google Sheets (gspread cuenta desde la fila 1 y los headers son la fila 1)
                            fila_num = idx + 2 
                            worksheet.update_cell(fila_num, 7, "Aprobado") # Columna 7 es Estado
                            worksheet.update_cell(fila_num, 8, nota_bodega) # Columna 8 es Notas Bodega
                            st.success("Entrega aprobada exitosamente.")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Rechazar", key=f"rej_{row['ID']}"):
                            fila_num = idx + 2
                            worksheet.update_cell(fila_num, 7, "Reprogramar")
                            worksheet.update_cell(fila_num, 8, "Solicita cambio de hora")
                            st.warning("Estado actualizado a Reprogramar.")
                            st.rerun()

    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado")
    confirmados = df_bodega[df_bodega["Estado"] != "Pendiente"]
    st.dataframe(confirmados, use_container_width=True)
