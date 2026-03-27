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
import glob

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
    """Carga los datos buscando en todas las ubicaciones posibles"""
    
    # Buscar en el directorio actual y subdirectorios
    archivos_encontrados = []
    
    # Buscar archivos CSV y ZIP
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.csv') or file.endswith('.zip'):
                archivos_encontrados.append(os.path.join(root, file))
    
    # Mostrar archivos encontrados para depuración (solo en modo desarrollo)
    if len(archivos_encontrados) > 0:
        with st.expander("🔍 Archivos encontrados (click para ver)"):
            for archivo in archivos_encontrados:
                st.write(f"- {archivo}")
    
    # Primero buscar archivos CSV directos
    for archivo in archivos_encontrados:
        if archivo.endswith('.csv'):
            try:
                # Intentar diferentes codificaciones
                for encoding in ['latin1', 'utf-8', 'iso-8859-1', 'cp1252']:
                    try:
                        df = pd.read_csv(archivo, encoding=encoding)
                        if len(df.columns) > 1:  # Verificar que se leyó correctamente
                            st.success(f"✅ Datos cargados correctamente desde: {archivo}")
                            st.success(f"📊 {len(df):,} registros, {len(df.columns)} columnas")
                            return df
                    except:
                        continue
            except Exception as e:
                continue
    
    # Si no hay CSV, buscar archivos ZIP
    for archivo in archivos_encontrados:
        if archivo.endswith('.zip'):
            try:
                with zipfile.ZipFile(archivo, 'r') as zip_ref:
                    # Listar archivos dentro del ZIP
                    archivos_zip = zip_ref.namelist()
                    
                    # Buscar archivos CSV dentro del ZIP
                    for archivo_zip in archivos_zip:
                        if archivo_zip.endswith('.csv'):
                            with zip_ref.open(archivo_zip) as csv_file:
                                # Intentar diferentes codificaciones
                                for encoding in ['latin1', 'utf-8', 'iso-8859-1', 'cp1252']:
                                    try:
                                        csv_file.seek(0)
                                        df = pd.read_csv(csv_file, encoding=encoding)
                                        if len(df.columns) > 1:
                                            st.success(f"✅ Datos cargados correctamente desde ZIP: {archivo}")
                                            st.success(f"📊 {len(df):,} registros, {len(df.columns)} columnas")
                                            return df
                                    except:
                                        continue
            except Exception as e:
                continue
    
    # Si no se encontró nada, mostrar error detallado
    st.error("❌ No se encontró ningún archivo de datos válido")
    st.write("### 📋 Instrucciones:")
    st.write("""
    1. Asegúrate de que tu archivo CSV o ZIP esté subido al repositorio
    2. El archivo debe estar en la carpeta principal del repositorio
    3. Puedes subir el archivo directamente desde GitHub:
       - Ve a tu repositorio
       - Haz clic en 'Add file' → 'Upload files'
       - Selecciona tu archivo CSV o ZIP
       - Haz clic en 'Commit changes'
    """)
    
    return None

# Cargar datos
df = load_data()

if df is None:
    st.stop()

# ==================== NORMALIZAR NOMBRES DE COLUMNAS ====================
# Convertir todos los nombres de columnas a minúsculas y quitar espacios
df.columns = df.columns.str.lower().str.strip()

# Verificar y limpiar nombres de columnas
df.columns = df.columns.str.replace('"', '').str.replace("'", "")

# Mostrar información de las columnas para depuración
with st.expander("📋 Ver estructura de datos (click para expandir)"):
    st.write("**Columnas encontradas:**")
    st.write(df.columns.tolist())
    st.write("**Primeras 5 filas:**")
    st.dataframe(df.head())
    st.write("**Información básica:**")
    st.write(f"Total de registros: {len(df):,}")
    st.write(f"Total de columnas: {len(df.columns)}")

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
    st.sidebar.warning("⚠️ No se encontró columna 'estado_usuaria'")
    st.sidebar.write("Columnas disponibles:", df.columns.tolist())
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
    st.sidebar.info("ℹ️ No se encontró columna 'municipio_usuaria'")
    df_selection = df_filtrado_estado

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Total Reportes", f"{len(df_selection):,}")

if 'edad' in df.columns:
    # Convertir edad a numérico
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

# ==================== GRÁFICA 1: DISTRIBUCIÓN POR OCUPACIÓN ====================
c1, c2 = st.columns([2,1])

with c1:
    st.subheader("Distribución por Ocupación")
    if 'ocupacion' in df.columns:
        df_ocupacion = df_selection['ocupacion'].dropna()
        if len(df_ocupacion) > 0:
            # Limitar a top 10 para mejor visualización
            top_ocupaciones = df_ocupacion.value_counts().head(10)
            fig_ocupacion = px.pie(values=top_ocupaciones.values, 
                                   names=top_ocupaciones.index, 
                                   hole=0.6,
                                   title="Top 10 Ocupaciones",
                                   color_discrete_sequence=["#E6CCFF","#D8B4FE","#C084FC","#A855F7","#9333EA","#7E22CE"])
            fig_ocupacion.update_layout(width=WIDTH, height=HEIGHT)
            st.plotly_chart(fig_ocupacion, use_container_width=False)
        else:
            st.info("No hay datos de ocupación disponibles")
    else:
        st.info("Columna 'ocupacion' no encontrada en los datos")

