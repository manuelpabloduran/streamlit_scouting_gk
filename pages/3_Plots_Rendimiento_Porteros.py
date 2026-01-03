import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Plots Rendimiento", page_icon="📊", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('CONSOLIDADO_metricas_por_90.csv')
    diccionario = pd.read_excel('diccionario_metricas_porteros.xlsx')
    return df, diccionario

df, diccionario = load_data()

st.title("📊 Plots de Rendimiento de Porteros")

# Crear diccionario de mapeo de nombres
nombre_map = dict(zip(diccionario['metrica'], diccionario['nombre_limpio']))
nombre_map_inverso = dict(zip(diccionario['nombre_limpio'], diccionario['metrica']))

# Obtener métricas numéricas del diccionario
metricas_disponibles = [col for col in diccionario['metrica'].tolist() if col in df.columns]

# Filtrar solo métricas numéricas positivas para tamaño y color
metricas_numericas_positivas = []
for metrica in metricas_disponibles:
    if pd.api.types.is_numeric_dtype(df[metrica]):
        # Verificar que todos los valores sean positivos o cero
        if (df[metrica] >= 0).all() or (df[metrica].dropna() >= 0).all():
            metricas_numericas_positivas.append(metrica)

# Nombres bonitos para las métricas
nombres_bonitos_todas = [nombre_map.get(m, m) for m in metricas_disponibles]
nombres_bonitos_positivas = [nombre_map.get(m, m) for m in metricas_numericas_positivas]

# CONFIGURACIÓN DEL GRÁFICO
st.sidebar.header("Configuración del Gráfico")

# Variable Eje X
variable_x_nombre = st.sidebar.selectbox(
    "Variable Eje X",
    options=nombres_bonitos_todas,
    index=0
)
variable_x = nombre_map_inverso.get(variable_x_nombre, variable_x_nombre)

# Variable Eje Y
variable_y_nombre = st.sidebar.selectbox(
    "Variable Eje Y",
    options=nombres_bonitos_todas,
    index=min(1, len(nombres_bonitos_todas) - 1)
)
variable_y = nombre_map_inverso.get(variable_y_nombre, variable_y_nombre)

# Variable Tamaño
variable_size_nombre = st.sidebar.selectbox(
    "Variable Tamaño Burbuja",
    options=["Ninguna"] + nombres_bonitos_positivas,
    index=0
)
variable_size = None if variable_size_nombre == "Ninguna" else nombre_map_inverso.get(variable_size_nombre, variable_size_nombre)

# Variable Color
variable_color_nombre = st.sidebar.selectbox(
    "Variable Color Burbuja",
    options=["Ninguna"] + nombres_bonitos_positivas,
    index=0
)
variable_color = None if variable_color_nombre == "Ninguna" else nombre_map_inverso.get(variable_color_nombre, variable_color_nombre)

st.sidebar.markdown("---")
st.sidebar.header("Filtros")

# Filtro de minutos totales
min_minutos = 450
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

# Filtro de competencias
if competencias_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Competencia'].isin(competencias_seleccionadas)]

# Filtro de temporadas
if temporadas_seleccionadas:
    df_filtrado = df_filtrado[df_filtrado['Temporada'].isin(temporadas_seleccionadas)]

# Mostrar contador de resultados
st.info(f"📊 Mostrando {len(df_filtrado)} porteros de {len(df)} totales")

# Preparar datos para el gráfico
df_plot = df_filtrado.copy()

# Crear columna de hover con información del portero
df_plot['hover_info'] = (
    df_plot['jugador'] + '<br>' +
    df_plot['TeamName'] + '<br>' +
    df_plot['Competencia'] + ' - ' + df_plot['Temporada'].astype(str)
)

# Crear el scatter plot
fig = px.scatter(
    df_plot,
    x=variable_x,
    y=variable_y,
    size=variable_size if variable_size else None,
    color=variable_color if variable_color else None,
    hover_name='hover_info',
    hover_data={
        'jugador': True,
        'TeamName': True,
        'Competencia': True,
        'Temporada': True,
        variable_x: ':.2f',
        variable_y: ':.2f',
        'hover_info': False
    },
    labels={
        variable_x: variable_x_nombre,
        variable_y: variable_y_nombre,
        variable_size: variable_size_nombre if variable_size else None,
        variable_color: variable_color_nombre if variable_color else None
    },
    title=f"{variable_y_nombre} vs {variable_x_nombre}",
    template="plotly_white",
    height=700
)

# Personalizar el layout
fig.update_traces(
    marker=dict(
        line=dict(width=0.5, color='DarkSlateGrey'),
        opacity=0.7
    )
)

fig.update_layout(
    xaxis_title=variable_x_nombre,
    yaxis_title=variable_y_nombre,
    font=dict(size=12),
    hovermode='closest',
    plot_bgcolor='rgba(240,240,240,0.5)'
)

# Agregar nombres de colores si hay variable de color
if variable_color:
    fig.update_layout(
        coloraxis_colorbar=dict(
            title=variable_color_nombre
        )
    )

# Mostrar el gráfico
st.plotly_chart(fig, use_container_width=True)

# Tabla resumen debajo del gráfico
st.markdown("---")
st.subheader("Tabla de Datos")

# Preparar columnas para mostrar
columnas_mostrar = ['jugador', 'TeamName', 'Competencia', 'Temporada', 'minutos_totales']

# Agregar variables seleccionadas
if variable_x not in columnas_mostrar:
    columnas_mostrar.append(variable_x)
if variable_y not in columnas_mostrar:
    columnas_mostrar.append(variable_y)
if variable_size and variable_size not in columnas_mostrar:
    columnas_mostrar.append(variable_size)
if variable_color and variable_color not in columnas_mostrar:
    columnas_mostrar.append(variable_color)

df_tabla = df_filtrado[columnas_mostrar].copy()

# Renombrar columnas
rename_dict = {
    'jugador': 'Jugador',
    'TeamName': 'Equipo',
    'Competencia': 'Competencia',
    'Temporada': 'Temporada',
    'minutos_totales': 'Minutos Totales'
}

for col in columnas_mostrar:
    if col in nombre_map and col not in rename_dict:
        rename_dict[col] = nombre_map[col]

df_tabla = df_tabla.rename(columns=rename_dict)

# Formatear columnas numéricas
for col in df_tabla.columns:
    if pd.api.types.is_numeric_dtype(df_tabla[col]) and col not in ['Temporada']:
        df_tabla[col] = df_tabla[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "")

st.dataframe(df_tabla, use_container_width=True, height=400, hide_index=True)

# Opción de descarga
csv = df_filtrado.to_csv(index=False).encode('utf-8')
st.download_button(
    label="📥 Descargar datos filtrados (CSV)",
    data=csv,
    file_name="porteros_plot_filtrados.csv",
    mime="text/csv"
)
