import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime
import zipfile
import os
import numpy as np

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
    try:
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
        return True
    except:
        return False

def guardar_respuesta(datos):
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
    except:
        return False

def cargar_respuestas_cuestionario():
    try:
        if os.path.exists('cuestionario_mujeres.db'):
            conn = sqlite3.connect('cuestionario_mujeres.db')
            df = pd.read_sql_query("SELECT * FROM respuestas_cuestionario", conn)
            conn.close()
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

init_database()
# ==================== FIN CONFIGURACIÓN ====================

@st.cache_data
def load_data():
    """Carga los datos del archivo ZIP"""
    zip_file = "linea-mujeres-cdmx_compressed_1774561829934.zip"
    
    if not os.path.exists(zip_file):
        archivos_zip = [f for f in os.listdir('.') if f.endswith('.zip')]
        if archivos_zip:
            zip_file = archivos_zip[0]
        else:
            return None
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for archivo in zip_ref.namelist():
                if archivo.endswith('.csv'):
                    with zip_ref.open(archivo) as csv_file:
                        content = csv_file.read().decode('latin1')
                        lines = content.split('\n')
                        
                        # Obtener columnas de la primera línea
                        columnas = lines[0].strip().split(',')
                        
                        # Procesar datos
                        data = []
                        for line in lines[1:]:
                            if line.strip():
                                valores = line.strip().split(',')
                                if len(valores) == len(columnas):
                                    data.append(valores)
                        
                        df = pd.DataFrame(data, columns=columnas)
                        
                        # Limpiar datos
                        for col in df.columns:
                            df[col] = df[col].str.replace('ï¾\x89', 'É').str.replace('ï¾\x8D', 'Í')
                            df[col] = df[col].str.replace('ï¾\x8F', 'Ó').str.replace('ï¾\x9A', 'Ú')
                        
                        # Convertir edad a número
                        if 'edad' in df.columns:
                            df['edad'] = pd.to_numeric(df['edad'], errors='coerce')
                        
                        # Convertir mes_alta a número
                        if 'mes_alta' in df.columns:
                            df['mes_alta'] = pd.to_numeric(df['mes_alta'], errors='coerce')
                        
                        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Cargar datos
df = load_data()

if df is None:
    st.error("No se pudieron cargar los datos")
    st.stop()

# ==================== FILTROS ====================
st.sidebar.header("Filtros")

# Filtro por Estado
estados_disponibles = df['estado_usuaria'].dropna().unique()
estado = st.sidebar.multiselect(
    "Selecciona Estado:",
    options=sorted(estados_disponibles),
    default=[]
)

if estado:
    df_filtrado = df[df['estado_usuaria'].isin(estado)]
else:
    df_filtrado = df

# Filtro por Municipio
municipios_disponibles = df_filtrado['municipio_usuaria'].dropna().unique()
municipio = st.sidebar.multiselect(
    "Selecciona Municipio:",
    options=sorted(municipios_disponibles),
    default=[]
)

if municipio:
    df_selection = df_filtrado[df_filtrado['municipio_usuaria'].isin(municipio)]
else:
    df_selection = df_filtrado

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Total Reportes", f"{len(df_selection):,}")
col2.metric("Edad Promedio", f"{df_selection['edad'].mean():.0f}" if 'edad' in df_selection else "N/A")
col3.metric("Municipios", f"{df_selection['municipio_usuaria'].nunique():,}")

# ==================== GRÁFICA 1: OCUPACIÓN ====================
st.subheader("📊 Distribución por Ocupación")
if 'ocupacion' in df_selection.columns:
    ocupacion_counts = df_selection['ocupacion'].value_counts().head(10)
    fig = px.pie(values=ocupacion_counts.values, 
                 names=ocupacion_counts.index,
                 title="Top 10 Ocupaciones",
                 hole=0.4,
                 color_discrete_sequence=px.colors.purples.Purples_r)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

# ==================== GRÁFICA 2: MESES ====================
st.subheader("📅 Atenciones por Mes")
if 'mes_alta' in df_selection.columns:
    meses = {1:'Ene',2:'Feb',3:'Mar',4:'Abr',5:'May',6:'Jun',
             7:'Jul',8:'Ago',9:'Sep',10:'Oct',11:'Nov',12:'Dic'}
    
    mes_counts = df_selection['mes_alta'].value_counts().sort_index()
    mes_df = pd.DataFrame({'mes': [meses.get(m, str(m)) for m in mes_counts.index], 
                          'total': mes_counts.values})
    
    fig = px.bar(mes_df, x='mes', y='total', 
                 title="Llamadas por Mes",
                 color='total',
                 color_continuous_scale='Purples')
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

