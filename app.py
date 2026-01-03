import streamlit as st

st.set_page_config(
    page_title="Scouting Porteros",
    page_icon="🧤",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🧤 Sistema de Scouting de Porteros")
st.markdown("""
### Bienvenido al Sistema de Análisis y Scouting de Porteros

Utiliza el menú lateral para navegar entre las diferentes secciones:

- **Búsqueda Porteros**: Tabla interactiva con todas las métricas
- **Búsqueda Por Perfil**: Encuentra porteros según perfiles específicos
- **Plots Rendimiento Porteros**: Visualizaciones de rendimiento
- **Comparativa Porteros**: Compara múltiples porteros
- **Perfil Individual**: Análisis detallado de un portero

---
Selecciona una página del menú lateral para comenzar.
""")
