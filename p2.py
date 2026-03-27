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
    
    # Lista de posibles nombres de archivo
    posibles_archivos = [
        "linea-mujeres-cdmx.csv",
        "datos.csv",
        "data.csv",
        "linea_mujeres.csv"
    ]
    
    # Primero buscar archivo CSV normal
    for archivo in posibles_archivos:
        if os.path.exists(archivo):
            try:
                df = pd.read_csv(archivo, encoding="latin1")
                st.success(f"✅ Datos cargados correctamente: {len(df)} registros")
                return df
            except:
                try:
                    df = pd.read_csv(archivo, encoding="utf-8")
                    st.success(f"✅ Datos cargados correctamente: {len(df)} registros")
                    return df
                except:
                    continue
    
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
    st.error("No se pudieron cargar los datos. Por favor verifica los archivos.")
    st.stop()

# ==================== NORMALIZAR Y DETECTAR COLUMNAS ====================
# Convertir todos los nombres de columnas a minúsculas y quitar espacios
df.columns = df.columns.str.lower().str.strip()

# Diccionario de mapeo para columnas comunes
mapeo_columnas = {
    'estado': 'estado_usuaria',
    'estado_usuaria': 'estado_usuaria',
    'estado_usuario': 'estado_usuaria',
    'entidad': 'estado_usuaria',
    'entidad_usuaria': 'estado_usuaria',
    'municipio': 'municipio_usuaria',
    'municipio_usuaria': 'municipio_usuaria',
    'municipio_usuario': 'municipio_usuaria',
    'delegacion': 'municipio_usuaria',
    'alcaldia': 'municipio_usuaria',
    'edad': 'edad',
    'edad_usuaria': 'edad',
    'ocupacion': 'ocupacion',
    'ocupación': 'ocupacion',
    'mes_alta': 'mes_alta',
    'mes': 'mes_alta',
    'servicio': 'servicio',
    'tipo_servicio': 'servicio',
    'escolaridad': 'escolaridad',
    'educacion': 'escolaridad',
    'nivel_educativo': 'escolaridad',
    'estado_civil': 'estado_civil',
    'estadocivil': 'estado_civil',
    'fecha_alta': 'fecha_alta',
    'fecha': 'fecha_alta',
    'fecha_llamada': 'fecha_alta'
}

# Aplicar mapeo de columnas
for col_original, col_nuevo in mapeo_columnas.items():
    if col_original in df.columns and col_nuevo not in df.columns:
        df.rename(columns={col_original: col_nuevo}, inplace=True)

# Buscar columnas de temáticas
for i in range(1, 8):
    posibles_nombres = [f'tematica_{i}', f'temática_{i}', f'tema_{i}', f'problematica_{i}', f'violencia_{i}']
    for nombre in posibles_nombres:
        if nombre in df.columns and f'tematica_{i}' not in df.columns:
            df.rename(columns={nombre: f'tematica_{i}'}, inplace=True)

# ==================== FUNCIONES DE VERIFICACIÓN DE COLUMNAS ====================
def get_column(col_name, alternativas):
    """Obtiene el nombre real de la columna si existe"""
    for alt in alternativas:
        if alt in df.columns:
            return alt
    return None

# ==================== FILTROS ====================
st.sidebar.header("Filtros")

# Detectar columna de estado
col_estado = get_column('estado_usuaria', ['estado_usuaria', 'estado', 'entidad', 'estado_usuario'])
if col_estado:
    estados_disponibles = df[col_estado].dropna().unique()
    estado = st.sidebar.multiselect(
        "Selecciona Estado:",
        options=sorted(estados_disponibles),
        default=sorted(estados_disponibles)[:3] if len(estados_disponibles) > 3 else sorted(estados_disponibles)
    )
    
    if estado:
        df_filtrado_estado = df[df[col_estado].isin(estado)]
    else:
        df_filtrado_estado = df
else:
    st.sidebar.warning("⚠️ No se encontró columna de estado")
    df_filtrado_estado = df

# Detectar columna de municipio
col_municipio = get_column('municipio_usuaria', ['municipio_usuaria', 'municipio', 'delegacion', 'alcaldia', 'ciudad'])
if col_municipio:
    municipios_disponibles = df_filtrado_estado[col_municipio].dropna().unique()
    municipio = st.sidebar.multiselect(
        "Selecciona Municipio:",
        options=sorted(municipios_disponibles),
        default=sorted(municipios_disponibles)[:5] if len(municipios_disponibles) > 5 else sorted(municipios_disponibles)
    )
    
    if municipio:
        df_selection = df_filtrado_estado[df_filtrado_estado[col_municipio].isin(municipio)]
    else:
        df_selection = df_filtrado_estado
