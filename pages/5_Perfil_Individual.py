import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import matplotlib.colors as mcolors

st.set_page_config(page_title="Perfil Individual", page_icon="👤", layout="wide")

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

st.title("👤 Perfil Individual de Portero")

st.markdown("""
Análisis detallado de un portero específico mostrando su posición relativa (Z-Score) en cada variable por categoría.
""")

# Crear mapeo de nombres
nombre_map = dict(zip(diccionario['metrica'], diccionario['nombre_limpio']))

# FILTROS
st.sidebar.header("Filtros de Comparación")

# Filtro de minutos mínimos
min_minutos = st.sidebar.slider(
    "Minutos Mínimos",
    min_value=0,
    max_value=int(df['minutos_totales'].max()),
    value=450,
    step=50
)

# Filtro de competencias
competencias_disponibles = sorted(df['Competencia'].unique())
competencias_seleccionadas = st.sidebar.multiselect(
    "Competencias",
    options=competencias_disponibles,
    default=competencias_disponibles
)

# Filtro de temporadas
temporadas_disponibles = sorted(df['Temporada'].unique(), reverse=True)
temporadas_seleccionadas = st.sidebar.multiselect(
    "Temporadas",
    options=temporadas_disponibles,
    default=temporadas_disponibles
)

# Filtro de edad
if 'age' in df.columns:
    min_edad = int(df['age'].min())
    max_edad = int(df['age'].max())
    edad_range = st.sidebar.slider(
        "Rango de Edad",
        min_value=min_edad,
        max_value=max_edad,
        value=(min_edad, max_edad)
    )

# Aplicar filtros para crear pool de comparación
df_pool = df.copy()

# Filtro de minutos
df_pool = df_pool[df_pool['minutos_totales'] >= min_minutos]

# Filtro de competencias
if competencias_seleccionadas:
    df_pool = df_pool[df_pool['Competencia'].isin(competencias_seleccionadas)]

# Filtro de temporadas
if temporadas_seleccionadas:
    df_pool = df_pool[df_pool['Temporada'].isin(temporadas_seleccionadas)]

# Filtro de edad
if 'age' in df_pool.columns:
    df_pool = df_pool[
        (df_pool['age'] >= edad_range[0]) & 
        (df_pool['age'] <= edad_range[1])
    ]

# Crear identificador único (Jugador - Temporada - Equipo - Competencia)
df_pool['id_jugador'] = df_pool['jugador'] + ' - ' + df_pool['Temporada'].astype(str) + ' - ' + df_pool['TeamName'] + ' - ' + df_pool['Competencia']

st.info(f"📊 Pool de comparación: {len(df_pool)} porteros")

# SELECTOR DE JUGADOR
st.sidebar.markdown("---")
st.sidebar.header("Selección de Jugador")

if len(df_pool) == 0:
    st.warning("⚠️ No hay porteros disponibles con los filtros seleccionados.")
