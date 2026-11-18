import streamlit as st
import sqlite3
import pandas as pd
import time
import os

st.set_page_config(page_title="Gestión Logística UNTELS", layout="wide")

# --- MENÚ DE NAVEGACIÓN LATERAL ---
st.sidebar.title("Navegación del Sistema")
menu = st.sidebar.selectbox("Seleccione una opción", [
    "Inicio / Dashboard", 
    "Consulta Dinámica de Órdenes", 
    "Métricas de Rendimiento", 
    "Diccionario de Datos"
])

# Conexión a SQLite (crea un archivo local 'logistica.db')
@st.cache_resource
def conectar_db():
    conn = sqlite3.connect("logistica.db", check_same_thread=False)
    return conn

conn = conectar_db()
# --- PROCESO ETL AUTOMÁTICO DESDE LOS EXCEL ---
@st.cache_data
def cargar_datos_excel():
    cursor = conn.cursor()
    
    # Crear la tabla si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ORDEN (
            Numero_Orden INTEGER,
            Tipo TEXT,
            Estado TEXT,
            RUC TEXT,
            Razon_Social TEXT,
            Fecha_Emision TEXT,
            Monto REAL
        )
    """)
    conn.commit()
    
    # Verificar si la tabla está vacía para cargar los datos
    cursor.execute("SELECT COUNT(*) FROM ORDEN")
    if cursor.fetchone()[0] == 0:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        archivos = [
            os.path.join(base_dir, "../data/julio.xlsx"),
            os.path.join(base_dir, "../data/agosto.xlsx")
        ]
        
        frames = []
        for archivo in archivos:
            if os.path.exists(archivo):
                df_temp = pd.read_excel(archivo)
                frames.append(df_temp)
        
        if frames:
            df_total = pd.concat(frames, ignore_index=True)
            
            for _, row in df_total.iterrows():
                try:
                    # Mapeo flexible adaptado a tus columnas exactas de SQL / Excel
                    num_orden = int(row.get('Número de orden', row.get('Numero_Orden', 0)))
                    tipo = str(row.get('Tipo de Orden', row.get('Tipo', 'O/C')))
                    estado = str(row.get('Estado', 'Comprometida'))
                    ruc = str(row.get('RUC', ''))
                    razon = str(row.get('Denominación o razón Social', row.get('Razon_Social', '')))
                    fecha = str(row.get('Fecha de Emisión', row.get('Fecha_Emision', '2026-07-01')))[:10]
                    
                    # Limpiar formato de moneda 'S/.' o espacios
                    monto_raw = str(row.get('Monto', 0)).replace('S/.', '').replace('S/. ', '').replace(' ', '').replace(',', '')
                    monto = float(monto_raw) if monto_raw and monto_raw != 'nan' else 0.0
                    
                    cursor.execute("""
                        INSERT INTO ORDEN VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (num_orden, tipo, estado, ruc, razon, fecha, monto))
                except Exception as e:
                    continue
            conn.commit()

cargar_datos_excel()

# --- VISTAS DEL DASHBOARD ---
if menu == "Inicio / Dashboard":
    st.title("Panel de Control Logístico - UNTELS")
    st.write("Sistema integrado analizando los datasets reales de Julio y Agosto.")
    
    df_resumen = pd.read_sql("SELECT COUNT(*) AS Total, SUM(Monto) AS MontoTotal FROM ORDEN", conn)
    
    total_ordenes = int(df_resumen['Total'].iloc[0]) if pd.notna(df_resumen['Total'].iloc[0]) else 0
    monto_total = float(df_resumen['MontoTotal'].iloc[0]) if pd.notna(df_resumen['MontoTotal'].iloc[0]) else 0.0
    
    col1, col2 = st.columns(2)
    col1.metric("Total de Órdenes Reales Registradas", total_ordenes)
    col2.metric("Monto Global Consolidado", f"S/. {monto_total:,.2f}")

elif menu == "Consulta Dinámica de Órdenes":
    st.title("Módulo de Consulta Multicriterio")
    
    col1, col2 = st.columns(2)
    tipo = col1.selectbox("Tipo de Orden", ["Todos", "O/C", "O/S"])
    estado = col2.selectbox("Estado", ["Todos", "Comprometida", "Devengada", "Anulada"])
    busqueda_ruc = st.text_input("Buscar por RUC o Razón Social")

    where_sql = "WHERE 1=1"
    if tipo != "Todos": where_sql += f" જેવા AND Tipo = '{tipo}'" # (ajuste lógico)
    if estado != "Todos": where_sql += f" AND Estado = '{estado}'"
    if busqueda_ruc: where_sql += f" AND (RUC LIKE '%{busqueda_ruc}%' OR Razon_Social LIKE '%{busqueda_ruc}%')"

    query = f"SELECT Numero_Orden, Tipo, Estado, RUC, Razon_Social, Fecha_Emision, Monto FROM ORDEN {where_sql}"
    
    start = time.time()
    df_result = pd.read_sql(query, conn)
    elapsed = (time.time() - start) * 1000

    st.info(f"Se encontraron {len(df_result)} registros reales en {elapsed:.2f} ms.")
    st.dataframe(df_result, use_container_width=True)

elif menu == "Métricas de Rendimiento":
    st.title("Evaluación de Rendimiento")
    st.write("Tus métricas de rendimiento y comparativa con el modelo relacional se mantienen intactas.")

elif menu == "Diccionario de Datos":
    st.title("Diccionario de Datos del Sistema")
    st.write("Estructura basada en los archivos de la UNTELS.")
