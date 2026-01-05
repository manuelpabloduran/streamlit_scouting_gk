import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="RRC - Scouting Porteros",
    page_icon="🧤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo en sidebar
try:
    logo = Image.open("real_racing_club.png")
    st.sidebar.image(logo, use_container_width=True)
    st.sidebar.markdown("---")
except:
    pass

# Imagen de estadio a lo ancho
try:
    estadio = Image.open("estadio_rrc.jpeg")
    st.image(estadio, use_container_width=True)
except:
    pass

st.title("🧤 Sistema de Scouting de Porteros - Real Racing Club")
st.markdown("""
### Bienvenido al Sistema de Análisis y Scouting de Porteros del Real Racing Club

Utiliza el menú lateral para navegar entre las diferentes secciones:

- **Búsqueda Porteros**: Tabla interactiva con todas las métricas
- **Búsqueda Por Perfil**: Encuentra porteros según perfiles específicos
- **Plots Rendimiento Porteros**: Visualizaciones de rendimiento
- **Comparativa Porteros**: Compara múltiples porteros
- **Perfil Individual**: Análisis detallado de un portero

---
Selecciona una página del menú lateral para comenzar.
""")