else:
    jugadores_opciones = sorted(df_pool['id_jugador'].unique())
    jugador_seleccionado = st.sidebar.selectbox(
        "Buscar y seleccionar portero",
        options=jugadores_opciones,
        index=0
    )
    
    if jugador_seleccionado:
        # CSS para reducir tamaño de fuente en metrics
        st.markdown("""
        <style>
        [data-testid="stMetricValue"] {
            font-size: 18px;
        }
        [data-testid="stMetricLabel"] {
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Obtener datos del jugador seleccionado
        jugador_data = df_pool[df_pool['id_jugador'] == jugador_seleccionado].iloc[0]
        
        # Crear identificador para buscar scores
        df_scores['id_jugador'] = df_scores['jugador'] + ' - ' + df_scores['Temporada'].astype(str) + ' - ' + df_scores['TeamName'] + ' - ' + df_scores['Competencia']
        
        # Obtener scores del jugador
        jugador_scores = df_scores[df_scores['id_jugador'] == jugador_seleccionado]
        score_global = jugador_scores['Score_Global'].iloc[0] if len(jugador_scores) > 0 else 0
        
        # Filtrar pool solo a la competencia del jugador seleccionado
        competencia_jugador = jugador_data['Competencia']
        df_pool_competencia = df_pool[df_pool['Competencia'] == competencia_jugador].copy()
        
        # Mostrar información básica del jugador
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Jugador", jugador_data['jugador'])
        with col2:
            st.metric("Equipo", jugador_data['TeamName'])
        with col3:
            st.metric("Competencia", competencia_jugador)
        with col4:
            st.metric("Edad", f"{int(jugador_data['age'])} años")
        with col5:
            st.metric("Minutos", int(jugador_data['minutos_totales']))
        with col6:
            st.metric("🎯 Score Global", f"{score_global:.1f}")
        
        st.info(f"📊 Comparando con {len(df_pool_competencia)} porteros de {competencia_jugador}")
        
        st.markdown("---")
        
        # GRÁFICO LOLLIPOP DE SCORES POR CATEGORÍA
        st.subheader("🎯 Scores por Categoría")
        
        # Obtener columnas de scores (excluyendo Score_Global)
        score_columns = [col for col in jugador_scores.columns if col.startswith('Score_') and col != 'Score_Global']
        
        if len(score_columns) > 0:
            # Preparar datos para el lollipop
            categorias_nombres = [col.replace('Score_', '').replace('_', ' ') for col in score_columns]
            scores_valores = [jugador_scores[col].iloc[0] for col in score_columns]
            
            # Crear figura
            fig_lollipop, ax_lollipop = plt.subplots(figsize=(12, max(4, len(categorias_nombres) * 0.4)))
            
            # Ordenar por score
            datos_ordenados = sorted(zip(categorias_nombres, scores_valores), key=lambda x: x[1])
            categorias_ordenadas = [x[0] for x in datos_ordenados]
            scores_ordenados = [x[1] for x in datos_ordenados]
            
            # Crear colormap de rojo a verde
            cmap_lollipop = mcolors.LinearSegmentedColormap.from_list(
                'RedGreen', ['#E53935', '#FDD835', '#00A651']
            )
            norm_lollipop = mcolors.Normalize(vmin=0, vmax=100)
            
            # Crear lollipops
            for i, (cat, score) in enumerate(zip(categorias_ordenadas, scores_ordenados)):
                color = cmap_lollipop(norm_lollipop(score))
                # Línea
                ax_lollipop.plot([0, score], [i, i], color=color, linewidth=2.5, alpha=0.8)
                # Círculo
                ax_lollipop.scatter([score], [i], color=color, s=150, zorder=3, edgecolor='black', linewidth=1.5)
                # Etiqueta de valor
                ax_lollipop.text(score + 2, i, f"{score:.1f}", va='center', fontsize=10, fontweight='bold')
            
            # Configuración del gráfico
            ax_lollipop.set_yticks(range(len(categorias_ordenadas)))
            ax_lollipop.set_yticklabels(categorias_ordenadas, fontsize=11)
            ax_lollipop.set_xlabel('Score', fontsize=12, fontweight='bold')
            ax_lollipop.set_xlim(-5, 110)
            ax_lollipop.set_title(
                f"Scores por Categoría - {jugador_data['jugador']} (Score Global: {score_global:.1f})",
                fontsize=13,
                fontweight='bold',
                pad=15
            )
            ax_lollipop.grid(axis='x', alpha=0.3, linestyle='--')
            ax_lollipop.axvline(x=50, color='gray', linestyle='--', linewidth=1, alpha=0.5)
            
            plt.tight_layout()
            st.pyplot(fig_lollipop)
            plt.close()
        
        st.markdown("---")
        
        # Obtener categorías (excluyendo 'Otras')
        categorias = [cat for cat in diccionario['categoria'].dropna().unique() if cat.lower() != 'otras']
        
        # Crear gráfico de Z-score por cada categoría
        for categoria in categorias:
            st.subheader(f"📊 {categoria}")
            
            # Obtener variables de esta categoría
            metricas_cat = diccionario[diccionario['categoria'] == categoria]
            variables = metricas_cat['metrica'].tolist()
            
            # Filtrar solo variables que existen en el dataframe
            variables = [v for v in variables if v in df_pool.columns]
            
            if len(variables) == 0:
                st.info(f"No hay variables disponibles para la categoría {categoria}")
                continue
            
            # Calcular Z-scores
            z_scores_data = []
            player_zscores = {}
            
            for var in variables:
                # Verificar si la variable debe invertirse
                var_info = diccionario[diccionario['metrica'] == var].iloc[0]
                invertir = var_info['Invertir'] if pd.notna(var_info['Invertir']) else False
                
                # Calcular media y desviación estándar del pool de la competencia
                values = df_pool_competencia[var].dropna()
                
                if len(values) < 2:  # Necesitamos al menos 2 valores
                    continue
                
                mean_val = values.mean()
                std_val = values.std()
                
                if std_val == 0:  # Evitar división por cero
                    continue
                
                # Obtener nombre bonito de la variable
                nombre_bonito = nombre_map.get(var, var)
                
                # Z-scores solo para jugadores de la misma competencia
                for idx, row in df_pool_competencia.iterrows():
                    if pd.notna(row[var]):
                        z_score = (row[var] - mean_val) / std_val
                        
                        # Invertir el signo si la variable es negativa
                        if invertir:
                            z_score = -z_score
                        
                        es_jugador = row['id_jugador'] == jugador_seleccionado
                        
                        z_scores_data.append({
                            'Variable': nombre_bonito,
                            'Z-Score': z_score,
                            'Es_Jugador_Seleccionado': es_jugador
                        })
                        
                        # Guardar z-score del jugador seleccionado
                        if es_jugador:
                            player_zscores[nombre_bonito] = z_score
            
            if len(z_scores_data) == 0:
                st.info(f"No hay datos suficientes para graficar {categoria}")
                continue
            
            df_zscore = pd.DataFrame(z_scores_data)
            
            # Crear el gráfico
            fig, ax = plt.subplots(figsize=(12, max(6, len(player_zscores) * 0.5)))
            
            # Configurar orden de variables (invertido para que aparezca de arriba a abajo)
            var_order = list(player_zscores.keys())[::-1]
            
            # Separar datos
            df_others = df_zscore[~df_zscore['Es_Jugador_Seleccionado']]
            df_selected = df_zscore[df_zscore['Es_Jugador_Seleccionado']]
            
            # Plot otros jugadores en gris
            if not df_others.empty:
                sns.stripplot(
                    data=df_others,
                    x='Z-Score',
                    y='Variable',
                    order=var_order,
                    color='#CCCCCC',
                    alpha=0.6,
                    size=5,
                    jitter=0.3,
                    ax=ax
                )
            
            # Crear colormap de rojo a amarillo a verde
            cmap = mcolors.LinearSegmentedColormap.from_list(
                'RedYellowGreen', ['#E53935', '#FDD835', '#00A651']
            )
            norm = mcolors.TwoSlopeNorm(vmin=-3, vcenter=0, vmax=3)
            
            # Plot jugador seleccionado con colores según z-score
            for nombre_var in var_order:
                if nombre_var in player_zscores:
                    z_val = player_zscores[nombre_var]
                    color = cmap(norm(z_val))
                    
                    # Filtrar datos del jugador para esta variable
                    df_var = df_selected[df_selected['Variable'] == nombre_var]
                    
                    if not df_var.empty:
                        ax.scatter(
                            df_var['Z-Score'],
                            [nombre_var] * len(df_var),
                            color=color,
                            s=120,
                            linewidth=1.5,
                            edgecolor='black',
                            alpha=1,
                            zorder=3
                        )
            
            # Línea vertical en Z-Score = 0 (media)
            ax.axvline(x=0, color='black', linestyle='--', linewidth=1.5, alpha=0.7)
            
            # Configuración del gráfico
            ax.set_xlabel('Z-Score', fontsize=12, fontweight='bold')
            ax.set_ylabel('')
            ax.tick_params(axis='y', labelsize=11)
            ax.tick_params(axis='x', labelsize=10)
            
            # Título con información del contexto
            temp_text = ", ".join(map(str, temporadas_seleccionadas)) if len(temporadas_seleccionadas) <= 3 else f"{len(temporadas_seleccionadas)} temporadas"
            
            ax.set_title(
                f"{jugador_data['jugador']} - {categoria}\n{competencia_jugador} | {temp_text} | {len(df_pool_competencia)} porteros",
                fontsize=13,
                fontweight='bold',
                pad=15
            )
            
            ax.set_xlim(-4, 4)
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            
            plt.tight_layout()
            
            # Mostrar en Streamlit
            st.pyplot(fig)
            plt.close()
            
            st.markdown("---")
