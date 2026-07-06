import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# -----------------------------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Análisis de Clientes Bancarios",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"   # Para mostrar los filtros de inmediato
)

# -----------------------------------------------------------------------------
# ESTILO FINANCIAL TIMES
# -----------------------------------------------------------------------------
FT_BLUE = '#1D2B53'
FT_TEAL = '#008571'
FT_RED = '#E3120B'
FT_GOLD = '#F8A32B'
FT_GRAY = '#6A6A6A'
FT_LIGHT_GRAY = '#F0F0F0'

def apply_ft_style(fig):
    fig.update_layout(
        plot_bgcolor='white',
        paper_bgcolor='white',
        font_family="Helvetica Neue, Arial, sans-serif",
        title_font_family="Helvetica Neue, Arial, sans-serif",
        title_font_size=18,
        title_font_color=FT_BLUE,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=12)
        ),
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(font_size=12)
    )
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor=FT_LIGHT_GRAY,
        tickfont=dict(size=12, color=FT_GRAY)
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor=FT_LIGHT_GRAY,
        tickfont=dict(size=12, color=FT_GRAY), zeroline=False
    )
    return fig

# -----------------------------------------------------------------------------
# CARGA Y PROCESAMIENTO (cacheado)
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_preprocess():
    df = pd.read_excel("Base Clientes Bancarios.xlsx", sheet_name="Datos")
    df.columns = df.columns.str.strip()

    # Fechas y edad
    df['Fecha Nacimiento'] = pd.to_datetime(df['Fecha Nacimiento'])
    today = pd.Timestamp.now()
    df['Edad'] = (today - df['Fecha Nacimiento']).dt.days // 365

    # Rangos
    bins_edad = [0, 50, 60, 70, 80, 100]
    labels_edad = ['<50', '50-60', '60-70', '70-80', '80+']
    df['Rango Edad'] = pd.cut(df['Edad'], bins=bins_edad, labels=labels_edad, right=False)

    # Segmento saldo (manejo seguro)
    try:
        df['Segmento Saldo'] = pd.qcut(df['Saldo Medio Anual'], q=4,
                                       labels=['Bajo', 'Medio-Bajo', 'Medio-Alto', 'Alto'],
                                       duplicates='drop')
    except ValueError:
        df['Segmento Saldo'] = pd.qcut(df['Saldo Medio Anual'], q=4, duplicates='drop')

    # Limpieza de categóricas
    cat_cols = ['Actividad Laboral', 'Estado Civil', 'Nivel Educacional',
                'Tiene Mora', 'Tiene Crédito Hipotecario', 'Tiene Crédito de Consumo',
                'Medio de Contacto Preferente', 'Tiene Inversiones']
    for col in cat_cols:
        if col in df.columns:
            df[col] = df[col].fillna('Desconocido').astype(str).str.strip()

    return df

df_full = load_and_preprocess()

# -----------------------------------------------------------------------------
# FILTROS INTERACTIVOS (barra lateral)
# -----------------------------------------------------------------------------
st.sidebar.header("🎯 Filtros Ejecutivos")

# Filtro por Actividad Laboral
actividades = ['Todos'] + sorted(df_full['Actividad Laboral'].unique().tolist())
actividad_sel = st.sidebar.selectbox("Actividad Laboral", actividades)

# Filtro por Rango de Edad
rangos_edad = ['Todos'] + sorted(df_full['Rango Edad'].dropna().unique().tolist())
edad_sel = st.sidebar.selectbox("Rango de Edad", rangos_edad)

# Filtro por Inversiones
inversion_sel = st.sidebar.radio("Tiene Inversiones", ['Todos', 'Si', 'No'])

# Aplicar filtros
df = df_full.copy()
if actividad_sel != 'Todos':
    df = df[df['Actividad Laboral'] == actividad_sel]
if edad_sel != 'Todos':
    df = df[df['Rango Edad'] == edad_sel]
if inversion_sel != 'Todos':
    df = df[df['Tiene Inversiones'] == inversion_sel]

