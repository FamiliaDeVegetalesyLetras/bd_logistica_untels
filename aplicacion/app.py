import streamlit as st
import sqlite3
import pandas as pd
import time

st.set_page_config(page_title="Gestión Logística UNTELS", layout="wide")

# --- MENÚ DE NAVEGACIÓN LATERAL ---
st.sidebar.title("Navegación del Sistema")
menu = st.sidebar.selectbox("Seleccione una opción", [
    "Inicio / Dashboard", 
    "Consulta Dinámica de Órdenes", 
    "Métricas de Rendimiento", 
    "Diccionario de Datos"
])

# Conexión a SQLite (crea un archivo local 'logistica.db' automáticamente)
@st.cache_resource
def conectar_db():
    conn = sqlite3.connect("logistica.db", check_same_thread=False)
    return conn

conn = conectar_db()

# --- FUNCION PARA INICIALIZAR LA BD SI ESTÁ VACÍA ---
def inicializar_datos_prueba():
    cursor = conn.cursor()
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
    # Insertar datos de prueba si la tabla está vacía
    cursor.execute("SELECT COUNT(*) FROM ORDEN")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO ORDEN VALUES (?, ?, ?, ?, ?, ?, ?)", [
            (101, 'O/C', 'Comprometida', '20123456781', 'Proveedor A S.A.C.', '2026-07-05', 4500.00),
            (102, 'O/S', 'Devengada', '20123456782', 'Servicios Generales E.I.R.L.', '2026-07-12', 12000.50),
            (103, 'O/C', 'Comprometida', '20123456783', 'Comercial Lima S.A.', '2026-08-01', 850.00),
            (104, 'O/S', 'Anulada', '20123456781', 'Proveedor A S.A.C.', '2026-08-15', 3100.00)
        ])
        conn.commit()

inicializar_datos_prueba()

# --- VISTAS DEL SISTEMA ---
if menu == "Inicio / Dashboard":
    st.title("Panel de Control Logístico - UNTELS")
    st.write("Bienvenido al sistema web integrado con SQLite.")
    
    query_resumen = "SELECT COUNT(*) AS Total, SUM(Monto) AS MontoTotal FROM ORDEN"
    df_resumen = pd.read_sql(query_resumen, conn)
    
    col1, col2 = st.columns(2)
    col1.metric("Total de Órdenes Registradas", int(df_resumen['Total'].iloc[0]))
    col2.metric("Monto Global", f"S/. {df_resumen['MontoTotal'].iloc[0]:,.2f}")

elif menu == "Consulta Dinámica de Órdenes":
    st.title("Módulo de Consulta Multicriterio")
    
    col1, col2 = st.columns(2)
    tipo = col1.selectbox("Tipo de Orden", ["Todos", "O/C", "O/S"])
    estado = col2.selectbox("Estado", ["Todos", "Comprometida", "Devengada", "Anulada"])
    busqueda_ruc = st.text_input("Buscar por RUC o Razón Social")

    where_sql = "WHERE 1=1"
    if tipo != "Todos": where_sql += f" AND Tipo = '{tipo}'"
    if estado != "Todos": where_sql += f" AND Estado = '{estado}'"
    if busqueda_ruc: where_sql += f" AND (RUC LIKE '%{busqueda_ruc}%' OR Razon_Social LIKE '%{busqueda_ruc}%')"

    query = f"SELECT Numero_Orden, Tipo, Estado, RUC, Razon_Social, Fecha_Emision, Monto FROM ORDEN {where_sql}"
    
    start = time.time()
    df_result = pd.read_sql(query, conn)
    elapsed = (time.time() - start) * 1000

    st.info(f"Se encontraron {len(df_result)} registros en {elapsed:.2f} ms.")
    st.dataframe(df_result, use_container_width=True)

elif menu == "Métricas de Rendimiento":
    st.title("Evaluación de Rendimiento")
    st.write("Comparativa técnica del modelo y rendimiento de consultas con SQLite en la nube.")
    
    data_comparativa = {
        "Métrica Evaluada": ["Tiempo de Respuesta", "Tipo de Servidor", "Despliegue Web"],
        "Estructura Local (SQL Server)": ["< 5 ms", "Instancia Local (SQLEXPRESS)", "Requiere Túnel/IP"],
        "Estructura Cloud (SQLite)": ["< 10 ms", "Archivo Integrado en Contenedor", "100% Compatible con Link Público"]
    }
    st.table(pd.DataFrame(data_comparativa))

elif menu == "Diccionario de Datos":
    st.title("Diccionario de Datos del Sistema")
    st.write("Estructura de la tabla principal `ORDEN`.")
    st.markdown("""
    * **Numero_Orden**: Identificador único de la orden de compra o servicio.
    * **Tipo**: Clasificación de la orden (`O/C` u `O/S`).
    * **Estado**: Situación actual de la orden (`Comprometida`, `Devengada`, `Anulada`).
    * **RUC / Razon_Social**: Datos de identificación del proveedor.
    * **Monto**: Importe total expresado en Soles (S/.).
    """)