# ==================== GRÁFICA 3: EDADES ====================
st.subheader("👥 Distribución de Edades")
if 'edad' in df_selection.columns:
    fig = px.histogram(df_selection, x='edad', 
                       title="Edad de las Usuarias",
                       nbins=30,
                       color_discrete_sequence=['#9333EA'])
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

# ==================== GRÁFICA 4: ESTADO CIVIL ====================
st.subheader("💍 Estado Civil")
if 'estado_civil' in df_selection.columns:
    ec_counts = df_selection['estado_civil'].value_counts()
    fig = px.bar(x=ec_counts.index, y=ec_counts.values,
                 title="Estado Civil de las Usuarias",
                 color=ec_counts.values,
                 color_continuous_scale='Purples')
    fig.update_layout(height=450, xaxis_tickangle=45)
    st.plotly_chart(fig, use_container_width=True)

# ==================== GRÁFICA 5: TEMÁTICAS ====================
st.header("🏷️ Análisis de Temáticas")

tematicas_cols = ['tematica_1', 'tematica_2', 'tematica_3', 'tematica_4', 
                  'tematica_5', 'tematica_6', 'tematica_7']
tematicas_existentes = [col for col in tematicas_cols if col in df_selection.columns]

if tematicas_existentes:
    # Combinar todas las temáticas
    todas_tematicas = []
    for col in tematicas_existentes:
        todas_tematicas.extend(df_selection[col].dropna().tolist())
    
    tematica_counts = pd.Series(todas_tematicas).value_counts().head(15)
    
    fig = px.bar(x=tematica_counts.values, 
                 y=tematica_counts.index,
                 orientation='h',
                 title="Top 15 Temáticas más Reportadas",
                 color=tematica_counts.values,
                 color_continuous_scale='Purples_r')
    fig.update_layout(height=500, yaxis=dict(autorange="reversed"))
    st.plotly_chart(fig, use_container_width=True)

# ==================== GRÁFICA 6: ESCOLARIDAD ====================
st.header("🎓 Análisis de Escolaridad")
if 'escolaridad' in df_selection.columns:
    esc_counts = df_selection['escolaridad'].value_counts()
    fig = px.pie(values=esc_counts.values, 
                 names=esc_counts.index,
                 title="Nivel Educativo de las Usuarias",
                 hole=0.4,
                 color_discrete_sequence=px.colors.purples.Purples_r)
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

# ==================== CUESTIONARIO ====================
st.markdown("---")
st.header("📝 Encuesta")
st.markdown("Cuéntanos qué fue lo que sucedió ese día")

with st.form(key="cuestionario_form", clear_on_submit=True):
    col_q1, col_q2 = st.columns(2)
    
    with col_q1:
        edad_grupo = st.selectbox("¿Qué edad tienes?",
            ["Menor de 10", "10-15", "15-25", "25-35", "35-45", "Mayor de 45"])
        
        situacion = st.selectbox("¿Has experimentado alguna situación?",
            ["Abuso sexual", "Violencia Familiar", "Abuso de confianza", 
             "Violación en la escuela o trabajo", "Otros"])
    
    with col_q2:
        frecuencia = st.selectbox("¿Con qué frecuencia ocurre?",
            ["Ocurrió una vez", "De vez en cuando", "Frecuentemente", "Me está pasando ahora"])
        
        relacion = st.selectbox("Relación con la persona",
            ["Pareja", "Familiar", "Trabajo", "Otro"])
    
    hablado_alguien = st.selectbox("¿Has hablado con alguien?", ["Sí", "No"])
    
    submitted = st.form_submit_button("Enviar Respuesta", use_container_width=True)
    
    if submitted:
        try:
            datos = {
                'edad_grupo': edad_grupo,
                'situacion': situacion,
                'frecuencia': frecuencia,
                'relacion': relacion,
                'hablado_alguien': hablado_alguien
            }
            guardar_respuesta(datos)
            st.success("¡Gracias por tu confianza! Tu respuesta ha sido guardada.")
            st.balloons()
        except:
            st.success("¡Gracias por compartir tu experiencia!")

# Botón de ayuda
if st.button("🆘 Necesitas Ayuda"):
    st.warning("""
    ### 📞 Líneas de ayuda disponibles:
    - **800 10 84 053** - Línea de atención ciudadana
    - **079** - Línea de mujeres
    
    ### 🏢 Sedes de atención:
    - **Secretaría de las Mujeres**: 442 215 3404
    - **Secretaría de la Mujer del Municipio**: 442 238 7700
    
    ### 🫂 Recuerda:
    **No estás sola. Hablar es el primer paso.**
    """)

# Mostrar estadísticas del cuestionario
df_respuestas = cargar_respuestas_cuestionario()
if not df_respuestas.empty:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Estadísticas de la Encuesta")
    st.sidebar.metric("Respuestas Recibidas", len(df_respuestas))
