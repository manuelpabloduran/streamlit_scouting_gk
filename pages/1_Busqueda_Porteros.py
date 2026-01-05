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
columnas_base = ['jugador', 'TeamName', 'Competencia', 'Temporada', 'age', 'height', 'weight', 'minutos_totales']

# FILTROS
st.sidebar.header("Filtros")

# Filtro de categorías de métricas
categorias_disponibles = sorted(diccionario['categoria'].dropna().unique())
categorias_seleccionadas = st.sidebar.multiselect(
    "Categorías de Métricas",
    options=categorias_disponibles,
    default=[]
)

# Obtener métricas del diccionario según categorías seleccionadas
if categorias_seleccionadas:
    # Filtrar métricas por categorías seleccionadas
    metricas_disponibles = [
        col for col in diccionario[diccionario['categoria'].isin(categorias_seleccionadas)]['metrica'].tolist() 
        if col in df.columns
    ]
else:
    # Si no hay categorías seleccionadas, mostrar todas
    metricas_disponibles = [col for col in diccionario['metrica'].tolist() if col in df.columns]

# Filtro de minutos totales
min_minutos = 0
max_minutos = int(df['minutos_totales'].max())
minutos_range = st.sidebar.slider(
    "Minutos Totales Jugados",
    min_value=min_minutos,
    max_value=max_minutos,
    value=(min_minutos, max_minutos)
)

# Filtro de edad
if 'age' in df.columns:
    min_edad = int(df['age'].min())
    max_edad = int(df['age'].max())
    edad_range = st.sidebar.slider(
        "Edad",
        min_value=min_edad,
        max_value=max_edad,
        value=(min_edad, max_edad)
    )

# Filtro de altura
if 'height' in df.columns:
    min_altura = int(df['height'].min())
    max_altura = int(df['height'].max())
    altura_range = st.sidebar.slider(
        "Altura (cm)",
        min_value=min_altura,
        max_value=max_altura,
        value=(min_altura, max_altura)
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

# Filtro de edad
if 'age' in df.columns:
    df_filtrado = df_filtrado[
        (df_filtrado['age'] >= edad_range[0]) & 
        (df_filtrado['age'] <= edad_range[1])
    ]

# Filtro de altura
if 'height' in df.columns:
    df_filtrado = df_filtrado[
        (df_filtrado['height'] >= altura_range[0]) & 
        (df_filtrado['height'] <= altura_range[1])
    ]

# Filtro de competencias (si hay selección)
if competencias_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Competencia'].isin(competencias_seleccionadas)]

# Filtro de temporadas (si hay selección)
if temporadas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Temporada'].isin(temporadas_seleccionadas)]

# Guardar cantidad total filtrada
total_filtrados = len(df_filtrado)

# Ordenar por Goles Evitados de mayor a menor
if 'goles_evitados' in df_filtrado.columns:
    df_filtrado = df_filtrado.sort_values(by='goles_evitados', ascending=False)

# Limitar a top 500 para rendimiento
df_filtrado = df_filtrado.head(500)

# Mostrar contador de resultados
if total_filtrados > 500:
    st.info(f"📊 Mostrando el Top 500 de {total_filtrados} porteros que cumplen los filtros (ordenado por Goles Evitados)")
else:
    st.info(f"📊 Mostrando {total_filtrados} porteros de {len(df)} totales")
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
    'age': 'Edad',
    'height': 'Altura (cm)',
    'weight': 'Peso (kg)',
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

# Eliminar columnas duplicadas, manteniendo solo la primera aparición
df_display = df_display.loc[:, ~df_display.columns.duplicated(keep='first')]

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
        
        # Si es una columna de porcentaje, formatear, 'Edad', 'Altura (cm)', 'Peso (kg)'
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
    
    # Identificar columnas numéricas (excluyendo las ya formateadas como string)
    numeric_cols = []
    for col in df.columns:
        if col not in ['Jugador', 'Equipo', 'Competencia', 'Temporada', 'Edad', 'Altura (cm)', 'Peso (kg)']:
            # Buscar la métrica original
            metrica_original = None
            for k, v in rename_dict.items():
                if v == col:
                    metrica_original = k
                    break
            
            # Solo agregar columnas numéricas que no estén ya formateadas como string
            if metrica_original and not metrica_original.startswith('pct_'):
                # Verificar si aún es numérico (antes del formateo a string)
                try:
                    # Como ya están formateadas como string, no aplicamos gradiente a estas
                    # El gradiente solo funciona con valores numéricos
                    pass
                except:
                    pass
    
    # Como las columnas están formateadas como string, no podemos aplicar gradiente
    # Retornar el DataFrame sin estilo
    return df

# Crear copia para filtrado y aplicar formato
df_filtered = df_display.copy()

# Formatear todas las columnas numéricas a 2 decimales y porcentajes
for col in df_filtered.columns:
    # Buscar la métrica original
    metrica_original = None
    for k, v in rename_dict.items():
        if v == col:
            metrica_original = k
            break
    
    # Si es una columna de porcentaje, formatear como porcentaje
    if metrica_original and metrica_original.startswith('pct_'):
        df_filtered[col] = df_filtered[col].apply(
            lambda x: f"{x*100:.2f}%" if pd.notna(x) else ""
        )
    # Si es una columna numérica (no pct_ y no descriptiva), formatear a 2 decimales
    elif col not in ['Jugador', 'Equipo', 'Competencia', 'Temporada', 'Edad', 'Altura (cm)', 'Peso (kg)']:
        if pd.api.types.is_numeric_dtype(df_filtered[col]):
            df_filtered[col] = df_filtered[col].apply(
                lambda x: f"{x:.2f}" if pd.notna(x) else ""
            )

# Aplicar gradiente (antes del formateo a string para que funcione)
# Necesitamos aplicar el gradiente ANTES de formatear a strings
def apply_gradient_and_format(df_display_orig, rename_dict):
    # Primero aplicar gradiente a columnas numéricas sin formatear
    df_for_gradient = df_display_orig.copy()
    
    # Identificar columnas numéricas para el gradiente
    numeric_cols = []
    for col in df_for_gradient.columns:
        if col not in ['Jugador', 'Equipo', 'Competencia', 'Temporada', 'Edad', 'Altura (cm)', 'Peso (kg)']:
            metrica_original = None
            for k, v in rename_dict.items():
                if v == col:
                    metrica_original = k
                    break
            
            if metrica_original and not metrica_original.startswith('pct_'):
                if pd.api.types.is_numeric_dtype(df_for_gradient[col]):
                    numeric_cols.append(col)
    
    # Aplicar el gradiente
    if numeric_cols:
        styled = df_for_gradient.style.background_gradient(
            cmap='RdYlGn',
            subset=numeric_cols
        )
    else:
        styled = df_for_gradient.style
    
    # Ahora aplicar formato de 2 decimales y porcentajes
    format_dict = {}
    for col in df_for_gradient.columns:
        metrica_original = None
        for k, v in rename_dict.items():
            if v == col:
                metrica_original = k
                break
        
        if metrica_original and metrica_original.startswith('pct_'):
            format_dict[col] = lambda x: f"{x*100:.2f}%" if pd.notna(x) else ""
        elif col not in ['Jugador', 'Equipo', 'Competencia', 'Temporada']:
            if pd.api.types.is_numeric_dtype(df_for_gradient[col]):
                format_dict[col] = "{:.2f}"
    
    styled = styled.format(format_dict, na_rep="")
    return styled

styled_df = apply_gradient_and_format(df_display, rename_dict)

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
