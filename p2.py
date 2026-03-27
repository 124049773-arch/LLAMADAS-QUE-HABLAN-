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
    except Exception as e:
        return False

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
        return False

def cargar_respuestas_cuestionario():
    """Carga las respuestas del cuestionario para análisis"""
    try:
        if os.path.exists('cuestionario_mujeres.db'):
            conn = sqlite3.connect('cuestionario_mujeres.db')
            df = pd.read_sql_query("SELECT * FROM respuestas_cuestionario", conn)
            conn.close()
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

init_database()
# ==================== FIN CONFIGURACIÓN BASE DE DATOS ====================

@st.cache_data
def load_data():
    """Carga los datos del archivo ZIP y corrige el formato"""
    
    zip_file = "linea-mujeres-cdmx_compressed_1774561829934.zip"
    
    if not os.path.exists(zip_file):
        archivos_zip = [f for f in os.listdir('.') if f.endswith('.zip')]
        if archivos_zip:
            zip_file = archivos_zip[0]
        else:
            st.error("❌ No se encontró archivo ZIP")
            return None
    
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            archivos_internos = zip_ref.namelist()
            
            for archivo in archivos_internos:
                if archivo.endswith('.csv'):
                    with zip_ref.open(archivo) as csv_file:
                        # Leer el archivo línea por línea
                        content = csv_file.read().decode('latin1')
                        lines = content.split('\n')
                        
                        # La primera línea tiene los nombres de las columnas
                        columnas = lines[0].strip().split(',')
                        
                        # Procesar los datos
                        data = []
                        for line in lines[1:]:
                            if line.strip():
                                # Separar por comas, respetando que puede haber comillas
                                valores = []
                                valor_actual = ""
                                entre_comillas = False
                                
                                for char in line:
                                    if char == '"':
                                        entre_comillas = not entre_comillas
                                    elif char == ',' and not entre_comillas:
                                        valores.append(valor_actual.strip())
                                        valor_actual = ""
                                    else:
                                        valor_actual += char
                                
                                if valor_actual:
                                    valores.append(valor_actual.strip())
                                
                                if len(valores) == len(columnas):
                                    data.append(valores)
                        
                        df = pd.DataFrame(data, columns=columnas)
                        st.success(f"✅ Datos cargados: {len(df):,} registros")
                        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# Cargar datos
df = load_data()

if df is None:
    st.stop()

# ==================== NORMALIZAR NOMBRES ====================
df.columns = df.columns.str.lower().str.strip()

# Renombrar columnas para que coincidan con el código
renombres = {
    'estado_usuario': 'estado_usuaria',
    'municipio_usuario': 'municipio_usuaria',
    'colonia_usuario': 'colonia_usuaria',
    'cp_usuario': 'cp_usuaria'
}

for old, new in renombres.items():
    if old in df.columns:
        df.rename(columns={old: new}, inplace=True)

# ==================== FILTROS ====================
st.sidebar.header("Filtros")

# Filtro por Estado
if 'estado_usuaria' in df.columns:
    estados_disponibles = df['estado_usuaria'].dropna().unique()
    estado = st.sidebar.multiselect(
        "Selecciona Estado:",
        options=sorted(estados_disponibles),
        default=sorted(estados_disponibles)[:3] if len(estados_disponibles) > 3 else sorted(estados_disponibles)
    )
    
    if estado:
        df_filtrado_estado = df[df['estado_usuaria'].isin(estado)]
    else:
        df_filtrado_estado = df
else:
    st.sidebar.warning("⚠️ Columna 'estado_usuaria' no encontrada")
    df_filtrado_estado = df

# Filtro por Municipio
if 'municipio_usuaria' in df.columns:
    municipios_disponibles = df_filtrado_estado['municipio_usuaria'].dropna().unique()
    municipio = st.sidebar.multiselect(
        "Selecciona Municipio:",
        options=sorted(municipios_disponibles),
        default=sorted(municipios_disponibles)[:5] if len(municipios_disponibles) > 5 else sorted(municipios_disponibles)
    )
    
    if municipio:
        df_selection = df_filtrado_estado[df_filtrado_estado['municipio_usuaria'].isin(municipio)]
    else:
        df_selection = df_filtrado_estado