# -----------------------------------------------------------------------------
# KPI - INDICADORES CLAVE (dinámicos según filtros)
# -----------------------------------------------------------------------------
total_clientes = len(df)
saldo_promedio = df['Saldo Medio Anual'].mean()
saldo_mediano = df['Saldo Medio Anual'].median()
pct_inversiones = (df['Tiene Inversiones'] == 'Si').mean() * 100
pct_credito_hip = (df['Tiene Crédito Hipotecario'] == 'Si').mean() * 100
pct_credito_cons = (df['Tiene Crédito de Consumo'] == 'Si').mean() * 100
pct_mora = (df['Tiene Mora'] == 'Si').mean() * 100
edad_promedio = df['Edad'].mean()
contactos_promedio = df['Contactos con su Ejecutivo'].mean()

# Texto dinámico de segmento
if actividad_sel != 'Todos' or edad_sel != 'Todos' or inversion_sel != 'Todos':
    st.info(f"🔍 Mostrando datos filtrados: **{total_clientes:,} clientes** seleccionados.")
else:
    st.caption("Vista global de todos los clientes. Use los filtros laterales para segmentar.")

# ---------- FILA DE KPIs (dos filas) ----------
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("👥 Total Clientes", f"{total_clientes:,}")
with col2:
    st.metric("💰 Saldo Promedio", f"${saldo_promedio:,.0f}")
with col3:
    st.metric("📊 Saldo Mediano", f"${saldo_mediano:,.0f}")
with col4:
    st.metric("⚠️ Tasa de Mora", f"{pct_mora:.2f}%")
with col5:
    st.metric("🎂 Edad Promedio", f"{edad_promedio:.0f} años")

col6, col7, col8, col9, col10 = st.columns(5)
with col6:
    st.metric("📈 Con Inversiones", f"{pct_inversiones:.1f}%")
with col7:
    st.metric("🏠 Créd. Hipotecario", f"{pct_credito_hip:.1f}%")
with col8:
    st.metric("🛒 Créd. Consumo", f"{pct_credito_cons:.1f}%")
with col9:
    st.metric("📞 Contactos Prom.", f"{contactos_promedio:.1f}")
with col10:
    st.metric("📉 Riesgo Combinado", f"{pct_mora + (100-pct_inversiones):.1f}", 
              help="Tasa de Mora + % sin inversiones (proxy de riesgo)")

st.divider()

# -----------------------------------------------------------------------------
# 1. PERFIL DEMOGRÁFICO (mejorado con distribuciones)
# -----------------------------------------------------------------------------
st.subheader("📌 1. Perfil del Cliente: ¿Quiénes son?")
col1, col2 = st.columns(2)

with col1:
    # Distribución de Edad (histograma)
    fig_hist_age = px.histogram(df, x='Edad', nbins=30,
                                 title="Distribución de Edad",
                                 color_discrete_sequence=[FT_BLUE])
    fig_hist_age = apply_ft_style(fig_hist_age)
    fig_hist_age.add_vline(x=df['Edad'].median(), line_dash="dash", line_color=FT_RED,
                           annotation_text="Mediana", annotation_position="top")
    st.plotly_chart(fig_hist_age, use_container_width=True)

