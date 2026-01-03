import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Comparativa Porteros", page_icon="⚖️", layout="wide")

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

@st.cache_data
def calcular_percentiles_variables(df, diccionario):
    """
    Calcula percentiles (0-100) para cada métrica disponible
    """
    df_percentiles = df[['jugador', 'TeamName', 'Competencia', 'Temporada', 'minutos_totales']].copy()
    
    # Filtrar solo jugadores con mínimo 450 minutos
    df_trabajo = df[df['minutos_totales'] >= 450].copy()
    
    # Crear mapeo de nombres
    nombre_map = dict(zip(diccionario['metrica'], diccionario['nombre_limpio']))
    
    # Procesar cada métrica del diccionario
    for _, row in diccionario.iterrows():
        metrica = row['metrica']
        nombre_limpio = row['nombre_limpio']
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
        
        # Reemplazar NaN por 0 (jugadores sin datos en esta métrica obtienen percentil 0)
        percentiles = percentiles.fillna(0)
        
        # Agregar al dataframe con el nombre limpio
        col_name = f'Percentil_{nombre_limpio}'
        df_percentiles.loc[percentiles.index, col_name] = percentiles
    
    # Rellenar NaN con 0 para jugadores con menos de 450 minutos
    percentil_columns = [col for col in df_percentiles.columns if col.startswith('Percentil_')]
    df_percentiles[percentil_columns] = df_percentiles[percentil_columns].fillna(0)
    
    return df_percentiles

df, diccionario = load_data()
df_scores = calcular_scores(df, diccionario)
df_percentiles = calcular_percentiles_variables(df, diccionario)

st.title("⚖️ Comparativa de Porteros")

st.markdown("""
Compara porteros usando gráficos de radar. Selecciona jugadores para visualizar sus perfiles y fortalezas.
""")

# Crear identificador único para cada jugador (jugador - temporada - equipo - competencia)
df_scores['id_jugador'] = df_scores['jugador'] + ' - ' + df_scores['Temporada'].astype(str) + ' - ' + df_scores['TeamName'] + ' - ' + df_scores['Competencia']
df_percentiles['id_jugador'] = df_percentiles['jugador'] + ' - ' + df_percentiles['Temporada'].astype(str) + ' - ' + df_percentiles['TeamName'] + ' - ' + df_percentiles['Competencia']

# Filtrar jugadores con mínimo 450 minutos para el selector
df_disponibles = df_scores[df_scores['minutos_totales'] >= 450].copy()
df_disponibles = df_disponibles.sort_values('jugador')

# SELECTOR DE JUGADORES
st.sidebar.header("Selección de Jugadores")
jugadores_opciones = df_disponibles['id_jugador'].tolist()
jugadores_seleccionados = st.sidebar.multiselect(
    "Buscar y seleccionar jugadores",
    options=jugadores_opciones,
    default=[]
)

if len(jugadores_seleccionados) == 0:
    st.info("👈 Selecciona al menos un jugador en el panel lateral para ver la comparativa.")