with c2:
    st.subheader("Análisis gráfico")
    st.write("""
    - La gráfica muestra la distribución de las ocupaciones de las usuarias.
    - Se observa qué grupos ocupacionales tienen mayor presencia.
    - Las porciones más grandes indican los sectores con más casos.
    - Permite focalizar campañas de prevención en sectores específicos.
    """)

# ==================== GRÁFICA 2: ATENCIONES POR MES ====================
c3, c4 = st.columns([2,1])

with c3:
    st.subheader("Atenciones por Mes")
    if 'mes_alta' in df.columns:
        mes_counts = df_selection['mes_alta'].value_counts().reset_index()
        mes_counts.columns = ['mes', 'total']
        mes_counts = mes_counts.sort_values(by='mes')
        fig_mes = px.bar(mes_counts, x='mes', y='total',
            labels={'mes': 'Mes del Año', 'total': 'Número de llamadas'},
            color_discrete_sequence=['#9333EA'])
        fig_mes.update_layout(width=WIDTH, height=HEIGHT)
        st.plotly_chart(fig_mes, use_container_width=False)
    else:
        st.info("Columna 'mes_alta' no encontrada en los datos")

with c4:
    st.subheader("Análisis gráfico")
    st.write("""
    - Muestra la distribución de llamadas por mes del año.
    - Identifica meses con mayor y menor número de reportes.
    - Permite planificar recursos según la demanda estacional.
    """)

# ==================== GRÁFICA 3: DISTRIBUCIÓN DE EDADES ====================
c5, c6 = st.columns([2,1])

with c5:
    st.subheader("Distribución de Edades")
    if 'edad' in df.columns:
        bins = st.slider("Número de intervalos (bins)", 5, 50, 20, key="bins_edad")
        df_edad = df_selection['edad'].dropna()
        if len(df_edad) > 0:
            fig_edad = px.histogram(df_edad, x="edad", nbins=bins,
                title="Distribución de Edades de las Usuarias", 
                color_discrete_sequence=['#FFA200'],
                labels={'edad': 'Edad', 'count': 'Número de casos'})
            fig_edad.update_layout(width=WIDTH, height=HEIGHT)
            st.plotly_chart(fig_edad, use_container_width=False)
        else:
            st.info("No hay datos de edad disponibles")
    else:
        st.info("Columna 'edad' no encontrada en los datos")

with c6:
    st.subheader("Análisis gráfico")
    st.write("""
    - Muestra la concentración de edades de las usuarias.
    - La mayoría se concentra entre los 30 y 50 años.
    - Menos casos en edades extremas.
    """)

# ==================== GRÁFICA 4: FRECUENCIA POR ESTADO CIVIL ====================
c7, c8 = st.columns([2,1])

with c7:
    if 'estado_civil' in df.columns:
        st.subheader("Frecuencia por estado civil")
        conteo_ec = df_selection['estado_civil'].value_counts().reset_index()
        conteo_ec.columns = ['estado_civil', 'total']
        fig_ec = px.bar(conteo_ec, x='estado_civil', y='total', 
                       color_discrete_sequence=["#9333EA"],
                       title="Estado Civil de las Usuarias")
        fig_ec.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=45)
        st.plotly_chart(fig_ec, use_container_width=False)
    else:
        st.info("Columna 'estado_civil' no encontrada en los datos")

with c8:
    st.subheader("Análisis gráfico")
    st.write("""
    - Distribución por estado civil de las mujeres que reportan.
    - Permite identificar patrones según el estado civil.
    - Ayuda a entender el contexto familiar.
    """)

# ==================== GRÁFICA 5: EVOLUCIÓN TEMPORAL ====================
c9, c10 = st.columns([2,1])

with c9:
    st.subheader("Evolución temporal de llamadas")
    if 'fecha_alta' in df.columns:
        df_temp = df.copy()
        df_temp['fecha_alta'] = pd.to_datetime(df_temp['fecha_alta'], errors='coerce')
        df_temp = df_temp.dropna(subset=['fecha_alta'])
        df_temp['anio_mes'] = df_temp['fecha_alta'].dt.to_period('M').astype(str)
        llamadas_por_mes = df_temp.groupby('anio_mes').size().reset_index()
        llamadas_por_mes.columns = ['anio_mes', 'total']
        fig_ev = px.line(llamadas_por_mes, x='anio_mes', y='total', markers=True,
                        title="Evolución Mensual de Llamadas")
        fig_ev.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=90)
        st.plotly_chart(fig_ev, use_container_width=False)
    else:
        st.info("Columna 'fecha_alta' no encontrada en los datos")