else:
    st.sidebar.info("ℹ️ Columna 'municipio_usuaria' no encontrada")
    df_selection = df_filtrado_estado

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Total Reportes", f"{len(df_selection):,}")

if 'edad' in df.columns:
    df_selection['edad'] = pd.to_numeric(df_selection['edad'], errors='coerce')
    edad_promedio = df_selection['edad'].mean()
    col2.metric("Edad Promedio", f"{edad_promedio:.0f}" if not pd.isna(edad_promedio) else "N/A")
else:
    col2.metric("Edad Promedio", "No disponible")

if 'municipio_usuaria' in df.columns:
    if 'municipio' in locals() and municipio:
        col3.metric("Municipios Seleccionados", f"{len(municipio)}")
    else:
        col3.metric("Municipios Totales", f"{len(df_selection['municipio_usuaria'].unique())}")
else:
    col3.metric("Municipios", "No disponible")

# ==================== GRÁFICA 1: OCUPACIÓN ====================
c1, c2 = st.columns([2,1])

with c1:
    st.subheader("Distribución por Ocupación")
    if 'ocupacion' in df.columns:
        df_ocupacion = df_selection['ocupacion'].dropna()
        if len(df_ocupacion) > 0:
            top_ocupaciones = df_ocupacion.value_counts().head(10)
            fig = px.pie(values=top_ocupaciones.values, 
                        names=top_ocupaciones.index, 
                        hole=0.6,
                        color_discrete_sequence=["#E6CCFF","#D8B4FE","#C084FC","#A855F7","#9333EA","#7E22CE"])
            fig.update_layout(width=WIDTH, height=HEIGHT)
            st.plotly_chart(fig, use_container_width=False)
        else:
            st.info("No hay datos")
    else:
        st.info("Columna 'ocupacion' no encontrada")

with c2:
    st.subheader("Análisis")
    st.write("- Distribución de ocupaciones de las usuarias")
    st.write("- Permite focalizar campañas de prevención")

# ==================== GRÁFICA 2: MESES ====================
c3, c4 = st.columns([2,1])

with c3:
    st.subheader("Atenciones por Mes")
    if 'mes_alta' in df.columns:
        mes_counts = df_selection['mes_alta'].value_counts().reset_index()
        mes_counts.columns = ['mes', 'total']
        mes_counts = mes_counts.sort_values(by='mes')
        fig = px.bar(mes_counts, x='mes', y='total', color_discrete_sequence=['#9333EA'])
        fig.update_layout(width=WIDTH, height=HEIGHT)
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.info("Columna 'mes_alta' no encontrada")

with c4:
    st.subheader("Análisis")
    st.write("- Distribución de llamadas por mes")
    st.write("- Permite planificar recursos")

# ==================== GRÁFICA 3: EDADES ====================
c5, c6 = st.columns([2,1])

with c5:
    st.subheader("Distribución de Edades")
    if 'edad' in df.columns:
        bins = st.slider("Intervalos", 5, 50, 20, key="bins")
        df_edad = df_selection['edad'].dropna()
        if len(df_edad) > 0:
            fig = px.histogram(df_edad, x="edad", nbins=bins, color_discrete_sequence=['#FFA200'])
            fig.update_layout(width=WIDTH, height=HEIGHT)
            st.plotly_chart(fig, use_container_width=False)
        else:
            st.info("No hay datos")
    else:
        st.info("Columna 'edad' no encontrada")

with c6:
    st.subheader("Análisis")
    st.write("- Concentración de edades")
    st.write("- Mayoría entre 30 y 50 años")

# ==================== GRÁFICA 4: ESTADO CIVIL ====================
c7, c8 = st.columns([2,1])

with c7:
    if 'estado_civil' in df.columns:
        st.subheader("Estado Civil")
        conteo = df_selection['estado_civil'].value_counts().reset_index()
        conteo.columns = ['estado_civil', 'total']
        fig = px.bar(conteo, x='estado_civil', y='total', color_discrete_sequence=["#9333EA"])
        fig.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=45)
        st.plotly_chart(fig, use_container_width=False)
    else:
        st.info("Columna 'estado_civil' no encontrada")

