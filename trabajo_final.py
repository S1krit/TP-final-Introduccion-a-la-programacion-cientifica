# para ejecutar: streamlit run trabajo_final.py
# desde el VScode: python -m streamlit run trabajo_final.py


import pandas as pd
import matplotlib.pyplot as plt
from pandas.tseries.offsets import Minute
import streamlit as st
import datetime

import os
import io
import seaborn as sns
from io import BytesIO
from fpdf import FPDF
# pip install openpyxl // usamos una libreria pedia esto de dependencia
# en algun momento usar // import io // es para podes hacer la descarga de informe

#ideas:
# - agregar un pie de pagina con nuestros nombres y correos
# - un boton para poner modo claro y modo oscuro
# - hacer un boton para guardar los resultados en un archivo
# - VALIDACION DE DATOS: Si no se cargan datos, mostrar un mensaje de error. Resaltar valores faltantes o incorrectos en rojo, con mensajes explicativos.

st.set_page_config(page_title='Análisis de Datos Solares', layout= "wide")
st.title('Análisis de Datos Solares')

st.logo("logo_UTN_removebg_preview.png",size="large", link="https://www.frsf.utn.edu.ar/")

t1, t2, t3, = st.tabs(['🌐 General', '📊 Cálculos', '⬇️ Descargas'])

with t1:  #caratula y cargar el archivo

  with st.expander("Formato esperado del archivo excel", expanded=False):

    tabla_ejemplo = pd.DataFrame({
        "Fecha": ["2024-01-01", "2024-01-02", "2024-01-03", "..."],
        "Temperatura (°C)": [25.4, 26.1, 24.8, "..."],
        "Irradiancia (W/m²)": [500, 520, 490, "..."],
    })

    st.dataframe(tabla_ejemplo)

  archivo_subido = st.file_uploader("Cargar un archivo excel (.xlsx)", type=["xlsx"])

  if archivo_subido is not None:
    try:
        archivo_pasado_a_pandas = pd.read_excel(archivo_subido, index_col=0)
       
        filas_vacias= archivo_pasado_a_pandas.isnull().all(axis=1)
        celdas_vacias= archivo_pasado_a_pandas.isnull().sum().sum()
    
        numero_columnas = len(archivo_pasado_a_pandas.columns)
        if numero_columnas > 2:
            st.error("⚠️ERROR⚠️: El archivo tiene más de 3 columnas, esto podría causar problemas en el análisis de datos, por favor corregir antes de continuar")
        elif numero_columnas < 2:
            st.error("⚠️ERROR⚠️: El archivo tiene menos de 3 columnas, esto podria causar problemas en el analisis de datos, por favor corregir antes de continuar")
        else:
            columnas_esperadas= ['Irradiancia (W/m²)', 'Temperatura (°C)']
            columnas_subias= archivo_pasado_a_pandas.columns.tolist()

            if columnas_subias[:2] == columnas_esperadas:
                    
                if not filas_vacias.any():
                    if  celdas_vacias>0:
                        st.error("⚠️ERROR⚠️: El archivo contiene celdas en blanco, esto podría causar problemas en el análisis de datos, por favor corregir antes de continuar")

                    else:
                        st.success("✅ Archivo cargado correctamente")
                        with st.expander("Vista previa de datos", expanded=False):
                            st.table(archivo_pasado_a_pandas)
        
                else:
                    st.error("⚠️ERROR⚠️: El archivo contiene filas en blanco, esto podría causar problemas en el análisis de datos, por favor corregir antes de continuar")
            
            else:
                st.error("⚠️ERROR⚠️: El archivo tiene las columnas de Irradiancia (W/m²) y Temperatura (°C) invertidas, por favor corregir antes de continuar")

    except Exception as e:
        st.error(f"⚠️Error⚠️ al leer el archivo: {e}")


    col_irradiancia, col_temperatura = archivo_pasado_a_pandas.columns