else:
    st.sidebar.info("ℹ️ No se encontró columna de municipio")
    df_selection = df_filtrado_estado

# Métricas
col1, col2, col3 = st.columns(3)
col1.metric("Total Reportes", f"{len(df_selection):,}")

if 'edad' in df.columns:
    edad_promedio = pd.to_numeric(df_selection['edad'], errors='coerce').mean()
    col2.metric("Edad Promedio", f"{edad_promedio:.0f}" if not pd.isna(edad_promedio) else "N/A")
else:
    col2.metric("Edad Promedio", "No disponible")

if col_municipio and municipio:
    col3.metric("Municipios Seleccionados", f"{len(municipio)}")
elif col_municipio:
    col3.metric("Municipios Totales", f"{len(df_selection[col_municipio].unique())}")
else:
    col3.metric("Municipios", "No disponible")

# ==================== GRÁFICA 1: DISTRIBUCIÓN POR OCUPACIÓN ====================
c1, c2 = st.columns([2,1])

with c1:
    st.subheader("Distribución por Ocupación")
    if 'ocupacion' in df.columns:
        # Limpiar datos nulos
        df_ocupacion = df_selection['ocupacion'].dropna()
        if len(df_ocupacion) > 0:
            fig_ocupacion = px.pie(values=df_ocupacion.value_counts().values, 
                                   names=df_ocupacion.value_counts().index, 
                                   hole=0.6,
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
    - La gráfica muestra la distribución de las ocupaciones de las usuarias que realizaron llamadas.
    - Se observa qué grupos ocupacionales tienen mayor presencia en los reportes.
    - Las porciones más grandes indican los sectores laborales con más casos.
    - Esto permite focalizar campañas de prevención en sectores específicos.
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
    - La gráfica muestra la distribución de llamadas por cada mes del año.
    - Se identifican los meses con mayor y menor número de reportes.
    - Los picos más altos indican épocas de mayor demanda de atención.
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
                title="Distribución de Edades de las Usuarias", color_discrete_sequence=['#FFA200'])
            fig_edad.update_layout(width=WIDTH, height=HEIGHT)
            st.plotly_chart(fig_edad, use_container_width=False)
        else:
            st.info("No hay datos de edad disponibles")
    else:
        st.info("Columna 'edad' no encontrada en los datos")

with c6:
    st.subheader("Análisis gráfico")
    st.write("""
    - La gráfica muestra la concentración de edades de las usuarias que reportan.
    - Se observa que la mayoría de las personas se concentran entre los 30 y 50 años.
    - Hay menos casos en edades muy jóvenes y en edades muy avanzadas.
    - El núcleo más fuerte está en edades medias, los extremos son poco frecuentes.
    """)

# ==================== GRÁFICA 4: FRECUENCIA POR ESTADO CIVIL ====================
c7, c8 = st.columns([2,1])

with c7:
    if 'estado_civil' in df.columns:
        st.subheader("Frecuencia por estado civil")
        conteo_ec = df_selection['estado_civil'].value_counts().reset_index()
        conteo_ec.columns = ['estado_civil', 'total']
        fig_ec = px.bar(conteo_ec, x='estado_civil', y='total', color_discrete_sequence=["#9333EA"])
        fig_ec.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=45)
        st.plotly_chart(fig_ec, use_container_width=False)
    else:
        st.info("Columna 'estado_civil' no encontrada en los datos")

with c8:
    st.subheader("Análisis gráfico")
    st.write("""
    - La gráfica muestra la distribución por estado civil de las mujeres que reportan.
    - Permite identificar patrones según el estado civil.
    - Ayuda a entender el contexto familiar de las usuarias.
    """)

# ==================== GRÁFICA 5: EVOLUCIÓN MENSUAL DE LLAMADAS ====================
c9, c10 = st.columns([2,1])

with c9:
    st.subheader("Evolución mensual de llamadas")
    if 'fecha_alta' in df.columns:
        df_temp = df.copy()
        df_temp['fecha_alta'] = pd.to_datetime(df_temp['fecha_alta'], errors='coerce')
        df_temp = df_temp.dropna(subset=['fecha_alta'])
        df_temp['anio_mes'] = df_temp['fecha_alta'].dt.to_period('M').astype(str)
        llamadas_por_mes = df_temp.groupby('anio_mes').size().reset_index()
        llamadas_por_mes.columns = ['anio_mes', 'total']
        fig_ev = px.line(llamadas_por_mes, x='anio_mes', y='total', markers=True)
        fig_ev.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=90)
        st.plotly_chart(fig_ev, use_container_width=False)
    else:
        st.info("Columna 'fecha_alta' no encontrada en los datos")

