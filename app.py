import streamlit as st
import requests
import csv
import os  # <-- Asegúrate de que esta línea esté
from datetime import datetime

st.set_page_config(page_title="Calendario de Recepción Bodega", layout="wide")

st.title("📅 Sistema de Programación de Entregas - Super Barú")
st.markdown("---")

# 1. Enlaces desde las Variables de Entorno de Render
try:
    SHEET_URL = os.environ.get("spreadsheet")
    APPS_SCRIPT_URL = os.environ.get("apps_script_url")
    SHEET_ID = SHEET_URL.split("/d/")[1].split("/edit")[0]
except Exception:
    st.error("Error al cargar las variables de entorno en el servidor.")
    st.stop()