with col2:
    # Actividad Laboral vs Rango Edad (heatmap o barras agrupadas)
    ct_act_edad = pd.crosstab(df['Actividad Laboral'], df['Rango Edad'])
    fig_act_edad = px.imshow(ct_act_edad, text_auto=True, aspect="auto",
                             title="Actividad Laboral por Rango de Edad",
                             color_continuous_scale='Blues')
    fig_act_edad = apply_ft_style(fig_act_edad)
    st.plotly_chart(fig_act_edad, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 2. COMPORTAMIENTO FINANCIERO (saldo, inversiones, mora)
# -----------------------------------------------------------------------------
st.subheader("💰 2. Comportamiento Financiero")
col1, col2 = st.columns(2)

with col1:
    # Boxplot de Saldo por Actividad (mejorado con puntos outliers ocultos y con filtro de inversión)
    fig_box = px.box(df, x='Actividad Laboral', y='Saldo Medio Anual',
                     color='Actividad Laboral',
                     color_discrete_sequence=[FT_BLUE, FT_TEAL, FT_GOLD, FT_RED],
                     points=False, title="Saldo Medio Anual por Actividad Laboral")
    fig_box = apply_ft_style(fig_box)
    fig_box.update_yaxes(tickprefix="$")
    st.plotly_chart(fig_box, use_container_width=True)

with col2:
    # Penetración de productos (barras apiladas por Actividad o general)
    prod_by_act = df.groupby('Actividad Laboral').agg(
        Inversiones=('Tiene Inversiones', lambda x: (x == 'Si').mean() * 100),
        Hipotecario=('Tiene Crédito Hipotecario', lambda x: (x == 'Si').mean() * 100),
        Consumo=('Tiene Crédito de Consumo', lambda x: (x == 'Si').mean() * 100)
    ).reset_index()
    prod_melt = prod_by_act.melt(id_vars='Actividad Laboral', var_name='Producto', value_name='Penetración (%)')
    fig_prod = px.bar(prod_melt, x='Actividad Laboral', y='Penetración (%)', color='Producto',
                      barmode='group', title="Penetración de Productos por Actividad",
                      color_discrete_sequence=[FT_TEAL, FT_BLUE, FT_GOLD])
    fig_prod = apply_ft_style(fig_prod)
    st.plotly_chart(fig_prod, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 3. RIESGO DE MORA (por segmentos)
# -----------------------------------------------------------------------------
st.subheader("⚠️ 3. Riesgo de Mora: ¿Dónde está el peligro?")
col1, col2 = st.columns(2)

with col1:
    # Tasa de mora por Actividad Laboral
    mora_act = df.groupby('Actividad Laboral')['Tiene Mora'].apply(lambda x: (x == 'Si').mean() * 100).reset_index()
    mora_act.columns = ['Actividad Laboral', 'Tasa de Mora (%)']
    fig_mora = px.bar(mora_act, x='Actividad Laboral', y='Tasa de Mora (%)',
                      color='Actividad Laboral', text_auto='.2f',
                      title="Tasa de Mora por Actividad Laboral",
                      color_discrete_sequence=[FT_RED, FT_GOLD, FT_BLUE, FT_TEAL])
    fig_mora = apply_ft_style(fig_mora)
    st.plotly_chart(fig_mora, use_container_width=True)

with col2:
    # Mora vs Inversiones (barras agrupadas)
    cross_mora_inv = df.groupby(['Tiene Inversiones', 'Tiene Mora']).size().unstack(fill_value=0)
    # Normalizar por fila
    cross_mora_inv_pct = cross_mora_inv.div(cross_mora_inv.sum(axis=1), axis=0) * 100
    fig_mora_inv = px.bar(cross_mora_inv_pct.reset_index(), x='Tiene Inversiones', y='Si',
                          color='Tiene Inversiones', text_auto='.2f',
                          title="Clientes en Mora según tenencia de Inversiones",
                          labels={'Si': 'Tasa de Mora (%)'},
                          color_discrete_sequence=[FT_TEAL, FT_GRAY])
    fig_mora_inv = apply_ft_style(fig_mora_inv)
    st.plotly_chart(fig_mora_inv, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 4. MAPA DE CALOR DE CORRELACIONES
# -----------------------------------------------------------------------------
st.subheader("🔗 4. Correlaciones entre Variables Numéricas")
# Seleccionar numéricas
num_cols = ['Edad', 'Saldo Medio Anual', 'Contactos con su Ejecutivo']
# Convertir 'Tiene Mora' a numérico
df['Mora_num'] = (df['Tiene Mora'] == 'Si').astype(int)
num_cols.append('Mora_num')
corr = df[num_cols].corr()
fig_heat = px.imshow(corr, text_auto=True, aspect="auto",
                     title="Matriz de Correlación",
                     color_continuous_scale='RdBu_r', zmin=-1, zmax=1)
fig_heat = apply_ft_style(fig_heat)
st.plotly_chart(fig_heat, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 5. SUNBURST: NIVEL EDUCACIONAL → INVERSIONES
# -----------------------------------------------------------------------------
st.subheader("🎓 5. Nivel Educacional y su relación con Inversiones")
fig_sun = px.sunburst(df, path=['Nivel Educacional', 'Tiene Inversiones'],
                      title="Jerarquía: Nivel Educacional → Tiene Inversiones",
                      color_discrete_sequence=[FT_BLUE, FT_TEAL, FT_GOLD, FT_RED, FT_GRAY])
fig_sun = apply_ft_style(fig_sun)
st.plotly_chart(fig_sun, use_container_width=True)

st.divider()

# -----------------------------------------------------------------------------
# 6. STORYTELLING EJECUTIVO (adaptativo)
# -----------------------------------------------------------------------------
st.header("📖 Narrativa Ejecutiva")

# Determinar algunos hechos automáticos para el storytelling
jubilados_pct = (df['Actividad Laboral'] == 'Jubilado').mean() * 100
saldo_jub = df[df['Actividad Laboral'] == 'Jubilado']['Saldo Medio Anual'].median()
inversiones_jub = (df[df['Actividad Laboral'] == 'Jubilado']['Tiene Inversiones'] == 'Si').mean() * 100

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    ### 🔍 ¿Quién es nuestro cliente?
    - **{total_clientes:,} clientes** bajo los filtros actuales.
    - Edad promedio: **{edad_promedio:.0f} años**; el **{jubilados_pct:.0f}%** son jubilados.
    - Saldo mediano: **${saldo_mediano:,.0f}** (promedio ${saldo_promedio:,.0f}).
    """)

with col2:
    st.markdown(f"""
    ### 📊 Comportamiento financiero
    - **{pct_inversiones:.0f}%** tiene inversiones (depósitos a plazo).
    - **{pct_mora:.1f}%** está en mora; los clientes **sin inversiones** muestran mayor morosidad.
    - Penetración de créditos hipotecarios: **{pct_credito_hip:.1f}%**.
    """)

with col3:
    st.markdown(f"""
    ### 🚀 Oportunidad estratégica
    - Los jubilados concentran los **mayores saldos** (mediana ${saldo_jub:,.0f}) y un **{inversiones_jub:.0f}%** ya invierte.
    - Solo **{contactos_promedio:.1f} contactos/año** con el ejecutivo: hay espacio para asesoría proactiva.
    - La correlación positiva entre saldo y contactos sugiere que **el contacto sí construye relación**.
    """)

st.divider()

# Recomendaciones basadas en los datos filtrados
st.subheader("✅ Recomendaciones de Negocio Accionables")
rec_col1, rec_col2 = st.columns(2)

with rec_col1:
    st.markdown("""
    ### 🎯 Programa "Asesoría Patrimonial Senior"
    - **Segmento objetivo**: Jubilados con saldo > $10M que aún no tienen inversiones.
    - **Acción**: Asignar un ejecutivo dedicado para ofrecer fondos mutuos y planificación hereditaria.
    - **Impacto esperado**: +20% en captación de inversiones, reducción de fuga por herencia.
    """)

with rec_col2:
    st.markdown("""
    ### 📱 Digitalización selectiva para hijos y nietos
    - **Segmento objetivo**: Clientes <50 años o familiares de clientes actuales.
    - **Acción**: Campaña omnicanal (email, app) con beneficios por referidos.
    - **Impacto esperado**: Aumentar la base de clientes jóvenes en un 5%, mejorar NPS.
    """)

st.divider()
st.caption("Dashboard dinámico · Filtros laterales para explorar · Estilo Financial Times · Datos actualizados desde Excel.")
