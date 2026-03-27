import streamlit as st
import pandas as pd
import zipfile
import os

st.title("🔍 DIAGNÓSTICO")

# Cargar datos
zip_file = "linea-mujeres-cdmx_compressed_1774561829934.zip"

if os.path.exists(zip_file):
    st.success(f"✅ Archivo encontrado")
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        archivos = zip_ref.namelist()
        
        for archivo in archivos:
            if archivo.endswith('.csv'):
                with zip_ref.open(archivo) as csv_file:
                    # Leer el archivo
                    content = csv_file.read().decode('latin1')
                    lines = content.split('\n')
                    
                    # Primera línea: nombres de columnas
                    primera_linea = lines[0]
                    st.subheader("📋 Primera línea (nombres de columnas):")
                    st.code(primera_linea)
                    
                    # Separar por comas
                    columnas = primera_linea.strip().split(',')
                    st.subheader(f"📊 Columnas detectadas ({len(columnas)}):")
                    st.write(columnas)
                    
                    # Mostrar primeras filas
                    st.subheader("👀 Primeras 3 filas de datos:")
                    for i in range(1, min(4, len(lines))):
                        st.code(lines[i])
                    
                    # Crear DataFrame para probar
                    st.subheader("📝 Creando DataFrame...")
                    
                    # Procesar datos
                    data = []
                    for line in lines[1:]:
                        if line.strip():
                            valores = line.strip().split(',')
                            if len(valores) == len(columnas):
                                data.append(valores)
                    
                    df = pd.DataFrame(data, columns=columnas)
                    st.success(f"✅ DataFrame creado con {len(df)} filas")
                    
                    # Mostrar columnas reales
                    st.subheader("📋 Columnas en el DataFrame:")
                    st.write(df.columns.tolist())
                    
                    # Mostrar primeras filas
                    st.subheader("👀 Primeras 5 filas del DataFrame:")
                    st.dataframe(df.head())
                    
                    # Verificar columnas importantes
                    st.subheader("🔍 Verificando columnas importantes:")
                    
                    columnas_buscar = ['estado_usuario', 'estado_usuaria', 'municipio_usuario', 'municipio_usuaria', 'ocupacion', 'edad', 'mes_alta']
                    
                    for col in columnas_buscar:
                        if col in df.columns:
                            st.success(f"✅ '{col}' ENCONTRADA")
                            st.write(f"   Valores únicos: {df[col].nunique()}")
                            st.write(f"   Muestra: {df[col].head(3).tolist()}")
                        else:
                            st.error(f"❌ '{col}' NO encontrada")
                    
                    break
else:
    st.error("Archivo no encontrado")
