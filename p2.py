import streamlit as st
import pandas as pd
import zipfile
import os

st.set_page_config(page_title="Dashboard", layout="wide")

st.title("Llamadas que hablan Línea de Mujeres CDMX")

@st.cache_data
def load_data():
    """Carga los datos"""
    zip_file = "linea-mujeres-cdmx_compressed_1774561829934.zip"
    
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        for archivo in zip_ref.namelist():
            if archivo.endswith('.csv'):
                with zip_ref.open(archivo) as csv_file:
                    # Leer línea por línea
                    content = csv_file.read().decode('latin1')
                    lines = content.split('\n')
                    
                    # Obtener columnas
                    columnas = lines[0].strip().split(',')
                    
                    # Procesar datos
                    data = []
                    for line in lines[1:]:
                        if line.strip():
                            valores = line.strip().split(',')
                            if len(valores) == len(columnas):
                                data.append(valores)
                    
                    df = pd.DataFrame(data, columns=columnas)
                    
                    # Convertir edad a número
                    df['edad'] = pd.to_numeric(df['edad'], errors='coerce')
                    df['mes_alta'] = pd.to_numeric(df['mes_alta'], errors='coerce')
                    
                    return df

df = load_data()

st.success(f"✅ Datos cargados: {len(df):,} registros")

# Mostrar columnas disponibles
with st.expander("Ver columnas disponibles"):
    st.write(df.columns.tolist())

# Filtros en sidebar
st.sidebar.header("Filtros")

# Filtro Estado
estados = sorted(df['estado_usuaria'].dropna().unique())
estado_seleccionado = st.sidebar.multiselect("Estado", estados, default=[])

if estado_seleccionado:
    df_filtrado = df[df['estado_usuaria'].isin(estado_seleccionado)]
else:
    df_filtrado = df

# Filtro Municipio
municipios = sorted(df_filtrado['municipio_usuaria'].dropna().unique())
municipio_seleccionado = st.sidebar.multiselect("Municipio", municipios, default=[])

if municipio_seleccionado:
    df_final = df_filtrado[df_filtrado['municipio_usuaria'].isin(municipio_seleccionado)]
else:
    df_final = df_filtrado

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Total Reportes", f"{len(df_final):,}")
col2.metric("Edad Promedio", f"{df_final['edad'].mean():.0f}")
col3.metric("Municipios", f"{df_final['municipio_usuaria'].nunique()}")

# Mostrar datos
st.subheader("Vista previa de los datos")
st.dataframe(df_final.head(100))