with st.sidebar:
  "Parametros de la instalación fotovoltaica"

  valores_predeterminados_UTN = st.button(
      "Usar valores de la instalación en la UTN")

  cantidad_de_paneles = st.number_input(
      "Cantidad de módulos fotovoltaicos",
      min_value=1,
      value=12 if valores_predeterminados_UTN else 1,
      step=1)

  G_estandar = st.number_input(
      "Irradiancia estandar [W/m^2]",
      min_value=0.00,
      value=1000.00 if valores_predeterminados_UTN else 1000.00,
      step=0.01)

  T_de_referencia = st.number_input(
      "Temperatura de referencia [°C]",
      min_value=0.00,
      max_value=50.00,
      value=25.00 if valores_predeterminados_UTN else 25.00,
      step=0.01)

  P_pico = st.number_input(
      "Potencia pico de cada módulo [W]",
      min_value=0.00,
      max_value=380.00,
      value=240.00 if valores_predeterminados_UTN else 220.00,
      step=0.01)

  P_del_inversor = st.number_input(
      "Potencia nominal del inversor [kW]",
      min_value=0.00,
      value=2500.00 if valores_predeterminados_UTN else 2000.00,
      step=0.01)

  k_de_temperatura_potencia = st.number_input(
      "Coeficiente de Temperatura-Potencia [°C^(-1)]",
      min_value=-10.0000,
      max_value=0.0000,
      value=-0.0044 if valores_predeterminados_UTN else -0.0050,
      step=0.0001,
      format="%0.4f")

  rendimiento = st.number_input(
      "Rendimientoglobal de la instalación",
      min_value=0.01,
      max_value=1.00,
      value=0.97 if valores_predeterminados_UTN else 1.00,
      step=0.01)

  if valores_predeterminados_UTN is True:
    valores_personalizados = st.button("Personalizar valores")

    if valores_personalizados is True:
      valores_predeterminados_UTN = False

  st.markdown("---")
  st.markdown(r"""
  ###Autores:<br>
  Renk, Santiago:<br>
  santirenk2004@gmail.com<br>
  Schmuth Gassmann, Katerina:<br>
  katerinaschmuth@hotmail.com
  """, unsafe_allow_html=True)


