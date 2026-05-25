import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import urllib.parse
import re

# CONFIGURACIÓN DE PÁGINA PREMIUM
st.set_page_config(
    page_title="Tienda de Agro - Paid Media Dashboard",
    page_icon="🌱",
    layout="wide"
)

# ESTILOS PREMIUM GO BIG 
st.markdown("""
    <style>
    .main { background-color: #0d0d0d; }
    [data-testid="stMetricValue"] { font-size: 32px; color: #d6b58e !important; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #f5f5f5 !important; }
    h1, h2, h3 { color: #ffffff; font-family: 'Georgia', serif; }
    .stSidebar { background-color: #1a1a1a; border-right: 1px solid #333; }
    .stPlotlyChart { border: 1px solid #333; border-radius: 8px; background-color: #1a1a1a; }
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA HISTÓRICA DE MESES ---
def obtener_meses_disponibles():
    meses_es = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    start_year, start_month = 2026, 5
    now = datetime.now()
    lista = []
    ano, mes = start_year, start_month
    while (ano < now.year) or (ano == now.year and mes <= now.month):
        lista.append(f"{meses_es[mes-1]} {ano}")
        if mes == 12:
            mes = 1
            ano += 1
        else:
            mes += 1
    return list(reversed(lista))

def get_csv_url_by_sheet(url, sheet_name):
    try:
        id_publicacion = url.split("/d/")[1].split("/")[0]
        sheet_enc = urllib.parse.quote(sheet_name)
        return f"https://docs.google.com/spreadsheets/d/{id_publicacion}/gviz/tq?tqx=out:csv&sheet={sheet_enc}"
    except:
        return url

def limpiar_monto_numerico(valor_str):
    try:
        limpio = re.sub(r'[^\d.-]', '', str(valor_str))
        return float(limpio) if limpio else 0.0
    except:
        return 0.0

# --- SIDEBAR CONTROL ---
meses_disponibles = obtener_meses_disponibles()
with st.sidebar:
    try:
        st.image("logo_tienda_de_agro.png", use_container_width=True)
    except:
        st.caption("🌱 *Sube 'logo_tienda_de_agro.png' a GitHub para activar el logo personalizado*")
        
    st.markdown("## 📊 Control de Paid Media")
    st.write("Propiedad: **Tienda de Agro**")
    st.markdown("---")
    mes_seleccionado = st.selectbox("📅 Seleccione el Mes de Reporte:", options=meses_disponibles)

# --- CONEXIÓN DINÁMICA CON LA URL TEXTUAL VERIFICADA ---
url_base = "https://docs.google.com/spreadsheets/d/19E2z83hOslnCEpV7wMTHDuR7PGTj1LN91ytMf4AiYhM/"
url_pacing = get_csv_url_by_sheet(url_base, mes_seleccionado)

try:
    df_raw = pd.read_csv(url_pacing, header=None, dtype=str).fillna('')
    
    # 1. RADAR INTELIGENTE DE ENCABEZADO: Localiza la fila 6 de forma dinámica
    idx_header = None
    for i, row in df_raw.iterrows():
        valores_fila = [str(x).lower().strip() for x in row.tolist()]
        if any(k in valores_fila for k in ['channel', 'canal', 'campaign', 'campaña']):
            idx_header = i
            break
            
    if idx_header is None:
        st.error(f"⚠️ Estructura de tabla (Channel/Campaign) no localizada en la pestaña '{mes_seleccionado}'.")
        st.stop()

    # 2. LECTURA LINEAL DEL PRESUPUESTO APROBADO GLOBAL (Fila 2)
    presupuesto_mensual = "$0"
    for i in range(idx_header):
        fila = df_raw.iloc[i].astype(str).tolist()
        for j, celda in enumerate(fila):
            celda_limpia = celda.lower().strip()
            if 'approved' in celda_limpia or 'aprobado' in celda_limpia:
                if j + 1 < len(fila) and fila[j+1].strip() not in ['', 'nan', '<na>']:
                    presupuesto_mensual = fila[j+1].strip()
                break
        if presupuesto_mensual != "$0":
            break

    # 3. EXTRACCIÓN INVERSA DE FECHA DE ACTUALIZACIÓN (Columna S = índice 18)
    col_idx_fecha = 18
    fecha_update = "N/D"
    if len(df_raw.columns) > col_idx_fecha:
        for row_pos in range(len(df_raw) - 1, idx_header, -1):
            val_celda = str(df_raw.iloc[row_pos, col_idx_fecha]).strip()
            val_lower = val_celda.lower()
            
            if val_celda != '' and val_lower not in ['nan', 'none', '<na>', '-', 'null', 'total']:
                if not any(k in val_lower for k in ['actualiz', 'pacing', 'fecha', 'campaign', 'channel', 'canal']):
                    fecha_update = val_celda
                    break

    # 4. EXTRACCIÓN Y CONSTRUCCIÓN DE MATRIZ DE DATOS (Mapeo posicional limpio)
    df_datos = df_raw.iloc[idx_header + 1:].copy()
    
    col_idx_medio = 0  # Columna A: Channel / Canal
    col_idx_camp = 1   # Columna B: Campaign
    col_idx_spend = 7  # Columna H: Spend (COP)
    col_idx_res = 14   # Columna O: Platform Conversions
    col_idx_tipo = 15  # Columna P: Official Conversions
    col_idx_cpa = 17   # Columna R: CPA

    df_limpio = pd.DataFrame()
    df_limpio['Medio_Raw'] = df_datos.iloc[:, col_idx_medio].astype(str).str.strip()
    df_limpio['Campaña'] = df_datos.iloc[:, col_idx_camp].astype(str).str.strip()
    df_limpio['Gasto_Raw'] = df_datos.iloc[:, col_idx_spend].astype(str).str.strip()
    
    if len(df_datos.columns) > col_idx_tipo:
        df_limpio['Objetivo'] = df_datos.iloc[:, col_idx_tipo].astype(str).str.strip().replace('', 'Sin Objetivo')
    else:
        df_limpio['Objetivo'] = 'General'
        
    df_limpio['Resultados'] = df_datos.iloc[:, col_idx_res].astype(str).str.strip() if len(df_datos.columns) > col_idx_res else 'N/D'
    df_limpio['CPA'] = df_datos.iloc[:, col_idx_cpa].astype(str).str.strip() if len(df_datos.columns) > col_idx_cpa else 'N/D'

    # 5. FILTRADO EXCLUSIVO DE FILAS VÁLIDAS (Ignora filas vacías y las de TOTAL de control)
    df_limpio = df_limpio[df_limpio['Campaña'] != '']
    df_limpio = df_limpio[~df_limpio['Campaña'].str.upper().str.contains('TOTAL')]
    df_limpio = df_limpio[~df_limpio['Campaña'].str.lower().str.contains('campaign|campaña|channel|canal')]

    # Relleno inteligente hacia abajo para asociar correctamente Google y META a sus campañas
    df_limpio['Medio_Raw'] = df_limpio['Medio_Raw'].replace(['', 'nan', 'NaN'], pd.NA)
    df_limpio['Medio'] = df_limpio['Medio_Raw'].ffill().fillna('Sin Medio')

    # Limpieza y conversión a número real de la columna de Inversión
    df_limpio['Gasto'] = df_limpio['Gasto_Raw'].str.replace(r'[^\d.-]', '', regex=True)
    df_limpio['Gasto'] = pd.to_numeric(df_limpio['Gasto'], errors='coerce').fillna(0)

    # 6. MÁSTER CÁLCULOS PARA LA INTERFAZ Y GRÁFICOS
    gasto_total_calculado = df_limpio['Gasto'].sum()
    
    resumen_medios = df_limpio.groupby('Medio')['Gasto'].sum()
    mapa_medios = {med: f"{med} (${tot:,.0f})" for med, tot in resumen_medios.items()}
    df_limpio['Medio_Labels'] = df_limpio['Medio'].map(mapa_medios).astype(str)

    # --- INTERFAZ VISUAL ---
    st.title(f"🌱 Dashboard Gerencial Tienda de Agro: {mes_seleccionado.title()}")
    
    c1, c2, c3 = st.columns(3)
    with c1: st.metric("Presupuesto Mensual", f"{presupuesto_mensual}")
    with c2: st.metric("Inversión Ejecutada", f"${gasto_total_calculado:,.0f}")
    with c3:
        if mes_seleccionado == meses_disponibles[0]:
            st.metric("Día de Medición", f"Día {datetime.now().day}")
        else:
            st.metric("Estado del Mes", "Cerrado")

    st.success(f"✅ Sincronización exitosa con la pestaña [{mes_seleccionado}] | Último registro: {fecha_update}")
    st.divider()

    # --- VISUALIZACIÓN TREEMAP ---
    st.header("📊 Distribución por Canal y Objetivo")
    df_plot = df_limpio[df_limpio['Gasto'] > 0]
    if not df_plot.empty:
        fig = px.treemap(df_plot, path=['Medio_Labels', 'Objetivo'], values='Gasto', color='Gasto', color_continuous_scale=['#b2d8d8', '#2e5b4b'])
        fig.update_traces(texttemplate="<b>%{label}</b><br>$%{value:,.0f}", hovertemplate="<b>%{label}</b><br>Inversión: $%{value:,.0f}<extra></extra>", textposition="middle center")
        fig.update_layout(margin=dict(t=10, l=10, r=10, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No se detectan datos de gasto mayores a $0 para graficar en este periodo.")

    # --- TABLA CONTROL ---
    with st.expander("📝 Detalle General de Campañas"):
        st.dataframe(df_limpio[['Medio', 'Campaña', 'Objetivo', 'Resultados', 'CPA']].sort_values(by='Medio'), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error detectado en el procesamiento de datos: {e}")

st.caption(f"Tienda de Agro Analytics | Strategic Analytics by goBIG")