with c10:
    st.subheader("Análisis gráfico")
    st.write("""
    - La gráfica muestra la evolución de las llamadas a lo largo del tiempo.
    - Permite identificar tendencias y evaluar el impacto de intervenciones.
    - Los picos indican períodos de mayor demanda.
    """)

# ==================== GRÁFICA 6: CLUSTERS EDAD VS SERVICIO ====================
c11, c12 = st.columns([2,1])

with c11:
    st.subheader("Clusters de llamadas")
    if 'edad' in df.columns and 'servicio' in df.columns:
        # Seleccionar solo columnas numéricas
        df_num = df.select_dtypes(include=['int64','float64']).fillna(df.select_dtypes(include=['int64','float64']).median())
        if len(df_num.columns) > 0:
            scaler = StandardScaler()
            datos_escalados = scaler.fit_transform(df_num)
            kmeans = KMeans(n_clusters=3, random_state=42)
            df['cluster'] = kmeans.fit_predict(datos_escalados)
            
            fig_cl = px.scatter(df, x='edad', y='servicio', color='cluster', 
                               color_continuous_scale='viridis',
                               title="Clusters: Edad vs Servicio")
            fig_cl.update_layout(width=WIDTH, height=HEIGHT)
            st.plotly_chart(fig_cl, use_container_width=False)
        else:
            st.info("No hay suficientes datos numéricos para clustering")
    else:
        st.info("Columnas 'edad' y/o 'servicio' no encontradas")

