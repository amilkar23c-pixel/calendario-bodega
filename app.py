import streamlit as os
import streamlit as st
import pandas as pd
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

# Ruta del archivo Excel en tu OneDrive local (ajustada a tu ruta según tu terminal)
EXCEL_PATH = r"C:\Users\AmilcarContreras\OneDrive - Super Baru, S.A\Documentos\Calendario-Recibo\registro_entregas.xlsx"

# Función para cargar datos de Excel
def cargar_datos():
    try:
        df = pd.read_excel(EXCEL_PATH, dtype={'OC': str})
        return df
    except Exception as e:
        # Si el archivo no existe en la ruta, creamos uno temporal para evitar que la app se caiga
        st.error(f"No se encontró el archivo Excel en la ruta especificada. Cargando base de datos temporal. Error: {e}")
        return pd.DataFrame(columns=["ID", "Proveedor", "OC", "Fecha Sugerida", "Hora Sugerida", "Volumen", "Estado", "Notas Bodega"])

# Función para guardar datos en Excel
def guardar_datos(df):
    try:
        df.to_excel(EXCEL_PATH, index=False)
        return True
    except Exception as e:
        st.error(f"Error al guardar en el Excel: {e}")
        return False

# Inicializar datos
entregas_df = cargar_datos()

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# Selector de Rol en la barra lateral
rol = st.sidebar.selectbox("Selecciona tu Rol:", ["Compras (Tú)", "Bodega"])

# Re-cargar datos fresco en cada interacción
if 'df_actual' not in st.session_state:
    st.session_state.df_actual = entregas_df

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
            df_actual = cargar_datos()
            nuevo_id = int(df_actual["ID"].max() + 1) if not df_actual.empty and pd.notna(df_actual["ID"].max()) else 1
            
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
            
            df_actual = pd.concat([df_actual, pd.DataFrame([nueva_fila])], ignore_index=True)
            if guardar_datos(df_actual):
                st.success(f"Propuesta para {proveedor} guardada con éxito en el Excel compartido.")
                st.rerun()

    st.subheader("📋 Historial y Estado en el Excel Real")
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
                            df_actualizar = cargar_datos()
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Estado"] = "Aprobado"
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Notas Bodega"] = nota_bodega
                            guardar_datos(df_actualizar)
                            st.success("Entrega aprobada en el Excel.")
                            st.rerun()
                    with col_btn2:
                        if st.button("❌ Rechazar", key=f"rej_{row['ID']}"):
                            df_actualizar = cargar_datos()
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Estado"] = "Reprogramar"
                            df_actualizar.loc[df_actualizar["ID"] == row["ID"], "Notas Bodega"] = "Solicita cambio de hora"
                            guardar_datos(df_actualizar)
                            st.warning("Estado actualizado a Reprogramar.")
                            st.rerun()

    st.markdown("---")
    st.subheader("🗓️ Cronograma General Confirmado (Leído del Excel)")
    confirmados = df_bodega[df_bodega["Estado"] != "Pendiente"]
    st.dataframe(confirmados, use_container_width=True)