with c10:
    st.subheader("Análisis gráfico")
    st.write("""
    - Evolución de las llamadas a lo largo del tiempo.
    - Identifica tendencias y evalua el impacto de intervenciones.
    - Los picos indican períodos de mayor demanda.
    """)

# ==================== ANÁLISIS DE TEMÁTICAS ====================
st.header("Análisis de Temáticas")

# Detectar columnas de temáticas
columnas_tematicas = ['tematica_1', 'tematica_2', 'tematica_3', 'tematica_4', 'tematica_5', 'tematica_6', 'tematica_7']
tematicas_existentes = [col for col in columnas_tematicas if col in df.columns]

if tematicas_existentes:
    # Crear versión expandida para análisis
    df_temp = df_selection.copy()
    for col in tematicas_existentes:
        df_temp[col] = df_temp[col].fillna('No especificado')
    
    df_temp['tematicas_lista'] = df_temp[tematicas_existentes].apply(lambda x: x.tolist(), axis=1)
    df_exploded = df_temp.explode('tematicas_lista')
    df_exploded = df_exploded[df_exploded['tematicas_lista'] != 'No especificado']
    df_exploded = df_exploded.rename(columns={'tematicas_lista': 'tematica'})
    
    # GRÁFICA: TOP TEMÁTICAS
    c_tem1, c_tem2 = st.columns([2,1])
    
    with c_tem1:
        st.subheader("Top 15 temáticas más reportadas")
        
        top_tematicas = df_exploded['tematica'].value_counts().head(15)
        
        if len(top_tematicas) > 0:
            fig_top_tematicas = px.bar(
                x=top_tematicas.values, 
                y=top_tematicas.index,
                orientation='h',
                labels={'x': 'Número de casos', 'y': 'Temática'},
                color=top_tematicas.values,
                color_continuous_scale='Purples_r',
                title="Problemáticas Más Frecuentes"
            )
            fig_top_tematicas.update_layout(width=WIDTH, height=HEIGHT, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_top_tematicas, use_container_width=False)
        else:
            st.info("No hay datos de temáticas disponibles")
    
    with c_tem2:
        st.subheader("Análisis gráfico")
        st.write("""
        - Las 15 problemáticas más frecuentes reportadas.
        - Las barras más largas representan los problemas más comunes.
        - Las primeras temáticas deben ser prioridad de atención.
        """)
else:
    st.info("No se encontraron columnas de temáticas en los datos")

# ==================== CUESTIONARIO ====================
st.markdown("---")
st.header("Encuesta")
st.title("Cuéntanos qué fue lo que sucedió ese día")
st.markdown("Responde lo más sincera posible")

with st.form(key="cuestionario_form"):
    edad_grupo = st.selectbox(
        "¿Qué edad tienes?",
        ["Menor de 10", "10-15", "15-25", "25-35", "35-45", "Mayor de 45"]
    )
    
    situacion = st.selectbox(
        "¿Has experimentado alguna situación?",
        ["Abuso sexual", "Violencia Familiar", "Abuso de confianza", "Violación en la escuela o trabajo", "Otros"]
    )
    
    frecuencia = st.selectbox(
        "¿Con qué frecuencia ocurre?",
        ["Ocurrió una vez", "De vez en cuando", "Frecuentemente", "Me está pasando ahora"]
    )
    
    relacion = st.selectbox(
        "Relación con la persona",
        ["Pareja", "Familiar", "Trabajo", "Otro"]
    )
    
    hablado_alguien = st.selectbox(
        "¿Has hablado con alguien?",
        ["Sí", "No"]
    )
    
    submitted = st.form_submit_button("Enviar")
    
    if submitted:
        datos_respuesta = {
            'edad_grupo': edad_grupo,
            'situacion': situacion,
            'frecuencia': frecuencia,
            'relacion': relacion,
            'hablado_alguien': hablado_alguien
        }
        
        if guardar_respuesta(datos_respuesta):
            st.success("¡Gracias por tu confianza! Tu respuesta ha sido guardada.")
            st.balloons()
        else:
            st.error("Hubo un error al guardar tu respuesta. Por favor, intenta de nuevo.")

if st.button("Necesitas ayuda"):
    st.warning("""Llama al: 800 10 84 053 o 079  Recuerda no estas sola. Puedes acudar a las siguientes sedes, no tengas miedo de hablar: 
Secretaría de las Mujeres
Prolongación Corregidora Sur 210, 76074 Querétaro
442 215 3404         
Secretaría de la Mujer del Municipio de Querétaro
Galaxia 543, 76085 Santiago de Querétaro, Querétaro
442 238 7700
Secretaría Municipal de la Mujer Corregidora Querétaro
Calle Monterrey, 76902 Corregidora, Querétaro""")

df_respuestas = cargar_respuestas_cuestionario()
if not df_respuestas.empty:
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Estadísticas del Cuestionario")
    st.sidebar.metric("Respuestas recibidas", len(df_respuestas))
    st.sidebar.metric("Última respuesta", df_respuestas['fecha'].max().split()[0] if not df_respuestas.empty else "N/A")
