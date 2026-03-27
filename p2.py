import streamlit as st
import pandas as pd
import zipfile
import os

st.title("Test - App funcionando")

st.write("La app está corriendo correctamente")

# Cargar datos
zip_file = "linea-mujeres-cdmx_compressed_1774561829934.zip"

if os.path.exists(zip_file):
    st.write(f"✅ Archivo encontrado: {zip_file}")
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            archivos = zip_ref.namelist()
            st.write(f"Archivos dentro del ZIP: {archivos}")
            
            for archivo in archivos:
                if archivo.endswith('.csv'):
                    with zip_ref.open(archivo) as csv_file:
                        df = pd.read_csv(csv_file, encoding='latin1')
                        st.success(f"✅ Datos cargados: {len(df)} registros")
                        st.write(f"Columnas: {df.columns.tolist()}")
                        st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.error(f"❌ Archivo no encontrado: {zip_file}")
    st.write("Archivos disponibles:", os.listdir('.'))
