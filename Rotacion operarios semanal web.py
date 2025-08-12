# -*- coding: utf-8 -*-
"""
Created on Tue Aug 12 14:39:07 2025

@author: NCGNpracpim
"""

# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import io

# Título y descripción de la aplicación
st.title("Análisis de Seguimiento de Mano de Obra")
st.write("Sube tu archivo de Excel para analizar los incumplimientos de rotación y asignaciones prolongadas.")

# --- Sección para subir el archivo ---
uploaded_file = st.file_uploader("Sube el archivo 'Seguimiento de Mano de obra.xlsx'", type=["xlsx"])

# Solo ejecuta el resto del código si se ha subido un archivo
if uploaded_file:
    # Cargar y leer los datos
    df = pd.read_excel(uploaded_file)
    st.success("¡Archivo cargado exitosamente!")
    
    # Muestra las primeras filas para que el usuario pueda verificar
    st.subheader("Datos Cargados (Primeras 5 Filas)")
    st.dataframe(df.head())

    # --- PASO 1: Preparar y Limpiar Datos ---
    try:
        df['Año'] = pd.to_numeric(df['Año'])
        df['Semana'] = pd.to_numeric(df['Semana'])
        
        df['Nombre'] = df['Nombre'].astype(str).str.strip()
        df['Turno'] = df['Turno'].astype(str).str.strip()
        df['Linea'] = df['Linea'].astype(str).str.strip()
        df['Horno'] = df['Horno'].astype(str).str.strip()
        df['Cargo'] = df['Cargo'].astype(str).str.strip()
        
        df = df.sort_values(by=['Nombre', 'Año', 'Semana']).reset_index(drop=True)
        
    except KeyError as e:
        st.error(f"Error: La columna esperada no se encuentra en el archivo. Faltan las columnas: {e}. Por favor, verifica el nombre de las columnas.")
        st.stop() # Detiene la ejecución del script si hay un error
    
    # --- PASO 2: Crear la Clave de "Grupo de Trabajo" ---
    df['Clave_grupo_trabajo'] = df['Nombre'] + '_' + \
                                df['Turno'] + '_' + \
                                df['Linea'] + '_' + \
                                df['Horno'] + '_' + \
                                df['Cargo']

    # --- PASO 3: Calcular Semanas Consecutivas ---
    # La lógica para 'semanas_consecutivas_rotacion' es idéntica a la de tu script original.
    # Aquí puedes pegar esa parte sin cambios.
    # Inicializar nueva columna
    df['semanas_consecutivas_rotacion'] = 0
    # ... [PEGA TU BUCLE FOR COMPLETO PARA EL CÁLCULO AQUÍ] ...

    # Ejemplo del bucle a pegar
    for i in range(len(df)):
        if i == 0:
            df.loc[i, 'semanas_consecutivas_rotacion'] = 1
        else:
            nombre_actual = df.loc[i, 'Nombre']
            clave_grupo_actual = df.loc[i, 'Clave_grupo_trabajo']
            año_actual = df.loc[i, 'Año']
            semana_actual = df.loc[i, 'Semana']

            nombre_anterior = df.loc[i-1, 'Nombre']
            clave_grupo_anterior = df.loc[i-1, 'Clave_grupo_trabajo']
            año_anterior = df.loc[i-1, 'Año']
            semana_anterior = df.loc[i-1, 'Semana']
            semanas_consecutivas_anterior = df.loc[i-1, 'semanas_consecutivas_rotacion']

            if (nombre_actual == nombre_anterior) and (clave_grupo_actual == clave_grupo_anterior):
                is_consecutive_week = False
                if año_actual == año_anterior and semana_actual == semana_anterior + 1:
                    is_consecutive_week = True
                elif (año_actual == año_anterior + 1) and (semana_actual == 1) and (semana_anterior >= 52):
                    is_consecutive_week = True
            
                if is_consecutive_week:
                    df.loc[i, 'semanas_consecutivas_rotacion'] = semanas_consecutivas_anterior + 1
                else:
                    df.loc[i, 'semanas_consecutivas_rotacion'] = 1
            else:
                df.loc[i, 'semanas_consecutivas_rotacion'] = 1

    # CÁLCULO DE SEMANAS CONSECUTIVAS PARA "SIN ASIGNAR"
    df_sin_asignar = df[df['Cargo'].str.contains('sin asignar', case=False, na=False)].copy()
    if not df_sin_asignar.empty:
        df_sin_asignar = df_sin_asignar.sort_values(by=['Nombre', 'Año', 'Semana']).reset_index(drop=True)
        df_sin_asignar['semanas_sin_asignar_consecutivas'] = 0
        
        # ... [PEGA TU BUCLE FOR COMPLETO PARA EL CÁLCULO 'SIN ASIGNAR' AQUÍ] ...
        for i in range(len(df_sin_asignar)):
            if i == 0:
                df_sin_asignar.loc[i, 'semanas_sin_asignar_consecutivas'] = 1
            else:
                nombre_actual_sa = df_sin_asignar.loc[i, 'Nombre']
                año_actual_sa = df_sin_asignar.loc[i, 'Año']
                semana_actual_sa = df_sin_asignar.loc[i, 'Semana']

                nombre_anterior_sa = df_sin_asignar.loc[i-1, 'Nombre']
                año_anterior_sa = df_sin_asignar.loc[i-1, 'Año']
                semana_anterior_sa = df_sin_asignar.loc[i-1, 'Semana']
                semanas_consecutivas_anterior_sa = df_sin_asignar.loc[i-1, 'semanas_sin_asignar_consecutivas']

                if nombre_actual_sa == nombre_anterior_sa:
                    is_consecutive_week_sa = False
                    if año_actual_sa == año_anterior_sa and semana_actual_sa == semana_anterior_sa + 1:
                        is_consecutive_week_sa = True
                    elif (año_actual_sa == año_anterior_sa + 1) and (semana_actual_sa == 1) and (semana_anterior_sa >= 52):
                        is_consecutive_week_sa = True
                    
                    if is_consecutive_week_sa:
                        df_sin_asignar.loc[i, 'semanas_sin_asignar_consecutivas'] = semanas_consecutivas_anterior_sa + 1
                    else:
                        df_sin_asignar.loc[i, 'semanas_sin_asignar_consecutivas'] = 1
                else:
                    df_sin_asignar.loc[i, 'semanas_sin_asignar_consecutivas'] = 1
    
    # --- PASO 4: Identificar y Reportar los Incumplimientos ---
    st.header("Análisis de Incumplimientos")
    
    # Reporte de Incumplimientos de Rotación
    limite_semanas_rotacion = 16
    incumplimientos_rotacion_raw = df[df['semanas_consecutivas_rotacion'] > limite_semanas_rotacion].copy()
    if not incumplimientos_rotacion_raw.empty:
        incumplimientos_rotacion_consolidados = incumplimientos_rotacion_raw.loc[incumplimientos_rotacion_raw.groupby('Clave_grupo_trabajo')['semanas_consecutivas_rotacion'].idxmax()]
        incumplimientos_rotacion_consolidados = incumplimientos_rotacion_consolidados.sort_values(by=['Nombre', 'Año', 'Semana'])
        st.subheader(f"⚠️ Incumplimientos de Rotación (más de {limite_semanas_rotacion} semanas)")
        st.dataframe(incumplimientos_rotacion_consolidados[['Nombre', 'Año', 'Semana', 'Turno', 'Linea', 'Horno', 'Cargo', 'semanas_consecutivas_rotacion']])
    else:
        st.success(f"✅ ¡Felicitaciones! No se encontraron incumplimientos de rotación (límite: {limite_semanas_rotacion} semanas).")

    # Reporte de Incumplimientos de "Sin Asignar"
    limite_semanas_sin_asignar = 1
    if not df_sin_asignar.empty:
        incumplimientos_sin_asignar_raw = df_sin_asignar[df_sin_asignar['semanas_sin_asignar_consecutivas'] > limite_semanas_sin_asignar].copy()
        if not incumplimientos_sin_asignar_raw.empty:
            incumplimientos_sin_asignar_consolidados = incumplimientos_sin_asignar_raw.loc[incumplimientos_sin_asignar_raw.groupby('Nombre')['semanas_sin_asignar_consecutivas'].idxmax()]
            incumplimientos_sin_asignar_consolidados = incumplimientos_sin_asignar_consolidados.sort_values(by=['Nombre', 'Año', 'Semana'])
            st.subheader(f"⚠️ Incumplimientos 'Sin Asignar' (más de {limite_semanas_sin_asignar} semana)")
            st.dataframe(incumplimientos_sin_asignar_consolidados[['Nombre', 'Año', 'Semana', 'Cargo', 'semanas_sin_asignar_consecutivas']])
        else:
            st.success(f"✅ ¡Felicitaciones! No se encontraron incumplimientos 'Sin Asignar' (límite: {limite_semanas_sin_asignar} semana).")
    else:
        st.info("No se encontraron registros con el cargo 'Sin Asignar' en el archivo.")