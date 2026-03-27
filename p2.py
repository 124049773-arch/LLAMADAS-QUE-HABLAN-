import streamlit as st
import pandas as pd
import zipfile
import os

st.title("Llamadas que hablan Línea de Mujeres CDMX")
st.title("La cicatriz es la prueba de que sobreviviste, pero tu brillo es la prueba de que venciste")
st.markdown("Visualización dinámica de los reportes de atención.")

# Cargar datos
zip_file = "linea-mujeres-cdmx_compressed_1774561829934.zip"

if os.path.exists(zip_file):
    st.success(f"✅ Archivo encontrado: {zip_file}")
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            archivos = zip_ref.namelist()
            st.write(f"Archivos dentro del ZIP: {archivos}")
            
            for archivo in archivos:
                if archivo.endswith('.csv'):
                    with zip_ref.open(archivo) as csv_file:
                        df = pd.read_csv(csv_file, encoding='latin1')
                        st.success(f"✅ Datos cargados: {len(df):,} registros")
                        st.write(f"Columnas encontradas: {df.columns.tolist()}")
                        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error al leer archivo: {e}")
else:
    st.error(f"❌ Archivo no encontrado")
    st.write("Archivos disponibles:", os.listdir('.'))
