import streamlit as st
from PIL import Image

st.set_page_config(
    page_title="RRC - Scouting Porteros",
    page_icon="🧤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Logo en sidebar - usando st.logo para que aparezca arriba de todo
try:
    st.logo("real_racing_club.png")
except:
    pass

# CSS para centrar y agrandar el logo
st.markdown("""
<style>
    [data-testid="stSidebarNav"] {
        padding-top: 0rem;
    }
    [data-testid="stSidebarUserContent"] {
        padding-top: 1rem;
    }
    /* Agrandar el logo */
    [data-testid="stLogo"] {
        width: 500px !important;
        height: auto !important;
    }
    [data-testid="stLogo"] img {
        width: 500px !important;
        height: auto !important;
    }
</style>
""", unsafe_allow_html=True)

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