else:
    # RADAR CHART 1: SCORES POR CATEGORÍA
    st.header("📊 Comparativa de Scores por Categoría")
    
    # Obtener columnas de scores (excluyendo Score_Global)
    score_columns = [col for col in df_scores.columns if col.startswith('Score_') and col != 'Score_Global']
    categorias = [col.replace('Score_', '').replace('_', ' ') for col in score_columns]
    
    # Crear figura de radar
    fig_scores = go.Figure()
    
    # Colores para los jugadores
    colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
    
    for idx, id_jugador in enumerate(jugadores_seleccionados):
        jugador_data = df_scores[df_scores['id_jugador'] == id_jugador].iloc[0]
        
        # Obtener scores de cada categoría
        valores_scores = [jugador_data[col] for col in score_columns]
        score_global = jugador_data['Score_Global']
        
        # Nombre para la leyenda con score global
        nombre_leyenda = f"{jugador_data['jugador']} (Score: {score_global:.1f})"
        
        # Agregar traza al radar
        fig_scores.add_trace(go.Scatterpolar(
            r=valores_scores + [valores_scores[0]],  # Cerrar el polígono
            theta=categorias + [categorias[0]],
            fill='toself',
            name=nombre_leyenda,
            line_color=colores[idx % len(colores)]
        ))
    
    fig_scores.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=600,
        title="Scores por Categoría (0-100)"
    )
    
    st.plotly_chart(fig_scores, use_container_width=True)
    
    # RADAR CHART 2: VARIABLES SELECCIONABLES
    st.markdown("---")
    st.header("📈 Comparativa de Variables Personalizadas")
    
    # Obtener variables disponibles de percentiles
    percentil_columns = [col for col in df_percentiles.columns if col.startswith('Percentil_')]
    variables_disponibles = [col.replace('Percentil_', '') for col in percentil_columns]
    
    # Selector de variables
    variables_seleccionadas = st.multiselect(
        "Selecciona variables a comparar (mínimo 3 para un radar efectivo)",
        options=variables_disponibles,
        default=variables_disponibles[:5] if len(variables_disponibles) >= 5 else variables_disponibles[:3]
    )
    
    if len(variables_seleccionadas) < 3:
        st.warning("⚠️ Selecciona al menos 3 variables para crear un gráfico de radar significativo.")
    else:
        # Crear figura de radar para variables
        fig_variables = go.Figure()
        
        for idx, id_jugador in enumerate(jugadores_seleccionados):
            jugador_data_perc = df_percentiles[df_percentiles['id_jugador'] == id_jugador].iloc[0]
            jugador_data_score = df_scores[df_scores['id_jugador'] == id_jugador].iloc[0]
            
            # Obtener percentiles de cada variable seleccionada
            valores_percentiles = [jugador_data_perc[f'Percentil_{var}'] for var in variables_seleccionadas]
            score_global = jugador_data_score['Score_Global']
            
            # Nombre para la leyenda con score global
            nombre_leyenda = f"{jugador_data_perc['jugador']} (Score: {score_global:.1f})"
            
            # Agregar traza al radar
            fig_variables.add_trace(go.Scatterpolar(
                r=valores_percentiles + [valores_percentiles[0]],  # Cerrar el polígono
                theta=variables_seleccionadas + [variables_seleccionadas[0]],
                fill='toself',
                name=nombre_leyenda,
                line_color=colores[idx % len(colores)]
            ))
        
        fig_variables.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            showlegend=True,
            height=600,
            title="Percentiles por Variable (0-100)"
        )
        
        st.plotly_chart(fig_variables, use_container_width=True)
    
    # TABLA RESUMEN
    st.markdown("---")
    st.subheader("📋 Tabla Resumen de Jugadores Seleccionados")
    
    # Filtrar datos para jugadores seleccionados
    df_tabla = df_scores[df_scores['id_jugador'].isin(jugadores_seleccionados)].copy()
    
    # Seleccionar columnas relevantes
    columnas_tabla = ['jugador', 'TeamName', 'Competencia', 'Temporada', 'age', 'height', 'minutos_totales', 'Score_Global'] + score_columns
    df_tabla = df_tabla[columnas_tabla]
    
    # Renombrar columnas
    rename_dict = {
        'jugador': 'Jugador',
        'TeamName': 'Equipo',
        'Competencia': 'Competencia',
        'Temporada': 'Temporada',
        'age': 'Edad',
        'height': 'Altura (cm)',
        'minutos_totales': 'Minutos Totales',
        'Score_Global': 'Score Global'
    }
    
    for col in score_columns:
        categoria_nombre = col.replace('Score_', '').replace('_', ' ')
        rename_dict[col] = f'Score {categoria_nombre}'
    
    df_tabla = df_tabla.rename(columns=rename_dict)
    
    # Formatear columnas numéricas
    for col in df_tabla.columns:
        if pd.api.types.is_numeric_dtype(df_tabla[col]) and col not in ['Temporada']:
            if 'Score' in col:
                df_tabla[col] = df_tabla[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "")
            else:
                df_tabla[col] = df_tabla[col].apply(lambda x: f"{x:.0f}" if pd.notna(x) else "")
    
    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
