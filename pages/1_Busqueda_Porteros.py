import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Búsqueda Porteros", page_icon="🔍", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('CONSOLIDADO_metricas_por_90.csv')
    diccionario = pd.read_excel('diccionario_metricas_porteros.xlsx')
    return df, diccionario

df, diccionario = load_data()

st.title("🔍 Búsqueda de Porteros")

# Crear diccionario de mapeo de nombres
nombre_map = dict(zip(diccionario['metrica'], diccionario['nombre_limpio']))

# Columnas base que siempre se muestran
columnas_base = ['jugador', 'TeamName', 'Competencia', 'Temporada', 'minutos_totales']

# Obtener métricas del diccionario (solo las que están en el dataset)
metricas_disponibles = [col for col in diccionario['metrica'].tolist() if col in df.columns]

# FILTROS
st.sidebar.header("Filtros")

# Filtro de minutos totales
min_minutos = int(df['minutos_totales'].min())
max_minutos = int(df['minutos_totales'].max())
minutos_range = st.sidebar.slider(
    "Minutos Totales Jugados",
    min_value=min_minutos,
    max_value=max_minutos,
    value=(min_minutos, max_minutos)
)

# Filtro de competencias
competencias_disponibles = sorted(df['Competencia'].unique())
competencias_seleccionadas = st.sidebar.multiselect(
    "Competencias",
    options=competencias_disponibles,
    default=[]
)

# Filtro de temporadas
temporadas_disponibles = sorted(df['Temporada'].unique(), reverse=True)
temporadas_seleccionadas = st.sidebar.multiselect(
    "Temporadas",
    options=temporadas_disponibles,
    default=[]
)

# Aplicar filtros
df_filtrado = df.copy()

# Filtro de minutos
df_filtrado = df_filtrado[
    (df_filtrado['minutos_totales'] >= minutos_range[0]) & 
    (df_filtrado['minutos_totales'] <= minutos_range[1])
]

# Filtro de competencias (si hay selección)
if competencias_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Competencia'].isin(competencias_seleccionadas)]

# Filtro de temporadas (si hay selección)
if temporadas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Temporada'].isin(temporadas_seleccionadas)]

# Mostrar contador de resultados
st.info(f"📊 Mostrando {len(df_filtrado)} porteros de {len(df)} totales")

# Preparar dataframe para mostrar
columnas_a_mostrar = columnas_base + metricas_disponibles
df_display = df_filtrado[columnas_a_mostrar].copy()

# Resetear índice para evitar problemas con índices duplicados
df_display = df_display.reset_index(drop=True)

# Renombrar columnas según diccionario
rename_dict = {
    'jugador': 'Jugador',
    'TeamName': 'Equipo',
    'Competencia': 'Competencia',
    'Temporada': 'Temporada',
    'minutos_totales': 'Minutos Totales'
}

# Agregar nombres limpios de métricas - asegurándose de que no haya duplicados
contador_nombres = {}
for metrica in metricas_disponibles:
    if metrica in nombre_map:
        nombre_limpio = nombre_map[metrica]
        # Contar cuántas veces aparece este nombre
        if nombre_limpio not in contador_nombres:
            contador_nombres[nombre_limpio] = 0
        else:
            contador_nombres[nombre_limpio] += 1
            # Si es duplicado, agregar un sufijo numérico
            nombre_limpio = f"{nombre_limpio} ({contador_nombres[nombre_limpio]})"
        rename_dict[metrica] = nombre_limpio
    else:
        # Si no está en el diccionario, usar el nombre original
        rename_dict[metrica] = metrica

df_display = df_display.rename(columns=rename_dict)

# Debug: Verificar duplicados
duplicated_cols = df_display.columns[df_display.columns.duplicated()].tolist()
if duplicated_cols:
    st.error(f"Columnas duplicadas detectadas: {duplicated_cols}")
    st.write("Todas las columnas:", df_display.columns.tolist())
    # Hacer nombres únicos agregando sufijos
    df_display.columns = pd.Index([f"{col}_{i}" if df_display.columns.tolist().count(col) > 1 and i > 0 else col 
                                     for i, col in enumerate(df_display.columns)])
    st.info("Columnas renombradas para hacerlas únicas")

# Formatear columnas de porcentaje (las que empiezan con pct_)
def format_dataframe(df):
    df_formatted = df.copy()
    
    for col in df_filtered.columns:
        # Buscar la métrica original
        metrica_original = None
        for k, v in rename_dict.items():
            if v == col:
                metrica_original = k
                break
        
        # Si es una columna de porcentaje, formatear
        if metrica_original and metrica_original.startswith('pct_'):
            df_formatted[col] = df_formatted[col].apply(
                lambda x: f"{x*100:.2f}%" if pd.notna(x) else ""
            )
    
    return df_formatted

# Aplicar gradiente de color
def apply_gradient(df):
    # Asegurarse de que el índice sea único
    if not df.index.is_unique:
        df = df.reset_index(drop=True)
    
    # Identificar columnas numéricas (excluyendo las ya formateadas como string de %)
    numeric_cols = []
    for col in df.columns:
        if col not in ['Jugador', 'Equipo', 'Competencia', 'Temporada']:
            # Buscar la métrica original
            metrica_original = None
            for k, v in rename_dict.items():
                if v == col:
                    metrica_original = k
                    break
            
            # Solo agregar columnas numéricas que no sean porcentajes (ya formateados)
            if metrica_original and not metrica_original.startswith('pct_'):
                if pd.api.types.is_numeric_dtype(df[col]):
                    numeric_cols.append(col)
    
    # Aplicar gradiente solo a columnas numéricas
    if numeric_cols:
        return df.style.background_gradient(
            cmap='RdYlGn',
            subset=numeric_cols,
            vmin=None,
            vmax=None
        )
    else:
        return df

# Crear copia para filtrado y aplicar formato
df_filtered = df_display.copy()

# Formatear las columnas de porcentaje
for col in df_filtered.columns:
    # Buscar la métrica original
    metrica_original = None
    for k, v in rename_dict.items():
        if v == col:
            metrica_original = k
            break
    
    # Si es una columna de porcentaje, formatear
    if metrica_original and metrica_original.startswith('pct_'):
        df_filtered[col] = df_filtered[col].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else ""
        )

# Aplicar gradiente (solo a columnas numéricas no formateadas)
styled_df = apply_gradient(df_filtered)

# Mostrar tabla
st.dataframe(
    styled_df,
    width='stretch',
    height=600,
    hide_index=True
)

# Opción de descarga
csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar datos filtrados (CSV)",
    data=csv,
    file_name="porteros_filtrados.csv",
    mime="text/csv"
)