with c8:
    st.subheader("Análisis")
    st.write("- Distribución por estado civil")
    st.write("- Ayuda a entender el contexto familiar")

# ==================== GRÁFICA 5: TEMÁTICAS ====================
st.header("Análisis de Temáticas")

columnas_tematicas = ['tematica_1', 'tematica_2', 'tematica_3', 'tematica_4', 'tematica_5', 'tematica_6', 'tematica_7']
tematicas_existentes = [col for col in columnas_tematicas if col in df.columns]

if tematicas_existentes:
    df_temp = df_selection.copy()
    for col in tematicas_existentes:
        df_temp[col] = df_temp[col].fillna('No especificado')
    
    df_temp['tematicas_lista'] = df_temp[tematicas_existentes].apply(lambda x: x.tolist(), axis=1)
    df_exploded = df_temp.explode('tematicas_lista')
    df_exploded = df_exploded[df_exploded['tematicas_lista'] != 'No especificado']
    df_exploded = df_exploded.rename(columns={'tematicas_lista': 'tematica'})
    
    c_tem1, c_tem2 = st.columns([2,1])
    
    with c_tem1:
        st.subheader("Top 15 temáticas")
        top = df_exploded['tematica'].value_counts().head(15)
        
        if len(top) > 0:
            fig = px.bar(x=top.values, y=top.index, orientation='h',
                        color=top.values, color_continuous_scale='Purples_r')
            fig.update_layout(width=WIDTH, height=HEIGHT, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig, use_container_width=False)
    
    with c_tem2:
        st.subheader("Análisis")
        st.write("- Problemáticas más frecuentes")
        st.write("- Priorizar atención en las primeras")

# ==================== CUESTIONARIO ====================
st.markdown("---")
st.header("Encuesta")
st.title("Cuéntanos qué fue lo que sucedió ese día")

with st.form(key="cuestionario_form", clear_on_submit=True):
    edad_grupo = st.selectbox("¿Qué edad tienes?",
        ["Menor de 10", "10-15", "15-25", "25-35", "35-45", "Mayor de 45"])
    
    situacion = st.selectbox("¿Has experimentado alguna situación?",
        ["Abuso sexual", "Violencia Familiar", "Abuso de confianza", "Violación en la escuela o trabajo", "Otros"])
    
    frecuencia = st.selectbox("¿Con qué frecuencia ocurre?",
        ["Ocurrió una vez", "De vez en cuando", "Frecuentemente", "Me está pasando ahora"])
    
    relacion = st.selectbox("Relación con la persona",
        ["Pareja", "Familiar", "Trabajo", "Otro"])
    
    hablado_alguien = st.selectbox("¿Has hablado con alguien?", ["Sí", "No"])
    
    submitted = st.form_submit_button("Enviar", use_container_width=True)
    
    if submitted:
        try:
            datos = {
                'edad_grupo': edad_grupo,
                'situacion': situacion,
                'frecuencia': frecuencia,
                'relacion': relacion,
                'hablado_alguien': hablado_alguien
            }
            
            if guardar_respuesta(datos):
                st.success("¡Gracias por tu confianza!")
                st.balloons()
            else:
                st.info("¡Gracias por tu respuesta!")
                st.balloons()
        except:
            st.success("¡Gracias por compartir tu experiencia!")
            st.balloons()

if st.button("Necesitas ayuda"):
    st.warning("""
    📞 **Líneas de ayuda:**
    - **800 10 84 053** - Línea de atención ciudadana
    - **079** - Línea de mujeres
    
    🏢 **Sedes de atención:**
    - Secretaría de las Mujeres: 442 215 3404
    - Secretaría de la Mujer del Municipio: 442 238 7700
    
    🫂 **Recuerda: No estás sola.**
    """)

# Estadísticas
df_respuestas = cargar_respuestas_cuestionario()
if not df_respuestas.empty:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Encuesta")
    st.sidebar.metric("Respuestas", len(df_respuestas))
