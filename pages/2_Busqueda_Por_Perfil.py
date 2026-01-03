import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Búsqueda Por Perfil", page_icon="🎯", layout="wide")

# Cargar datos
@st.cache_data
def load_data():
    df = pd.read_csv('CONSOLIDADO_metricas_por_90.csv')
    diccionario = pd.read_excel('diccionario_metricas_porteros.xlsx')
    return df, diccionario

@st.cache_data
def calcular_scores(df, diccionario):
    """
    Calcula scores por categoría y global usando percentiles ponderados
    """
    # Cargar ponderaciones por competencia
    try:
        df_pond_comp = pd.read_excel('ponderacion_competencias.xlsx')
        pond_comp_dict = dict(zip(df_pond_comp['Competencia'], df_pond_comp['Ponderacion_Competencia']))
    except:
        pond_comp_dict = {}
    
    df_scores = df[['jugador', 'TeamName', 'Competencia', 'Temporada', 'age', 'height', 'weight', 'minutos_totales']].copy()
    
    # Filtrar solo jugadores con mínimo 450 minutos
    df_trabajo = df[df['minutos_totales'] >= 450].copy()
    
    # Obtener categorías (excluyendo 'Otras')
    categorias = [cat for cat in diccionario['categoria'].dropna().unique() if cat.lower() != 'otras']
    
    # Diccionario para almacenar scores por categoría
    scores_por_categoria = {}
    
    for categoria in categorias:
        # Filtrar métricas de esta categoría
        metricas_cat = diccionario[diccionario['categoria'] == categoria]
        
        score_categoria = pd.Series(0.0, index=df_trabajo.index)
        suma_ponderaciones = 0
        
        for _, row in metricas_cat.iterrows():
            metrica = row['metrica']
            ponderacion = row['Ponderacion'] if pd.notna(row['Ponderacion']) else 1
            invertir = row['Invertir'] if pd.notna(row['Invertir']) else False
            
            # Verificar que la métrica existe en el dataframe
            if metrica not in df_trabajo.columns:
                continue
            
            # Obtener valores de la métrica
            valores = df_trabajo[metrica].copy()
            
            # Skip si todos los valores son NaN
            if valores.isna().all():
                continue
            
            # Invertir si es necesario (mayor valor = peor)
            if invertir:
                valores = -valores
            
            # Calcular percentil (0-100), usando method='average' y manejando NaN
            percentiles = valores.rank(pct=True, method='average', na_option='keep') * 100
            
            # Reemplazar NaN por 0 (jugadores sin datos en esta métrica obtienen score 0)
            percentiles = percentiles.fillna(0)
            
            # Aplicar ponderación
            score_categoria += percentiles * ponderacion
            suma_ponderaciones += ponderacion
        
        # Normalizar por la suma de ponderaciones
        if suma_ponderaciones > 0:
            score_categoria = score_categoria / suma_ponderaciones
        
        # Aplicar ponderación por competencia
        for idx in score_categoria.index:
            competencia = df_trabajo.loc[idx, 'Competencia']
            pond_comp = pond_comp_dict.get(competencia, 1)
            score_categoria.loc[idx] = score_categoria.loc[idx] * pond_comp
        
        # Normalizar a rango 0-100 después de ponderar por competencia
        max_score = score_categoria.max()
        if max_score > 0:
            score_categoria = (score_categoria / max_score) * 100
        
        scores_por_categoria[f'Score_{categoria.replace(" ", "_")}'] = score_categoria
    
    # Calcular score global (promedio de todos los scores de categoría)
    if scores_por_categoria:
        score_global = pd.DataFrame(scores_por_categoria).mean(axis=1)
    else:
        score_global = pd.Series(0.0, index=df_trabajo.index)
    
    scores_por_categoria['Score_Global'] = score_global
    
    # Agregar scores al dataframe original
    for col_name, score_series in scores_por_categoria.items():
        df_scores.loc[score_series.index, col_name] = score_series
    
    # Rellenar NaN con 0 para jugadores con menos de 450 minutos
    score_columns = [col for col in df_scores.columns if col.startswith('Score_')]
    df_scores[score_columns] = df_scores[score_columns].fillna(0)
    
    return df_scores

df, diccionario = load_data()
df_scores = calcular_scores(df, diccionario)

st.title("🎯 Búsqueda Por Perfil")

st.markdown("""
Esta vista muestra porteros con **scores calculados** por categoría y globalmente.
Los scores se basan en percentiles ponderados de las métricas de cada categoría.
""")

# FILTROS
st.sidebar.header("Filtros")

# Filtro de minutos totales
min_minutos = 450
max_minutos = int(df_scores['minutos_totales'].max())
minutos_range = st.sidebar.slider(
    "Minutos Totales Jugados",
    min_value=min_minutos,
    max_value=max_minutos,
    value=(min_minutos, max_minutos)
)