with c12:
    st.subheader("Análisis gráfico")
    st.write("""
    - El eje horizontal indica la edad de las mujeres que llamaron.
    - El eje vertical indica el tipo de asesoría requerida.
    - Los puntos representan las llamadas y el color indica el grupo.
    - Permite identificar patrones de servicio según rangos de edad.
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
    
    # Crear grupos de edad si existe la columna edad
    if 'edad' in df.columns:
        df_exploded['edad'] = pd.to_numeric(df_exploded['edad'], errors='coerce')
        df_exploded['grupo_edad'] = pd.cut(
            df_exploded['edad'],
            bins=[0, 18, 25, 35, 45, 100],
            labels=['<18 años', '18-25 años', '26-35 años', '36-45 años', '>45 años']
        )
    
    # GRÁFICA 7: TOP 15 TEMÁTICAS MÁS REPORTADAS
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
                color_continuous_scale='Purples_r'
            )
            fig_top_tematicas.update_layout(width=WIDTH, height=HEIGHT, yaxis=dict(autorange="reversed"))
            st.plotly_chart(fig_top_tematicas, use_container_width=False)
        else:
            st.info("No hay datos de temáticas disponibles")
    
    with c_tem2:
        st.subheader("Análisis gráfico")
        st.write("""
        - La gráfica muestra las 15 problemáticas más frecuentes reportadas por las usuarias.
        - Las barras más largas y de color morado más oscuro representan los problemas más comunes.
        - Se observa una clara concentración en las primeras 3-4 temáticas.
        - La temática con mayor número de casos debe ser la principal atención.
        """)
    
    # GRÁFICA 8: DISTRIBUCIÓN DE TEMÁTICAS POR GRUPO DE EDAD
    if 'grupo_edad' in df_exploded.columns:
        c_tem3, c_tem4 = st.columns([2,1])
        
        with c_tem3:
            st.subheader("Distribución de temáticas por grupo de edad")
            
            # Seleccionar top 8 temáticas
            top8 = df_exploded['tematica'].value_counts().head(8).index
            df_top8 = df_exploded[df_exploded['tematica'].isin(top8)]
            
            if len(df_top8) > 0:
                # Crear tabla de contingencia
                edad_tematica = pd.crosstab(df_top8['tematica'], df_top8['grupo_edad'])
                
                # Colores de morado para grupos de edad
                colores_morados = ['#4A0E4E', '#6B2E6B', '#8B4B8B', '#AA6EAA', '#C999C9']
                
                fig_tematica_edad = px.bar(
                    edad_tematica,
                    labels={'value': 'Número de casos', 'tematica': 'Temática', 'variable': 'Grupo de Edad'},
                    color_discrete_sequence=colores_morados,
                    barmode='stack'
                )
                fig_tematica_edad.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=45)
                st.plotly_chart(fig_tematica_edad, use_container_width=False)
            else:
                st.info("No hay suficientes datos para este análisis")
        
        with c_tem4:
            st.subheader("Análisis gráfico")
            st.write("""
            - La gráfica muestra cómo se distribuyen las problemáticas según la edad de las usuarias.
            - El color morado más oscuro representa al grupo de menor edad (<18 años).
            - El color morado más claro representa al grupo de mayor edad (>45 años).
            - Permite identificar qué problemáticas afectan más a cada grupo etario.
            """)

else:
    st.warning("No se encontraron columnas de temáticas en los datos")

# ==================== ANÁLISIS DE ESCOLARIDAD ====================
st.header("Análisis de Escolaridad")

if 'escolaridad' in df.columns:
    # Preparar datos de temáticas para análisis con escolaridad
    if tematicas_existentes:
        df_temp_esc = df_selection.copy()
        for col in tematicas_existentes:
            df_temp_esc[col] = df_temp_esc[col].fillna('No especificado')
        
        df_temp_esc['tematicas_lista'] = df_temp_esc[tematicas_existentes].apply(lambda x: x.tolist(), axis=1)
        df_exploded_esc = df_temp_esc.explode('tematicas_lista')
        df_exploded_esc = df_exploded_esc[df_exploded_esc['tematicas_lista'] != 'No especificado']
        df_exploded_esc = df_exploded_esc.rename(columns={'tematicas_lista': 'tematica'})
    else:
        df_exploded_esc = df_selection.copy()
    
    # GRÁFICA 9: ESCOLARIDAD VS TIPO DE VIOLENCIA
    c_esc1, c_esc2 = st.columns([2,1])
    
    with c_esc1:
        st.subheader("Escolaridad vs Tipo de Violencia")
        
        if 'tematica' in df_exploded_esc.columns:
            # Crear tabla de contingencia
            escolaridad_violencia = pd.crosstab(df_exploded_esc['tematica'], df_exploded_esc['escolaridad'])
            
            # Seleccionar top 10 temáticas
            top10_esc = escolaridad_violencia.sum(axis=1).sort_values(ascending=False).head(10).index
            escolaridad_violencia_top = escolaridad_violencia.loc[top10_esc]
            
            if len(escolaridad_violencia_top) > 0:
                # Heatmap
                fig_esc_viol = px.imshow(
                    escolaridad_violencia_top,
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale='Purples',
                    title="Relación: Escolaridad vs Tipo de Violencia",
                    labels={'x': 'Nivel Educativo', 'y': 'Tipo de Violencia', 'color': 'Número de casos'}
                )
                fig_esc_viol.update_layout(width=WIDTH, height=HEIGHT)
                st.plotly_chart(fig_esc_viol, use_container_width=False)
            else:
                st.info("No hay suficientes datos para este análisis")
        else:
            st.info("No hay datos de temáticas para este análisis")
    
    with c_esc2:
        st.subheader("Análisis gráfico")
        st.write("""
        - La gráfica muestra qué tipos de violencia son más comunes según el nivel educativo.
        - Los colores más oscuros indican mayor concentración de casos.
        - Permite identificar patrones según el nivel educativo.
        - Ayuda a diseñar campañas de prevención adaptadas.
        """)
    
    # GRÁFICA 10: ESTADO CIVIL POR NIVEL EDUCATIVO
    if 'estado_civil' in df.columns:
        c_esc3, c_esc4 = st.columns([2,1])
        
        with c_esc3:
            st.subheader("Estado civil por nivel educativo")
            
            escolaridad_estado = pd.crosstab(df_selection['escolaridad'], df_selection['estado_civil'])
            
            if len(escolaridad_estado) > 0:
                fig_esc_estado = px.bar(
                    escolaridad_estado,
                    barmode='stack',
                    title="Estado Civil por Nivel Educativo",
                    labels={'value': 'Número de casos', 'escolaridad': 'Nivel Educativo', 'variable': 'Estado Civil'},
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_esc_estado.update_layout(width=WIDTH, height=HEIGHT, xaxis_tickangle=45)
                st.plotly_chart(fig_esc_estado, use_container_width=False)
            else:
                st.info("No hay suficientes datos para este análisis")
        
        with c_esc4:
            st.subheader("Análisis gráfico")
            st.write("""
            - La gráfica muestra la distribución de estados civiles según el nivel educativo.
            - Permite identificar patrones socio-familiares según nivel de estudios.
            - Ayuda a entender el contexto de las usuarias.
            """)

else:
    st.warning("No se encontró la columna 'escolaridad' en los datos")

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
