import streamlit as st

st.set_page_config(page_title="Test", layout="wide")

st.title("Test de funcionamiento")
st.write("Si ves este mensaje, Streamlit está funcionando correctamente")

# Verificar que podemos importar pandas
try:
    import pandas as pd
    st.success("✅ Pandas importado correctamente")
except:
    st.error("❌ Error con pandas")

# Verificar archivos
import os
st.write("Archivos en el directorio:")
for file in os.listdir('.'):
    st.write(f"- {file}")
