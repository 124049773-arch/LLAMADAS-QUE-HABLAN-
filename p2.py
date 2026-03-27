import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import sqlite3
from datetime import datetime
import plotly.graph_objects as go
import numpy as np
import zipfile
import os

WIDTH = 650
HEIGHT = 450

st.set_page_config(page_title="Dashb Línea de Mujeres", layout="wide")

st.markdown("""
<style>
.stApp {background-color: #F9F5FF;}
[data-testid="stSidebar"] {background-color: #E6CCFF;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {color: #581C87;}
.stMultiSelect div[data-baseweb="select"] {background-color: #F3E8FF; border-radius: 10px;}
span[data-baseweb="tag"] {background-color: #9333EA !important; color: white !important; border-radius: 8px;}
span[data-baseweb="tag"] svg {fill: white !important;}
span[data-baseweb="tag"]:hover {background-color: #7E22CE !important;}
h1 {color: #6B21A8;}
</style>
""", unsafe_allow_html=True)

st.title("Llamadas que hablan Línea de Mujeres CDMX")
st.title("La cicatriz es la prueba de que sobreviviste, pero tu brillo es la prueba de que venciste")
st.markdown("Visualización dinámica de los reportes de atención.")

# ==================== CONFIGURACIÓN DE BASE DE DATOS ====================
def init_database():
    """Inicializa la base de datos SQLite"""
    conn = sqlite3.connect('cuestionario_mujeres.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS respuestas_cuestionario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP,
        edad_grupo TEXT,
        situacion TEXT,
        frecuencia TEXT,
        relacion TEXT,
        hablado_alguien TEXT
    )''')
    
    conn.commit()
    conn.close()

def guardar_respuesta(datos):
    """Guarda las respuestas del cuestionario en la base de datos"""
    try:
        conn = sqlite3.connect('cuestionario_mujeres.db')
        c = conn.cursor()
        
        c.execute('''INSERT INTO respuestas_cuestionario 
                    (fecha, edad_grupo, situacion, frecuencia, relacion, hablado_alguien)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                  (datetime.now(), 
                   datos['edad_grupo'],
                   datos['situacion'],
                   datos['frecuencia'],
                   datos['relacion'],
                   datos['hablado_alguien']))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

def cargar_respuestas_cuestionario():
    """Carga las respuestas del cuestionario para análisis"""
    try:
        conn = sqlite3.connect('cuestionario_mujeres.db')
        df = pd.read_sql_query("SELECT * FROM respuestas_cuestionario", conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# Inicializar base de datos
init_database()
# ==================== FIN CONFIGURACIÓN BASE DE DATOS ====================

@st.cache_data
def load_data():
    """Carga los datos del archivo CSV (comprimido o no)"""
    
    # Buscar archivos ZIP
    archivos_zip = [f for f in os.listdir('.') if f.endswith('.zip')]
    
    if archivos_zip:
        for zip_file in archivos_zip:
            try:
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    csv_en_zip = [f for f in zip_ref.namelist() if f.endswith('.csv')]
                    
                    if csv_en_zip:
                        with zip_ref.open(csv_en_zip[0]) as csv_file:
                            for encoding in ['latin1', 'utf-8', 'iso-8859-1']:
                                try:
                                    csv_file.seek(0)
                                    df = pd.read_csv(csv_file, encoding=encoding)
                                    st.success(f"✅ Datos cargados correctamente desde ZIP: {len(df)} registros")
                                    return df
                                except:
                                    continue
            except Exception as e:
                continue
    
    st.error("❌ No se encontró ningún archivo de datos válido")
    return None

# Cargar datos
df = load_data()

if df is None:
    st.error("No se pudieron cargar los datos")
    st.stop()

# ==================== MOSTRAR INFORMACIÓN DE LAS COLUMNAS ====================
st.header("🔍 DIAGNÓSTICO - Nombres de las columnas")

st.subheader("📋 Nombres de todas las columnas:")
st.code(df.columns.tolist(), language="python")

st.subheader("👀 Vista previa de los primeros 5 registros:")
st.dataframe(df.head())

st.subheader("📊 Información básica del dataset:")
st.write(f"Total de registros: {len(df):,}")
st.write(f"Total de columnas: {len(df.columns)}")

# Mostrar tipos de datos
st.write("Tipos de datos por columna:")
st.dataframe(df.dtypes.reset_index().rename(columns={'index': 'Columna', 0: 'Tipo'}))

# Detener la ejecución para que puedas ver la información
st.info("⏸️ Este es un diagnóstico. Copia los nombres de las columnas y compártelos para ajustar el código.")

# Si quieres continuar con la app, comenta la línea de abajo
st.stop()

# ==================== CONTINUACIÓN DE LA APP (se ejecutará después del diagnóstico) ====================

# El resto de tu código iría aquí...