# Filtro de edad
if 'age' in df_scores.columns:
    min_edad = int(df_scores['age'].min())
    max_edad = int(df_scores['age'].max())
    edad_range = st.sidebar.slider(
        "Edad",
        min_value=min_edad,
        max_value=max_edad,
        value=(min_edad, max_edad)
    )

# Filtro de altura
if 'height' in df_scores.columns:
    min_altura = int(df_scores['height'].min())
    max_altura = int(df_scores['height'].max())
    altura_range = st.sidebar.slider(
        "Altura (cm)",
        min_value=min_altura,
        max_value=max_altura,
        value=(min_altura, max_altura)
    )

# Filtro de competencias
competencias_disponibles = sorted(df_scores['Competencia'].unique())
competencias_seleccionadas = st.sidebar.multiselect(
    "Competencias",
    options=competencias_disponibles,
    default=[]
)

# Filtro de temporadas
temporadas_disponibles = sorted(df_scores['Temporada'].unique(), reverse=True)
temporadas_seleccionadas = st.sidebar.multiselect(
    "Temporadas",
    options=temporadas_disponibles,
    default=[]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros de Score")

# Filtro de Score Global
score_global_range = st.sidebar.slider(
    "Score Global",
    min_value=0.0,
    max_value=100.0,
    value=(0.0, 100.0),
    step=1.0
)

# Filtros de Score por Categoría
score_columns = [col for col in df_scores.columns if col.startswith('Score_') and col != 'Score_Global']
score_filters = {}

for score_col in score_columns:
    categoria_nombre = score_col.replace('Score_', '').replace('_', ' ')
    score_filters[score_col] = st.sidebar.slider(
        f"Score {categoria_nombre}",
        min_value=0.0,
        max_value=100.0,
        value=(0.0, 100.0),
        step=1.0
    )

# Aplicar filtros
df_filtrado = df_scores.copy()

# Filtro de minutos
df_filtrado = df_filtrado[
    (df_filtrado['minutos_totales'] >= minutos_range[0]) & 
    (df_filtrado['minutos_totales'] <= minutos_range[1])
]

# Filtro de edad
if 'age' in df_filtrado.columns:
    df_filtrado = df_filtrado[
        (df_filtrado['age'] >= edad_range[0]) & 
        (df_filtrado['age'] <= edad_range[1])
    ]

# Filtro de altura
if 'height' in df_filtrado.columns:
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

# Filtro de Score Global
df_filtrado = df_filtrado[
    (df_filtrado['Score_Global'] >= score_global_range[0]) & 
    (df_filtrado['Score_Global'] <= score_global_range[1])
]

# Filtros de Score por Categoría
for score_col, (min_val, max_val) in score_filters.items():
    df_filtrado = df_filtrado[
        (df_filtrado[score_col] >= min_val) & 
        (df_filtrado[score_col] <= max_val)
    ]

# Mostrar contador de resultados
st.info(f"📊 Mostrando {len(df_filtrado)} porteros de {len(df_scores)} totales")

# Preparar dataframe para mostrar
df_display = df_filtrado.copy()
df_display = df_display.reset_index(drop=True)

# Renombrar columnas
rename_dict = {
    'jugador': 'Jugador',
    'TeamName': 'Equipo',
    'Competencia': 'Competencia',
    'Temporada': 'Temporada',
    'age': 'Edad',
    'height': 'Altura (cm)',
    'weight': 'Peso (kg)',
    'minutos_totales': 'Minutos Totales',
    'Score_Global': 'Score Global'
}

# Renombrar scores de categorías
for col in df_display.columns:
    if col.startswith('Score_') and col != 'Score_Global':
        categoria_nombre = col.replace('Score_', '').replace('_', ' ')
        rename_dict[col] = f'Score {categoria_nombre}'

df_display = df_display.rename(columns=rename_dict)

# Función para aplicar gradiente y formato
def apply_gradient_and_format_scores(df_display_orig, rename_dict):
    df_for_gradient = df_display_orig.copy()
    
    # Identificar columnas de score para gradiente
    score_cols = [col for col in df_for_gradient.columns if col.startswith('Score')]
    
    # Aplicar gradiente a columnas de score
    if score_cols:
        styled = df_for_gradient.style.background_gradient(
            cmap='RdYlGn',
            subset=score_cols,
            vmin=0,
            vmax=100
        )
    else:
        styled = df_for_gradient.style
    
    # Formatear scores a 2 decimales
    format_dict = {}
    for col in score_cols:
        format_dict[col] = "{:.2f}"
    
    styled = styled.format(format_dict, na_rep="")
    return styled

styled_df = apply_gradient_and_format_scores(df_display, rename_dict)

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
    file_name="porteros_scores_filtrados.csv",
    mime="text/csv"
)