with t2:  #resultados para la instalacion fotvoltaica (calculos)

  if archivo_subido is not None:  # Cálculos relacionados a la potencia generada

    # Corrección para la temperatura real ec(3)
    archivo_pasado_a_pandas['Temperatura (°C)'] = archivo_pasado_a_pandas[col_temperatura] + \
                                                  0.031 * archivo_pasado_a_pandas[col_irradiancia]

    # Cálculo de la potencia del panel ec(1):
    potencia_generada = cantidad_de_paneles * (archivo_pasado_a_pandas[col_irradiancia] / G_estandar) * P_pico * (1 + (k_de_temperatura_potencia *(archivo_pasado_a_pandas[col_temperatura] - T_de_referencia))) * rendimiento

    # Agrego la potencia al archivo pasado a pandas:
    archivo_pasado_a_pandas['Potencia Generada (kW)'] = potencia_generada

    # Corrección para la potencia real ec(4)
    P_min = (0.1 / 100) * P_del_inversor

    archivo_pasado_a_pandas['Potencia Generada (kW)'] = archivo_pasado_a_pandas['Potencia Generada (kW)'].apply(lambda x: 0 if x< P_min else(P_del_inversor if x> P_del_inversor else x))

    t5, t6, t7 = st.tabs(["Resultados anuales", "Análisis puntual", "Bibliografía de cálculos"])

    with t5:  # Graficas anuales (no modificables)

      # Obtener una lista de los años disponibles en los datos
      anos_disponibles = archivo_pasado_a_pandas.index.year.unique()

      # Crear un selector de año para que el usuario elija
      ano_seleccionado = st.selectbox('Seleccione el año que desea visualizar', anos_disponibles)

      # Filtrar los datos para el año seleccionado
      datos_ano_seleccionado = archivo_pasado_a_pandas[archivo_pasado_a_pandas.index.year == ano_seleccionado]

      
      # Verificar si hay datos para el año seleccionado
      if datos_ano_seleccionado.empty:
        st.error(f"⚠️ No se cuentan con los datos del año {ano_seleccionado} en la base de datos.")
      else:
        # Resumen de Resultados
        st.write(f"### Resumen de Resultados del Año {ano_seleccionado}")

        #se crea una tabla con los valores promedio de cada mes
        datos_ano_resumido_por_mes = datos_ano_seleccionado.resample('M').mean()
        
        col1, col2= st.columns(2)
        # Mostrar los datos del año seleccionado
        with col1:
          with st.expander(f"### Datos del Año {ano_seleccionado}", expanded=False):
            st.dataframe(datos_ano_seleccionado)
        
        # Mostrar los datos promedio del año
        with col2:
          with st.expander("Datos Promedio Mensuales", expanded=False):
            st.dataframe(datos_ano_resumido_por_mes)
        
        # Gráfico de irradiancia promedio mensual
        st.write(f"#### Gráfico de Irradiancia Promedio Mensual en {ano_seleccionado} (W/m²)")
        col3, col4= st.columns([3, 1])
        with col3:
          st.line_chart(datos_ano_resumido_por_mes['Irradiancia (W/m²)'], y_label="Irradiancia Promedio Mensual (W/m²)", color= "#0000ff" , use_container_width=True)

        with col4:
          st.metric(f"Máximo: {datos_ano_resumido_por_mes['Irradiancia (W/m²)'].idxmax().strftime('%B')}", value=f"{datos_ano_resumido_por_mes['Irradiancia (W/m²)'].max():.2f} W/m²", border=True)
          st.metric(f"Mínimo: {datos_ano_resumido_por_mes['Irradiancia (W/m²)'].idxmin().strftime('%B')}", value=f"{datos_ano_resumido_por_mes['Irradiancia (W/m²)'].min():.2f} W/m²", border=True)
          st.metric("Promedio anual:", value= f"{datos_ano_resumido_por_mes['Irradiancia (W/m²)'].mean():.2f} W/m²", border=True)

        # Gráfico de temperatura promedio mensual
        st.write(f"#### Gráfico de Temperatura Promedio Mensual en {ano_seleccionado} (°C)")
        col5, col6= st.columns([1, 3])
        with col5:
          st.metric(f"Máximo: {datos_ano_resumido_por_mes['Temperatura (°C)'].idxmax().strftime('%B')}", value=f"{datos_ano_resumido_por_mes['Temperatura (°C)'].max():.2f} °C", border=True)
          st.metric(f"Mínimo: {datos_ano_resumido_por_mes['Temperatura (°C)'].idxmin().strftime('%B')}", value=f"{datos_ano_resumido_por_mes['Temperatura (°C)'].min():.2f} °C", border=True)
          st.metric("Promedio anual:", value= f"{datos_ano_resumido_por_mes['Temperatura (°C)'].mean():.2f} °C", border=True)

        with col6:
          st.line_chart(datos_ano_resumido_por_mes['Temperatura (°C)'], y_label="Temperatura Promedio Mensual (°C)",color="#ff0000" ,use_container_width=True)

        # Gráfico de potencia generada promedio mensual
        st.write(f"#### Gráfico de Potencia Generada Promedio Mensual en {ano_seleccionado} (kW)")
        col7, col8= st.columns([3, 1])
        with col7:
          st.line_chart(datos_ano_resumido_por_mes['Potencia Generada (kW)'], y_label='Potencia Generada (kW)',color="#00ff00", use_container_width=True)

        with col8:
          st.metric(f"Máximo: {datos_ano_resumido_por_mes['Potencia Generada (kW)'].idxmax().strftime('%B')}", value=f"{datos_ano_resumido_por_mes['Potencia Generada (kW)'].max():.2f} kW", border=True)
          st.metric(f"Mínimo: {datos_ano_resumido_por_mes['Potencia Generada (kW)'].idxmin().strftime('%B')}", value=f"{datos_ano_resumido_por_mes['Potencia Generada (kW)'].min():.2f} kW", border=True)
          st.metric("Promedio anual:", value= f"{datos_ano_resumido_por_mes['Potencia Generada (kW)'].mean():.2f} kW", border=True)

    with t6:  #graficas en funcion de que quira ver el usuario

      st.header("Análisis Puntual por Rango de Fechas")

      fecha_inicial= archivo_pasado_a_pandas.index.min().strftime('%Y-%m-%d')

      fecha_inicial_temp= pd.to_datetime(fecha_inicial)
      fecha_por_precaucion= fecha_inicial_temp + datetime.timedelta(days=1)

      fecha_final= archivo_pasado_a_pandas.index.max().strftime('%Y-%m-%d')

      inicio_del_grafico, fin_del_grafico= st.date_input("¿Qué periodo desea analizar?", value=(fecha_inicial, fecha_por_precaucion), min_value= fecha_inicial, max_value= fecha_final, format= "DD/MM/YYYY")

      fin_del_grafico= fin_del_grafico + datetime.timedelta(days=1)

      inicio_del_grafico= pd.to_datetime(inicio_del_grafico)
      fin_del_grafico= pd.to_datetime(fin_del_grafico)

      rango_seleccionado= archivo_pasado_a_pandas[(archivo_pasado_a_pandas.index >= inicio_del_grafico) & (archivo_pasado_a_pandas.index <= fin_del_grafico)]

      dias_que_se_estan_analizando= fin_del_grafico - inicio_del_grafico

      col9, col10, col11, col12= st.columns(4)

      #mostrar dias analizados:
      with col9:
        st.metric("Periodo de análisis:", value=f"{dias_que_se_estan_analizando.days} Dias", border=True)

        with st.container(border=True):
          caja_de_chequeo= st.checkbox("Comparar con otra fecha", help="Se seleccionará un rago del mismo tamaño que el anterior")

          if caja_de_chequeo is True:

            maximo_permitido= pd.to_datetime(fecha_final) - dias_que_se_estan_analizando
            fecha_a_comparar= st.date_input("¿Desde que fecha desea comparar?", value=fecha_inicial, min_value= fecha_inicial, max_value= maximo_permitido)

            inicio_de_la_comparacion= pd.to_datetime(fecha_a_comparar)
            final_de_la_comparacion= inicio_de_la_comparacion + dias_que_se_estan_analizando

            rango_de_comparacion= archivo_pasado_a_pandas[(archivo_pasado_a_pandas.index >= inicio_de_la_comparacion) & (archivo_pasado_a_pandas.index <= final_de_la_comparacion)]

            activar_comparacion= st.toggle("Comparar en las gráficas")

      #mostrar max/min irradiancia:
      with col10:
        st.metric(f"Irradiacion Máxima: {rango_seleccionado['Irradiancia (W/m²)'].idxmax().strftime('%Y-%m-%d')}", value=f"{rango_seleccionado['Irradiancia (W/m²)'].max():.2f} W/m²", border=True)
        st.metric(f"Irradiacion Mínima: {rango_seleccionado['Irradiancia (W/m²)'].idxmin().strftime('%Y-%m-%d')}", value=f"{rango_seleccionado['Irradiancia (W/m²)'].min():.2f} W/m²", border=True)
        st.metric(f"Irradiancia Promedio:", value=f"{rango_seleccionado['Irradiancia (W/m²)'].mean():.2f} W/m²", border=True)
      #mostrar max/min temperatura:
      with col11:
        st.metric(f"Te,peratura Máxima: {rango_seleccionado['Temperatura (°C)'].idxmax().strftime('%Y-%m-%d')}", value=f"{rango_seleccionado['Temperatura (°C)'].max():.2f} °C", border=True)
        st.metric(f"Temperatura Mínima: {rango_seleccionado['Temperatura (°C)'].idxmin().strftime('%Y-%m-%d')}", value=f"{rango_seleccionado['Temperatura (°C)'].min():.2f} °C", border=True)
        st.metric(f"Temperatura Promedio:", value=f"{rango_seleccionado['Temperatura (°C)'].mean():.2f} °C", border=True)
      #mostrar potencia generada:°C
      with col12:
        st.metric(f"Potencia Máxima: {rango_seleccionado['Potencia Generada (kW)'].idxmax().strftime('%Y-%m-%d')}", value=f"{rango_seleccionado['Potencia Generada (kW)'].max():.2f} W", border=True)
        st.metric(f"Potencia Mínima: {rango_seleccionado['Potencia Generada (kW)'].idxmin().strftime('%Y-%m-%d')}", value=f"{rango_seleccionado['Potencia Generada (kW)'].min():.2f} W", border=True)
        st.metric(f"Potencia Promedio:", value=f"{rango_seleccionado['Potencia Generada (kW)'].mean():.2f} W", border=True)
      
      #los graficos
      if caja_de_chequeo:
        if activar_comparacion:
          
          st.title("General:")
          st.line_chart(rango_seleccionado, x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", color=("#0000ff", "#ff0000", "#00ff00"))
          st.line_chart(rango_de_comparacion, x_label=f"{inicio_de_la_comparacion.strftime('%Y-%m-%d')} - {final_de_la_comparacion.strftime('%Y-%m-%d')}", color=("#ffff00", "#00ffff", "#ff00ff"))

          st.title("Detallado")
          st.subheader("Irradiancia:")
          col13, col14= st.columns(2)
          with col13:
            st.line_chart(data= rango_seleccionado['Irradiancia (W/m²)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Irradiancia (W/m²)", color="#0000ff", use_container_width=True)
          with col14:
            st.line_chart(data= rango_de_comparacion['Irradiancia (W/m²)'], x_label=f"{inicio_de_la_comparacion.strftime('%Y-%m-%d')} - {final_de_la_comparacion.strftime('%Y-%m-%d')}", y_label="Irradiancia (W/m²)", color="#ffff00", use_container_width=True)

          st.subheader("Temperatura:")
          col15, col16= st.columns(2)
          with col15:
            st.line_chart(data= rango_seleccionado['Temperatura (°C)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Temperatura (°C)", color="#ff0000", use_container_width=True)       
          with col16:
            st.line_chart(data= rango_de_comparacion['Temperatura (°C)'], x_label=f"{inicio_de_la_comparacion.strftime('%Y-%m-%d')} - {final_de_la_comparacion.strftime('%Y-%m-%d')}", y_label="Temperatura (°C)", color="#00ffff", use_container_width=True)
          
          st.subheader("Potencia:")
          col17, col18= st.columns(2)
          with col17:
            st.line_chart(data= rango_seleccionado['Potencia Generada (kW)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Potencia Generada (kW)", color="#00ff00", use_container_width=True)
          with col18:
            st.line_chart(data= rango_de_comparacion['Potencia Generada (kW)'], x_label=f"{inicio_de_la_comparacion.strftime('%Y-%m-%d')} - {final_de_la_comparacion.strftime('%Y-%m-%d')}", y_label="Potencia Generada (kW)", color="#ff00ff", use_container_width=True)
        
        else:
          st.title("General:")
          st.line_chart(rango_seleccionado, x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", color=("#0000ff", "#ff0000", "#00ff00"))
          st.title("detallado:")
          st.subheader("Irradiancia:")
          st.line_chart(data= rango_seleccionado['Irradiancia (W/m²)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Irradiancia (W/m²)", color="#0000ff", use_container_width=True)
          st.subheader("Temperatura")
          st.line_chart(data= rango_seleccionado['Temperatura (°C)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Temperatura (°C)", color="#ff0000", use_container_width=True)
          st.subheader("Potencia")
          st.line_chart(data= rango_seleccionado['Potencia Generada (kW)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Potencia Generada (kW)", color="#00ff00", use_container_width=True)
      
      else:
        st.title("General:")
        st.line_chart(rango_seleccionado, x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", color=("#0000ff", "#ff0000", "#00ff00"))
        st.title("detallado:")
        st.subheader("Irradiancia:")
        st.line_chart(data= rango_seleccionado['Irradiancia (W/m²)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Irradiancia (W/m²)", color="#0000ff", use_container_width=True)
        st.subheader("Temperatura")
        st.line_chart(data= rango_seleccionado['Temperatura (°C)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Temperatura (°C)", color="#ff0000", use_container_width=True)
        st.subheader("Potencia")
        st.line_chart(data= rango_seleccionado['Potencia Generada (kW)'], x_label=f"{inicio_del_grafico.strftime('%Y-%m-%d')} - {fin_del_grafico.strftime('%Y-%m-%d')}", y_label="Potencia Generada (kW)", color="#00ff00", use_container_width=True)
        
    with t7:  #ventanas pequeñas donde se vean los calculos que se llevan a cabo para mostrar los resoltados

      #ecuacion de potencia
      st.markdown(r""" 
      La ecuación utilizada para calcular la potencia generada por los paneles es:
      $$
      P= N\cdot \frac{G}{G_{std}}\cdot P_{pico} \cdot [1+ k_p\cdot (T_c-T_r)] \cdot \eta \cdot 10^{-3}
      $$                 
      """)

      with st.expander("Variables", expanded=False):
        st.markdown(r"""     
        * $P$ (kW): Potencia generada por el generador fotovoltaico.
        * $N$: Cantidad de módulos fotovoltaicos instalados.
        * $G$ [W/m$^2$]: Irradiancia captada por los módulos fotovoltaicos.
        * $G_{std}$ [W/m$^2$]: Irradiancia estandar.
        * $T_r$ [C°]: Temperatura de referencia.
        * $T_c$ [C°]: Temperatura de la celda.
        * $P_{pico}$ [W]: Potencia pico de cada módulo.
        * $k_p$ [C$^{-1}$]: Coeficiente Temperatura-Potencia.
        * $\eta$: Rendimiento global de la instalación "por unidad".        
        """)

      #estimacion de T_c
      st.markdown(r""" 
      Para estimar $T_c$ se utiliza:
      $$
      T_c=T+0,031[\frac{°Cm^2}{W}]\cdot G            
      $$
      """)

      with st.expander("Variables", expanded=False):
        st.markdown(r"""
        * $T$ [°C]: Temperatura ambiente.
        * $T_r$ [C°]: Temperatura de referencia.
        * $G$ [W/m$^2$]: Irradiancia captada por los módulos fotovoltaicos.
        """)

      #Limites de generacion
      st.markdown(r"""
      Los limites de generación de los módulos fotovoltaicos estan dados por la siguiente relación:
      $$
      P_{min}= \frac{\mu (\%)}{100}\cdot P_{inv}
      $$
      """)

      st.markdown(r"""
      $$
      P_r=\begin{cases}    0 & \text{si: } P \leq P_{\text{min}} \\    P & \text{si: } P_{\text{min}} < P \leq P_{\text{inv}} \\    P_{\text{inv}} & \text{si: } P > P_{\text{inv}}\end{cases}
      $$
      """)

      with st.expander("Variables", expanded=False):
        st.markdown(r"""
        * $P_r$ (kW): Potencia real generada por el generador fotovoltaico.
        * $P$ (kW): Potencia generada por el generador fotovoltaico.
        * $P_{min}$ (kW): Potencia minima generada por el generador fotovoltaico.
        * $P_{inv}$ (kW): Potencia nominal del inversor.
        * $\mu$: Se asume 10%
        """)

with t3:  #descargas
  if archivo_subido is not None:

    st.header("Descargue un archivo exel con los datos finales de potencia:")
    descarga_de_exel_con_datos_finales= io.BytesIO()
    archivo_pasado_a_pandas.to_excel(descarga_de_exel_con_datos_finales)
    st.download_button("⬇️ Descargar tabla de resultados ⬇️", data=descarga_de_exel_con_datos_finales, file_name="Tabla con columna de potencia.xlsx")
    
    # Encabezado para la sección del informe en la aplicación
    st.header("Descargar Informe Personalizado en PDF")
  
    # Selección del tipo de análisis: Anual o por Fecha
    st.markdown("### Tipo de análisis")
    tipo_analisis = st.radio("Elija la fuente de datos para el informe:", options=["Anual", "Por Fecha"], index=1)  # Botón de selección, por defecto se elige "Por Fecha"
  
    # Determinar la fuente de datos basada en la selección del tipo de análisis
    Fuente_datos = datos_ano_seleccionado if tipo_analisis == "Anual" else rango_seleccionado
  
    # Mostrar información adicional dependiendo de la elección
    if tipo_analisis == "Por Fecha":
        st.markdown(f"**Utilizando datos del rango seleccionado en Calculos: {fecha_inicial} al {fecha_final}**")
    else:
        st.markdown("**Utilizando datos del análisis anual seleccionado en Calculos.**")
  
    # Sección para seleccionar los parámetros a incluir en el informe
    st.markdown("### Seleccione los parámetros para incluir en el informe")
    col_temp, col_irr, col_pot = st.columns(3)  # Divide la interfaz en tres columnas
  
    # Opciones para "Temperatura" dentro de la primera columna
    with col_temp:
        st.subheader("Temperatura")
        incluir_temp_max = st.checkbox("Máximo", key="temp_max")
        incluir_temp_min = st.checkbox("Mínimo", key="temp_min")
        incluir_temp_mean = st.checkbox("Promedio", key="temp_mean")
        incluir_temp_graf = st.checkbox("Gráfica", key="temp_graf")
  
    # Opciones para "Irradiancia" dentro de la segunda columna
    with col_irr:
        st.subheader("Irradiancia")
        incluir_irr_max = st.checkbox("Máximo", key="irr_max")
        incluir_irr_min = st.checkbox("Mínimo", key="irr_min")
        incluir_irr_mean = st.checkbox("Promedio", key="irr_mean")
        incluir_irr_graf = st.checkbox("Gráfica", key="irr_graf")
  
    # Opciones para "Potencia" dentro de la tercera columna
    with col_pot:
        st.subheader("Potencia")
        incluir_pot_max = st.checkbox("Máximo", key="pot_max")
        incluir_pot_min = st.checkbox("Mínimo", key="pot_min")
        incluir_pot_mean = st.checkbox("Promedio", key="pot_mean")
        incluir_pot_graf = st.checkbox("Gráfica", key="pot_graf")
  
    # Validar que al menos un parámetro esté seleccionado
    if not any([incluir_temp_max, incluir_temp_min, incluir_temp_mean, incluir_temp_graf,
                incluir_irr_max, incluir_irr_min, incluir_irr_mean, incluir_irr_graf,
                incluir_pot_max, incluir_pot_min, incluir_pot_mean, incluir_pot_graf]):
        st.error("❗Debe seleccionar al menos un parámetro o gráfico para incluir en el informe.")
        st.stop()
  
    # Crear un PDF en memoria
    # Crear un PDF en memoria
    buffer = BytesIO()  # Espacio en memoria para almacenar el PDF
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)  # Configurar saltos de página automáticos
    pdf.add_page()  # Añadir la primera página del PDF
    pdf.set_font("Arial",style='B', size=18)  # Establecer la fuente Arial y el tamaño
    pdf.cell(200, 10,"Informe de Análisis de Datos Solares", ln=True, align="C",)  # Título del informe
    pdf.ln(10)  # Añadir espacio después del título
  
    # Función para agregar contenido al PDF
    def agregar_seccion(pdf, nombre, incluir_max, incluir_min, incluir_mean, incluir_graf, columna):
        """Agrega una sección al PDF con valores y gráficas según los parámetros seleccionados."""
        try:
            # Inicializar valores temporales
            max_val, min_val, mean_val = None, None, None
            pdf.set_font("Arial", style="B", size=12)
            pdf.cell(0, 10, nombre, ln=True)

            pdf.ln(5)

            pdf.set_font("Arial", size=12)
          
            if incluir_max:
              max_val = Fuente_datos[columna].max()  # Calcular valor máximo
              pdf.cell(200, 10, f" Máximo: {max_val:.2f}", ln=True)
            
            if incluir_min:
              min_val = Fuente_datos[columna].min()  # Calcular valor mínimo
              pdf.cell(200, 10, f" Mínimo: {min_val:.2f}", ln=True)
  
            if incluir_mean:
              mean_val = Fuente_datos[columna].mean()  # Calcular valor promedio
              pdf.cell(200, 10, f"Promedio: {mean_val:.2f}", ln=True)
              
            pdf.ln(10)

              #Verificar si es necesario agregar una nueva página antes de agregar la gráfica
            y_before = pdf.get_y()  # Obtener la posición vertical actual del texto

            if incluir_graf:
                
              pdf.ln(10)  # Agregar espacio entre el texto y la imagen

              # Crear la gráfica con matplotlib
              fig, ax = plt.subplots(figsize=(6, 4))

              if tipo_analisis == "Por Fecha":
                  # Gráfico directo si el análisis es por fecha
                  Fuente_datos[columna].plot(ax=ax)
                  ax.set_title(f"Gráfico de {nombre} (Por Fecha)")
              else:
                  # Gráfico con promedios mensuales si el análisis es anual
                  datos_mensuales = Fuente_datos[columna].resample('M').mean()
                  datos_mensuales.plot(ax=ax)
                  ax.set_title(f"Gráfico de {nombre} (Promedios Mensuales)")

              ax.set_xlabel("Tiempo")
              ax.set_ylabel(nombre)

              # Guardar la gráfica temporalmente como un archivo
              temp_imagepath = f"temp_{nombre}.png"
              plt.savefig(temp_imagepath)
              plt.close(fig)

              # Insertar la imagen en el PDF
              pdf.image(temp_imagepath, x=10, y=y_before, w=180)

              # Espacio después de la gráfica
              pdf.ln(95)  # Ajusta este valor si es necesario para dar más espacio

              # Eliminar la imagen temporal
              os.remove(temp_imagepath)
            pdf.add_page()

        except KeyError:
          st.error("⚠️ No se encontró la columna en los datos.")
  
    # Agregar las secciones al PDF
    agregar_seccion(pdf, "Temperatura", incluir_temp_max, incluir_temp_min, incluir_temp_mean, incluir_temp_graf, "Temperatura (°C)")
    agregar_seccion(pdf, "Irradiancia", incluir_irr_max, incluir_irr_min, incluir_irr_mean, incluir_irr_graf, "Irradiancia (W/m²)")
    agregar_seccion(pdf, "Potencia", incluir_pot_max, incluir_pot_min, incluir_pot_mean, incluir_pot_graf, "Potencia Generada (kW)")
  
    # Guardar el contenido del PDF en el buffer
    pdf_output = pdf.output(dest="S").encode('latin1')  # Usamos .encode() para convertir el PDF a bytes
    buffer.write(pdf_output)  # Guardar los bytes en el buffer
    buffer.seek(0)  # Posicionar el puntero al inicio del buffer
  
    # Verificar si el PDF tiene contenido antes de permitir la descarga
    if buffer.getbuffer().nbytes > 0:
        file_name = f"informe_{tipo_analisis.lower()}_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf"  # Nombre del archivo PDF
        st.download_button(
            label="⬇️ Descargar Informe en PDF ⬇️",  # Texto del botón
            data=buffer,  # Contenido del archivo
            file_name=file_name,  # Nombre del archivo
            mime="application/pdf",  # Tipo MIME del archivo
            key="download-pdf"  # Clave para el botón
        )
    else:
        st.error("No se pudo generar el PDF. Verifique los datos seleccionados.")
  
    # Cerrar el buffer
    buffer.close()  # Liberar los recursos del buffer
