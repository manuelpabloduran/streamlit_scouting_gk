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

df, diccionario = load_data()

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
        # Obtener datos del jugador seleccionado
        jugador_data = df_pool[df_pool['id_jugador'] == jugador_seleccionado].iloc[0]
        
        # Filtrar pool solo a la competencia del jugador seleccionado
        competencia_jugador = jugador_data['Competencia']
        df_pool_competencia = df_pool[df_pool['Competencia'] == competencia_jugador].copy()
        
        # Mostrar información básica del jugador
        col1, col2, col3, col4, col5 = st.columns(5)
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
        
        st.info(f"📊 Comparando con {len(df_pool_competencia)} porteros de {competencia_jugador}")
        
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
            z_scores_data = [] de la competencia
                values = df_pool_competencia
            
            for var in variables:
                # Verificar si la variable debe invertirse
                var_info = diccionario[diccionario['metrica'] == var].iloc[0]
                invertir = var_info['Invertir'] if pd.notna(var_info['Invertir']) else False
                
                # Calcular media y desviación estándar del pool
                values = df_pool[var].dropna()
                
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
