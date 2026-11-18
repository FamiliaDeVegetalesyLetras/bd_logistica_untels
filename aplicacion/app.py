import streamlit as st
import sqlite3
import pandas as pd
import time
import os

st.set_page_config(page_title="Gestión de Base de Datos - UNTELS", layout="wide")

# --- MENÚ DE NAVEGACIÓN LATERAL ---
st.sidebar.title("Gestión de BD - UNTELS")
menu = st.sidebar.selectbox("Seleccione un módulo:", [
    "1. Inicio / Resumen Ejecutivo", 
    "2. Consulta Multicriterio (DML)", 
    "3. Laboratorio de Índices y Tuning", 
    "4. Diccionario y Arquitectura"
])

# --- CONEXIÓN A SQLITE ---
@st.cache_resource
def conectar_db():
    return sqlite3.connect("logistica_untels.db", check_same_thread=False)

conn = conectar_db()

# --- PROCESO ETL AUTOMÁTICO DESDE EXCEL ---
def inicializar_etl():
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ORDEN (
            Numero_Orden INTEGER,
            Tipo TEXT,
            Estado TEXT,
            RUC TEXT,
            Razon_Social TEXT,
            Tipo_Contratacion TEXT,
            Descripcion TEXT,
            Fecha_Emision TEXT,
            Monto REAL
        )
    """)
    conn.commit()
    
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
                # Limpiar espacios en los nombres de columnas
                df_temp.columns = [str(c).strip() for c in df_temp.columns]
                frames.append(df_temp)
        
        if frames:
            df_total = pd.concat(frames, ignore_index=True)
            registros = []
            for _, row in df_total.iterrows():
                try:
                    num = int(float(row.get('Número de orden', row.get('Numero_Orden', 0))))
                    tipo = str(row.get('Tipo de Orden', row.get('Tipo', 'O/C'))).strip()
                    estado = str(row.get('Estado', 'Comprometida')).strip()
                    ruc = str(row.get('RUC', '')).replace('.0', '').strip()
                    razon = str(row.get('Denominación o razón Social', row.get('Razon_Social', ''))).strip()
                    contratacion = str(row.get('Tipo de Contratación', 'NAN')).strip()
                    desc = str(row.get('Descripción y Finalidad de la contratación', '')).strip()
                    fecha = str(row.get('Fecha de Emisión', '2026-07-01'))[:10]
                    
                    monto_str = str(row.get('Monto', 0)).replace('S/.', '').replace(',', '').strip()
                    monto = float(monto_str) if monto_str and monto_str.lower() != 'nan' else 0.0
                    
                    if num > 0:
                        registros.append((num, tipo, estado, ruc, razon, contratacion, desc, fecha, monto))
                except Exception:
                    continue
            
            if registros:
                cursor.executemany("INSERT INTO ORDEN VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", registros)
                conn.commit()

inicializar_etl()

# --- MÓDULO 1: INICIO ---
if menu == "1. Inicio / Resumen Ejecutivo":
    st.title("Gestión de Base de Datos Logística - UNTELS")
    st.markdown("Sistema web conectado al repositorio centralizado de Órdenes de Compra y Servicio (Julio - Agosto 2026).")
    
    df_res = pd.read_sql_query("SELECT COUNT(*) AS Total, SUM(Monto) AS MontoTotal, COUNT(DISTINCT RUC) AS Proveedores FROM ORDEN", conn)
    total = int(df_res['Total'].iloc[0] or 0)
    monto = float(df_res['MontoTotal'].iloc[0] or 0.0)
    provs = int(df_res['Proveedores'].iloc[0] or 0)
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Órdenes Consolidadas", f"{total:,}")
    c2.metric("Monto Global Ejecutado", f"S/. {monto:,.2f}")
    c3.metric("Proveedores Únicos", f"{provs:,}")

    st.subheader("Distribución por Estado de Orden")
    df_estado = pd.read_sql_query("SELECT Estado, COUNT(*) AS Cantidad, SUM(Monto) AS Total_Soles FROM ORDEN GROUP BY Estado", conn)
    st.dataframe(df_estado, use_container_width=True)

# --- MÓDULO 2: CONSULTA DINÁMICA (DML) ---
elif menu == "2. Consulta Multicriterio (DML)":
    st.title("Módulo de Consulta Dinámica y Auditoría")
    
    col1, col2, col3 = st.columns(3)
    tipo = col1.selectbox("Tipo de Orden", ["Todos", "O/C", "O/S"])
    estado = col2.selectbox("Estado", ["Todos", "Comprometida", "Devengada", "Anulada"])
    busqueda = col3.text_input("Buscar por RUC o Razón Social")

    condiciones = ["1=1"]
    params = []
    if tipo != "Todos":
        condiciones.append("Tipo = ?")
        params.append(tipo)
    if estado != "Todos":
        condiciones.append("Estado = ?")
        params.append(estado)
    if busqueda:
        condiciones.append("(RUC LIKE ? OR Razon_Social LIKE ?)")
        params.extend([f"%{busqueda}%", f"%{busqueda}%"])

    query = f"SELECT Numero_Orden, Tipo, Estado, RUC, Razon_Social, Fecha_Emision, Monto FROM ORDEN WHERE {' AND '.join(condiciones)}"
    
    t0 = time.perf_counter()
    df_res = pd.read_sql_query(query, conn, params=params)
    t_ms = (time.perf_counter() - t0) * 1000

    st.success(f"Consulta ejecutada en **{t_ms:.2f} ms** | Registros encontrados: **{len(df_res)}**")
    st.dataframe(df_res, use_container_width=True)

# --- MÓDULO 3: LABORATORIO DE ÍNDICES Y TUNING ---
elif menu == "3. Laboratorio de Índices y Tuning":
    st.title("Laboratorio Dinámico de Indexación y Planes de Ejecución")
    st.write("Evalúa el impacto de crear un índice no agrupado temporal sobre un atributo de búsqueda, inspecciona el plan de ejecución y elimina el índice al finalizar.")
    
    atributo = st.selectbox("Seleccione el atributo a indexar:", ["RUC", "Fecha_Emision", "Estado", "Monto"])
    
    if st.button("Ejecutar Experimento (Crear Índice -> Consultar + Plan -> Eliminar Índice)"):
        cur = conn.cursor()
        
        # 1. Sin índice (Asegurar limpieza)
        cur.execute(f"DROP INDEX IF EXISTS IX_Temp_{atributo}")
        
        t_sin_0 = time.perf_counter()
        cur.execute(f"SELECT * FROM ORDEN WHERE {atributo} IS NOT NULL ORDER BY {atributo}")
        cur.fetchall()
        t_sin = (time.perf_counter() - t_sin_0) * 1000
        plan_sin = pd.read_sql_query(f"EXPLAIN QUERY PLAN SELECT * FROM ORDEN WHERE {atributo} IS NOT NULL ORDER BY {atributo}", conn)

        # 2. Crear índice temporal
        t_idx_0 = time.perf_counter()
        cur.execute(f"CREATE INDEX IX_Temp_{atributo} ON ORDEN({atributo})")
        t_creacion = (time.perf_counter() - t_idx_0) * 1000

        # 3. Con índice
        t_con_0 = time.perf_counter()
        cur.execute(f"SELECT * FROM ORDEN WHERE {atributo} IS NOT NULL ORDER BY {atributo}")
        cur.fetchall()
        t_con = (time.perf_counter() - t_con_0) * 1000
        plan_con = pd.read_sql_query(f"EXPLAIN QUERY PLAN SELECT * FROM ORDEN WHERE {atributo} IS NOT NULL ORDER BY {atributo}", conn)

        # 4. Eliminar índice temporal
        cur.execute(f"DROP INDEX IF EXISTS IX_Temp_{atributo}")
        conn.commit()

        st.info(f"Índice `IX_Temp_{atributo}` creado en {t_creacion:.2f} ms, evaluado y eliminado correctamente.")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Sin Índice (Table Scan)")
            st.metric("Tiempo de Ejecución", f"{t_sin:.3f} ms")
            st.dataframe(plan_sin, use_container_width=True)
        with c2:
            st.markdown("#### Con Índice (Index Scan / Covering)")
            st.metric("Tiempo de Ejecución", f"{t_con:.3f} ms")
            st.dataframe(plan_con, use_container_width=True)

# --- MÓDULO 4: DICCIONARIO Y ARQUITECTURA ---
elif menu == "4. Diccionario y Arquitectura":
    st.title("Arquitectura de Gestión de Base de Datos")
    st.markdown("""
    * **Almacenamiento Físico (SQL Server):** Archivos `.mdf` (Datos primarios) y `.ldf` (Log de transacciones) con crecimiento controlado.
    * **Integridad y Normalización (3FN):** Esquema compuesto por `ORDEN`, `PROVEEDOR`, `TIPO_ORDEN` y `ESTADO_ORDEN`.
    * **Tuning y Monitoreo:** Evaluación de lecturas lógicas (`STATISTICS IO`), tiempo de CPU (`STATISTICS TIME`) e índices B-Tree.
    """)

elif menu == "Diccionario de Datos":
    st.title("Diccionario de Datos del Sistema")
    st.write("Estructura basada en los archivos de la UNTELS.")
