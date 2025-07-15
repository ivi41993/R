import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
import plotly.express as px
from pathlib import Path
 
# Configuración inicial
st.set_page_config(page_title="Calendario de Vuelos 2025", layout="wide")
 
# Fecha de inicio
START_DATE_2025 = pd.to_datetime("2025-01-01")
 
# Cargar CSS
css_path = Path("styles.css")
if css_path.exists():
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        :root {
           --bg-start: #fff0f5;
           --bg-end: #ffe6f2;
           --primary-color: #ff66b2;
           --secondary-color: #ffccd9;
           --accent-color: #ff3366;
           --text-color: #333333;
           --font-stack: 'Montserrat', 'Arial', sans-serif;
           --border-radius: 8px;
           --transition-speed: 0.4s;
           --box-shadow-default: 0 4px 6px rgba(255,102,178,0.3);
           --box-shadow-hover: 0 8px 12px rgba(255,102,178,0.5);
        }
        .stApp {
            background: linear-gradient(135deg, var(--bg-start), var(--bg-end));
            background-size: 200% 200%;
            animation: subtleGlitter 12s ease infinite;
        }
        @keyframes subtleGlitter {
            0% { background-position: 0% 0%; }
            50% { background-position: 100% 100%; }
            100% { background-position: 0% 0%; }
        }
        h1, h2, h3 {
            color: var(--text-color);
            font-family: var(--font-stack);
            margin-bottom: 0.5em;
        }
        .stDataFrame, .stSelectbox, .stMultiSelect {
            background: #fff;
            border: 1px solid var(--primary-color);
            border-radius: var(--border-radius);
            padding: 12px;
            box-shadow: var(--box-shadow-default);
        }
        .stDataFrame:hover, .stSelectbox:hover, .stMultiSelect:hover {
            box-shadow: var(--box-shadow-hover);
            border-color: var(--accent-color);
            transform: translateY(-3px);
        }
        .stButton > button {
            background: var(--primary-color);
            color: var(--text-color);
            border-radius: var(--border-radius);
        }
        .stButton > button:hover {
            background: var(--secondary-color);
            box-shadow: var(--box-shadow-hover);
        }
        .dashboard-table {
            width: 100%;
            border-collapse: collapse;
            background: var(--bg-end);
            border: 1px solid var(--primary-color);
            border-radius: var(--border-radius);
            font-size: 0.9em;
        }
        .dashboard-table th, .dashboard-table td {
            padding: 8px;
            text-align: center;
            border: 1px solid var(--primary-color);
        }
        .dashboard-table th {
            background: var(--secondary-color);
            color: var(--text-color);
            font-weight: bold;
        }
        .dashboard-table td {
            background: #fff;
        }
        .summary-box {
            padding: 10px;
            border: 1px solid var(--primary-color);
            border-radius: var(--border-radius);
            background: var(--secondary-color);
            margin-top: 10px;
            font-size: 0.9em;
        }
        @media (max-width: 768px) {
            h1 { font-size: 1.8rem; }
 Stuart: h2 { font-size: 1.4rem; }
            h3 { font-size: 1.2rem; }
            .dashboard-table { font-size: 0.85em; }
        }
    </style>
    """, unsafe_allow_html=True)
 
# Funciones auxiliares
def convert_time_format(time_str):
    """Convierte formato de tiempo numérico a HH:MM."""
    if pd.isna(time_str):
        return "N/A"
    try:
        time_str = str(int(time_str)).zfill(4)
        return f"{time_str[:2]}:{time_str[2:]}"
    except (ValueError, TypeError):
        return "N/A"
 
def parse_time(time_str):
    """Convierte hora en formato HH:MM a datetime para cálculos horarios."""
    if time_str == "N/A":
        return None
    try:
        return datetime.strptime(time_str, "%H:%M")
    except (ValueError, TypeError):
        return None
 
def expand_flight_dates(df, source_file):
    """Expande fechas de vuelos, añadiendo la fuente del archivo y la compañía."""
    all_flights = []
   
    for _, row in df.iterrows():
        try:
            start_date = max(pd.to_datetime(row['from_date']), START_DATE_2025)
            end_date = pd.to_datetime(row['until_date'])
            weekdays = [int(d) for d in str(row['weekday']) if d.isdigit()]
           
            date_range = pd.date_range(start_date, end_date, freq='D')
            valid_dates = [d for d in date_range if (d.weekday() + 1) in weekdays]
           
            for date in valid_dates:
                all_flights.append({
                    'flight_number': row['fltno'],
                    'date': date,
                    'day_name': calendar.day_name[date.weekday()],
                    'departure_time': convert_time_format(row['departure_time']) if row['A/D'] == 'D' else 'N/A',
                    'arrival_time': convert_time_format(row['arrival_time']) if row['A/D'] == 'A' else 'N/A',
                    'origin': row['origin'],
                    'destination': row['dest'],
                    'flight_type': row['flight_type'],
                    'station': row['STATION'],
                    'type': row['A/D'],
                    'aircraft_type': row.get('actypeadv', 'N/A'),
                    'source_file': source_file,
                    'carrier': row['carrier']
                })
        except (ValueError, TypeError) as e:
            st.warning(f"Error al procesar fila en {source_file}: {e}")
            continue
   
    return pd.DataFrame(all_flights)
 
def render_flight_table(df, title, columns, key_prefix):
    """Función reutilizable para mostrar tablas de vuelos."""
    if len(df) == 0:
        st.info(f"No hay datos para {title.lower()}.")
        return
   
    months = sorted(df['month'].unique())
    month_tabs = st.tabs([calendar.month_name[m] + f" {df[df['month'] == m]['year'].iloc[0]}" for m in months])
   
    for tab, month in zip(month_tabs, months):
        with tab:
            month_df = df[df['month'] == month].sort_values('date')
            weeks = sorted(month_df['week'].unique())
            week_options = [
                f"Semana {w} ({month_df[month_df['week'] == w]['date'].min().strftime('%Y-%m-%d')} - "
                f"{month_df[month_df['week'] == w]['date'].max().strftime('%Y-%m-%d')})"
                for w in weeks
            ]
           
            selected_weeks = st.multiselect("Seleccionar semanas", week_options, key=f"{key_prefix}_weeks_{month}")
            if selected_weeks:
                selected_week_numbers = [int(w.split()[1]) for w in selected_weeks]
                month_df = month_df[month_df['week'].isin(selected_week_numbers)]
           
            page_size = st.slider("Filas por página", 10, 1000, 100, step=10, key=f"{key_prefix}_size_{month}")
            total_rows = len(month_df)
            total_pages = (total_rows + page_size - 1) // page_size
            page = st.number_input("Página", 1, total_pages, 1, key=f"{key_prefix}_page_{month}")
           
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, total_rows)
           
            st.dataframe(
                month_df.iloc[start_idx:end_idx][columns],
                column_config={
                    'flight_number': 'Nº Vuelo',
                    'day_name': 'Día',
                    'date': 'Fecha',
                    'arrival_time': 'Llegada',
                    'departure_time': 'Salida',
                    'origin': 'Origen',
                    'destination': 'Destino',
                    'flight_type': 'Tipo Vuelo',
                    'station': 'Estación',
                    'aircraft_type': 'Tipo de Avión',
                    'source_file': 'Archivo',
                    'carrier': 'Compañía'
                },
                hide_index=True,
                height=400
            )
           
            st.write(f"Mostrando filas {start_idx + 1} a {end_idx} de {total_rows}")
           
            csv = month_df.to_csv(index=False)
            st.download_button(
                label=f"Descargar CSV de {calendar.month_name[month]} ({title})",
                data=csv,
                file_name=f"horario_{title.lower()}_{month}.csv",
                mime='text/csv'
            )
 
# Configuración de la interfaz
st.title(" Calendario de Vuelos ")
st.write("Visualiza y filtra horarios de vuelos de múltiples estaciones por semana, día y hora.")
 
# Estado de la sesión
if 'flights_df' not in st.session_state:
    st.session_state.flights_df = pd.DataFrame()  # Inicializar como DataFrame vacío
 
# Cargar múltiples archivos
uploaded_files = st.file_uploader("Carga tus archivos Excel", type=['xlsx'], accept_multiple_files=True, key="excel_uploader")
 
if uploaded_files:
    try:
        all_dfs = []
        required_columns = ['A/D', 'fltno', 'departure_time', 'arrival_time', 'origin',
                           'dest', 'STATION', 'weekday', 'from_date', 'until_date', 'flight_type', 'actypeadv', 'carrier']
       
        for uploaded_file in uploaded_files:
            try:
                df = pd.read_excel(uploaded_file)
                if not all(col in df.columns for col in required_columns):
                    st.warning(f"El archivo {uploaded_file.name} no contiene todas las columnas requeridas (incluyendo 'carrier').")
                    continue
               
                file_df = expand_flight_dates(df, uploaded_file.name)
                if not file_df.empty:
                    all_dfs.append(file_df)
                else:
                    st.warning(f"No se generaron vuelos para el archivo {uploaded_file.name}.")
           
            except Exception as e:
                st.warning(f"Error al procesar el archivo {uploaded_file.name}: {e}")
                continue
       
        if not all_dfs:
            st.error("No se pudieron procesar los archivos cargados.")
            st.session_state.flights_df = pd.DataFrame()
        else:
            # Combinar todos los DataFrames
            st.session_state.flights_df = pd.concat(all_dfs, ignore_index=True)
            flights_df = st.session_state.flights_df
    except Exception as e:
        st.error(f"Error general al procesar los archivos: {e}")
        st.session_state.flights_df = pd.DataFrame()
else:
    st.info("Por favor, carga uno o más archivos Excel para comenzar.")
 
# Procesamiento de datos
flights_df = st.session_state.flights_df
 
if len(flights_df) == 0:
    st.warning("No se generaron vuelos a partir de los datos proporcionados.")
else:
    flights_df['date'] = pd.to_datetime(flights_df['date'])
    flights_df['year'] = flights_df['date'].dt.year
    flights_df['month'] = flights_df['date'].dt.month
    flights_df['week'] = flights_df['date'].dt.isocalendar().week
               
    # Filtrar a partir de 2025
    flights_df = flights_df[flights_df['date'] >= START_DATE_2025]
               
    if len(flights_df) == 0:
        st.warning("No hay vuelos a partir de 2025.")
    else:
        # Filtros generales
        st.subheader("Filtros Generales")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            stations = st.multiselect("Estación", options=sorted(flights_df['station'].unique()), key="stations")
        with col2:
            flight_types = st.multiselect("Tipo de vuelo", options=sorted(flights_df['flight_type'].unique()), key="flight_types")
        with col3:
            dates = st.multiselect("Fechas", options=sorted(flights_df['date'].dt.strftime('%Y-%m-%d').unique()), key="dates")
        with col4:
            sources = st.multiselect("Archivo", options=sorted(flights_df['source_file'].unique()), key="sources")
        with col5:
            carriers = st.multiselect("Compañía", options=sorted(flights_df['carrier'].unique()), key="carriers")
        with col6:
            aircraft_types = st.multiselect("Tipo de Avión", options=sorted(flights_df['aircraft_type'].unique()), key="aircraft_types")
                   
        # Aplicar filtros
        filtered_df = flights_df
        if stations:
            filtered_df = filtered_df[filtered_df['station'].isin(stations)]
        if flight_types:
            filtered_df = filtered_df[filtered_df['flight_type'].isin(flight_types)]
        if dates:
            filtered_df = filtered_df[filtered_df['date'].dt.strftime('%Y-%m-%d').isin(dates)]
        if sources:
            filtered_df = filtered_df[filtered_df['source_file'].isin(sources)]
        if carriers:
            filtered_df = filtered_df[filtered_df['carrier'].isin(carriers)]
        if aircraft_types:
            filtered_df = filtered_df[filtered_df['aircraft_type'].isin(aircraft_types)]
                   
        # Dashboard Semanal
        st.subheader("Dashboard Semanal")
        months = filtered_df[['year', 'month']].drop_duplicates().reset_index(drop=True)
        months['month_name'] = months.apply(lambda x: f"{calendar.month_name[x['month']]} {x['year']}", axis=1)
        month_options = sorted(months['month_name'].tolist())
                   
        if not month_options:
            st.warning("No hay datos disponibles para los filtros seleccionados.")
        else:
            selected_month = st.selectbox("Selecciona un mes", options=month_options, key="month_select")
            selected_year = int(selected_month.split()[-1])
            selected_month_num = list(calendar.month_name).index(selected_month.split()[0])
                       
            month_df = filtered_df[(filtered_df['year'] == selected_year) & (filtered_df['month'] == selected_month_num)]
                       
            if len(month_df) == 0:
                st.warning("No hay vuelos para el mes seleccionado.")
            else:
                weeks = sorted(month_df['week'].unique())
                week_options = [
                    f"Semana {w} ({month_df[month_df['week'] == w]['date'].min().strftime('%Y-%m-%d')} - "
                    f"{month_df[month_df['week'] == w]['date'].max().strftime('%Y-%m-%d')})"
                    for w in weeks
                ]
                           
                selected_week = st.selectbox("Selecciona una semana", options=week_options, key="week_select")
                selected_week_number = int(selected_week.split()[1])
                           
                week_df = month_df[month_df['week'] == selected_week_number]
                           
                if len(week_df) == 0:
                    st.warning("No hay vuelos para la semana seleccionada.")
                else:
                    # Tabla del dashboard semanal
                    days = sorted(week_df['date'].dt.strftime('%Y-%m-%d').unique())
                    flight_types_unique = sorted(week_df['flight_type'].unique())
                    aircraft_types_unique = sorted(week_df['aircraft_type'].unique())
                               
                    data = []
                    for ftype in flight_types_unique + aircraft_types_unique:
                        row = {'Tipo': ftype}
                        for day in days:
                            if ftype in flight_types_unique:
                                count = len(week_df[(week_df['date'].dt.strftime('%Y-%m-%d') == day) &
                                                   (week_df['flight_type'] == ftype)])
                            else:
                                count = len(week_df[(week_df['date'].dt.strftime('%Y-%m-%d') == day) &
                                                   (week_df['aircraft_type'] == ftype)])
                            row[day[-5:]] = count if count > 0 else '-'
                        data.append(row)
                               
                    st.dataframe(
                        pd.DataFrame(data),
                        use_container_width=True,
                        column_config={'Tipo': st.column_config.TextColumn('Tipo', width="medium")}
                    )
                               
                    # Gráfico de resumen semanal (con paleta de alto contraste)
                    aircraft_counts = week_df['aircraft_type'].value_counts().reset_index()
                    aircraft_counts.columns = ['aircraft_type', 'count']
                    # Calcular el porcentaje
                    total_flights = aircraft_counts['count'].sum()
                    aircraft_counts['percentage'] = (aircraft_counts['count'] / total_flights * 100).round(2)
                    # Ordenar por conteo descendente
                    aircraft_counts = aircraft_counts.sort_values('count', ascending=False)
                               
                    # Crear el gráfico
                    fig = px.bar(
                        aircraft_counts,
                        x='aircraft_type',
                        y='count',
                        title=f"Total por Tipo de Avión (Semana {selected_week_number}: "
                              f"{week_df['date'].min().strftime('%Y-%m-%d')} - "
                              f"{week_df['date'].max().strftime('%Y-%m-%d')})",
                        color='aircraft_type',
                        color_discrete_sequence=px.colors.qualitative.Plotly,
                        text='count',
                        hover_data={'count': True, 'percentage': ':.2f%'}
                    )
                    # Personalizar el diseño
                    fig.update_layout(
                        xaxis_title="Tipo de Avión",
                        yaxis_title="Número de Vuelos",
                        showlegend=True,
                        font=dict(family="Montserrat, Arial, sans-serif", size=12),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        xaxis_tickangle=45,
                        margin=dict(l=50, r=50, t=100, b=100),
                        yaxis=dict(gridcolor="lightgray"),
                        hoverlabel=dict(bgcolor="white", font_size=12)
                    )
                    fig.update_traces(
                        textposition='auto',
                        textfont=dict(size=12, color="black")
                    )
                    st.plotly_chart(fig, use_container_width=True)
                               
                    # Gráfico: Distribución día a día por tipo de avión (con paleta de alto contraste)
                    # Generar todos los días de la semana seleccionada
                    week_start = week_df['date'].min()
                    week_end = week_df['date'].max()
                    week_days = pd.date_range(start=week_start, end=week_end, freq='D')
                    all_days_df = pd.DataFrame({'date': week_days})
                    all_days_df['day_label'] = all_days_df['date'].apply(
                        lambda x: f"{calendar.day_name[x.weekday()]} {x.strftime('%Y-%m-%d')}"
                    )
                   
                    # Obtener conteos por día y tipo de avión
                    daily_aircraft_counts = week_df.groupby(['date', 'aircraft_type']).size().reset_index(name='count')
                   
                    # Crear DataFrame con todas las combinaciones de días y tipos de avión
                    all_combinations = pd.DataFrame(
                        [(d, a) for d in week_days for a in aircraft_types_unique],
                        columns=['date', 'aircraft_type']
                    )
                   
                    # Unir con los conteos, rellenando con 0 donde no hay datos
                    daily_aircraft_counts = all_combinations.merge(
                        daily_aircraft_counts,
                        on=['date', 'aircraft_type'],
                        how='left'
                    ).fillna({'count': 0})
                    daily_aircraft_counts['count'] = daily_aircraft_counts['count'].astype(int)
                    daily_aircraft_counts['day_label'] = daily_aircraft_counts['date'].apply(
                        lambda x: f"{calendar.day_name[x.weekday()]} {x.strftime('%Y-%m-%d')}"
                    )
                   
                    # Mostrar tabla de depuración para verificar datos
                    st.subheader("Datos para el Gráfico (Depuración)")
                    st.dataframe(
                        daily_aircraft_counts[['day_label', 'aircraft_type', 'count']],
                        column_config={
                            'day_label': 'Día',
                            'aircraft_type': 'Tipo de Avión',
                            'count': 'Número de Vuelos'
                        },
                        hide_index=True
                    )
                   
                    # Crear el gráfico lineal
                    fig_daily = px.line(
                        daily_aircraft_counts,
                        x='day_label',
                        y='count',
                        color='aircraft_type',
                        title=f"Distribución de Vuelos por Día y Tipo de Avión (Semana {selected_week_number}: "
                              f"{week_df['date'].min().strftime('%Y-%m-%d')} - "
                              f"{week_df['date'].max().strftime('%Y-%m-%d')})",
                        markers=True,
                        color_discrete_sequence=px.colors.qualitative.Plotly,
                        hover_data={'count': True, 'aircraft_type': True}
                    )
                    fig_daily.update_layout(
                        xaxis_title="Día de la Semana",
                        yaxis_title="Número de Vuelos",
                        showlegend=True,
                        font=dict(family="Montserrat, Arial, sans-serif", size=12),
                        plot_bgcolor="white",
                        paper_bgcolor="white",
                        xaxis_tickangle=45,
                        margin=dict(l=50, r=50, t=100, b=100),
                        yaxis=dict(gridcolor="lightgray"),
                        hoverlabel=dict(bgcolor="white", font_size=12),
                        xaxis=dict(
                            categoryorder='array',
                            categoryarray=[
                                f"{calendar.day_name[d.weekday()]} {d.strftime('%Y-%m-%d')}"
                                for d in week_days
                            ]
                        )
                    )
                    fig_daily.update_traces(
                        mode='lines+markers+text',
                        line=dict(width=4),
                        marker=dict(size=12),
                        text=daily_aircraft_counts['count'].where(daily_aircraft_counts['count'] > 0),
                        textposition='top center',
                        textfont=dict(size=12, color="black")
                    )
                    st.plotly_chart(fig_daily, use_container_width=True)
                               
                    # Dashboard Diario
                    st.subheader("Dashboard Diario")
                    day_options = [
                        f"{calendar.day_name[pd.to_datetime(day).weekday()]} {day}"
                        for day in sorted(week_df['date'].dt.strftime('%Y-%m-%d').unique())
                    ]
                               
                    selected_day = st.selectbox("Selecciona un día", options=day_options, key="day_select")
                    selected_day_date = selected_day.split()[-1]
                               
                    day_df = week_df[week_df['date'].dt.strftime('%Y-%m-%d') == selected_day_date]
                               
                    if len(day_df) == 0:
                        st.warning("No hay vuelos para el día seleccionado.")
                    else:
                        # Tabla del dashboard diario
                        data_day = []
                        for ftype in flight_types_unique + aircraft_types_unique:
                            row = {'Tipo': ftype}
                            if ftype in flight_types_unique:
                                count = len(day_df[day_df['flight_type'] == ftype])
                            else:
                                count = len(day_df[day_df['aircraft_type'] == ftype])
                            row['Vuelos'] = count if count > 0 else '-'
                            data_day.append(row)
                                   
                        st.dataframe(
                            pd.DataFrame(data_day),
                            use_container_width=True,
                            column_config={
                                'Tipo': st.column_config.TextColumn('Tipo', width="medium"),
                                'Vuelos': st.column_config.TextColumn('Vuelos')
                            }
                        )
                                   
                        # Gráfico de resumen diario (con paleta de alto contraste)
                        aircraft_counts_day = day_df['aircraft_type'].value_counts().reset_index()
                        aircraft_counts_day.columns = ['aircraft_type', 'count']
                        # Calcular el porcentaje
                        total_flights_day = aircraft_counts_day['count'].sum()
                        aircraft_counts_day['percentage'] = (aircraft_counts_day['count'] / total_flights_day * 100).round(2)
                        # Ordenar por conteo descendente
                        aircraft_counts_day = aircraft_counts_day.sort_values('count', ascending=False)
                                   
                        fig_day = px.bar(
                            aircraft_counts_day,
                            x='aircraft_type',
                            y='count',
                            title=f"Total por Tipo de Avión ({selected_day})",
                            color='aircraft_type',
                            color_discrete_sequence=px.colors.qualitative.Plotly,
                            text='count',
                            hover_data={'count': True, 'percentage': ':.2f%'}
                        )
                        # Personalizar el diseño
                        fig_day.update_layout(
                            xaxis_title="Tipo de Avión",
                            yaxis_title="Número de Vuelos",
                            showlegend=True,
                            font=dict(family="Montserrat, Arial, sans-serif", size=12),
                            plot_bgcolor="white",
                            paper_bgcolor="white",
                            xaxis_tickangle=45,
                            margin=dict(l=50, r=50, t=100, b=100),
                            yaxis=dict(gridcolor="lightgray"),
                            hoverlabel=dict(bgcolor="white", font_size=12)
                        )
                        fig_day.update_traces(
                            textposition='auto',
                            textfont=dict(size=12, color="black")
                        )
                        st.plotly_chart(fig_day, use_container_width=True)
                                   
                        # Visualización adicional 1: Tabla detallada de vuelos por día
                        st.subheader(f"Vuelos Detallados - {selected_day}")
                        day_detail_df = day_df.sort_values(['arrival_time', 'departure_time'])
                        st.dataframe(
                            day_detail_df[[
                                'flight_number', 'day_name', 'date', 'arrival_time', 'departure_time',
                                'origin', 'destination', 'flight_type', 'station', 'aircraft_type', 'carrier', 'source_file'
                            ]],
                            column_config={
                                'flight_number': 'Nº Vuelo',
                                'day_name': 'Día',
                                'date': 'Fecha',
                                'arrival_time': 'Llegada',
                                'departure_time': 'Salida',
                                'origin': 'Origen',
                                'destination': 'Destino',
                                'flight_type': 'Tipo Vuelo',
                                'station': 'Estación',
                                'aircraft_type': 'Tipo de Avión',
                                'carrier': 'Compañía',
                                'source_file': 'Archivo'
                            },
                            hide_index=True,
                            use_container_width=True
                        )
                                   
                        # Descargar CSV de vuelos diarios
                        csv_day = day_detail_df.to_csv(index=False)
                        st.download_button(
                            label=f"Descargar CSV de Vuelos ({selected_day})",
                            data=csv_day,
                            file_name=f"vuelos_{selected_day_date}.csv",
                            mime='text/csv'
                        )
                                   
                        # Visualización adicional 2: Distribución horaria (con paleta de alto contraste)
                        st.subheader(f"Distribución Horaria - {selected_day}")
                        hourly_data = []
                        for _, row in day_df.iterrows():
                            if row['type'] == 'A' and row['arrival_time'] != 'N/A':
                                time = parse_time(row['arrival_time'])
                                if time:
                                    hourly_data.append({'Hora': time.hour, 'Tipo': 'Llegada'})
                            elif row['type'] == 'D' and row['departure_time'] != 'N/A':
                                time = parse_time(row['departure_time'])
                                if time:
                                    hourly_data.append({'Hora': time.hour, 'Tipo': 'Salida'})
                                   
                        if hourly_data:
                            hourly_df = pd.DataFrame(hourly_data)
                            # Asegurar que todas las horas (0-23) estén presentes
                            all_hours = pd.DataFrame({'Hora': range(24)})
                            hourly_counts = hourly_df.groupby(['Hora', 'Tipo']).size().unstack(fill_value=0).reset_index()
                            hourly_counts = all_hours.merge(hourly_counts, on='Hora', how='left').fillna(0)
                            hourly_counts = hourly_counts.melt(id_vars='Hora', value_vars=['Llegada', 'Salida'],
                                                             var_name='Tipo', value_name='count')
                                       
                            fig_hourly = px.bar(
                                hourly_counts,
                                x='Hora',
                                y='count',
                                color='Tipo',
                                title=f"Distribución de Vuelos por Hora ({selected_day})",
                                barmode='stack',
                                color_discrete_sequence=px.colors.qualitative.Plotly[:2],
                                text='count',
                                hover_data={'count': True}
                            )
                            fig_hourly.update_layout(
                                xaxis_title="Hora del Día",
                                yaxis_title="Número de Vuelos",
                                showlegend=True,
                                font=dict(family="Montserrat, Arial, sans-serif", size=12),
                                plot_bgcolor="white",
                                paper_bgcolor="white",
                                xaxis=dict(tickmode='linear', tick0=0, dtick=1, range=[-0.5, 23.5]),
                                margin=dict(l=50, r=50, t=100, b=100),
                                yaxis=dict(gridcolor="lightgray"),
                                hoverlabel=dict(bgcolor="white", font_size=12)
                            )
                            fig_hourly.update_traces(
                                textposition='auto',
                                textfont=dict(size=12, color="black")
                            )
                            st.plotly_chart(fig_hourly, use_container_width=True)
                        else:
                            st.info("No hay datos horarios disponibles para el día seleccionado.")
                   
        # Detalles de vuelos
        st.subheader("Detalles de Vuelos")
        view_tabs = st.tabs(["Llegadas", "Salidas"])
                   
        with view_tabs[0]:
            render_flight_table(
                filtered_df[filtered_df['type'] == 'A'],
                "Llegadas",
                ['flight_number', 'day_name', 'date', 'arrival_time', 'origin', 'destination',
                 'flight_type', 'station', 'aircraft_type', 'carrier', 'source_file'],
                "arr"
            )
                   
        with view_tabs[1]:
            render_flight_table(
                filtered_df[filtered_df['type'] == 'D'],
                "Salidas",
                ['flight_number', 'day_name', 'date', 'departure_time', 'origin', 'destination',
                 'flight_type', 'station', 'aircraft_type', 'carrier', 'source_file'],
                "dep"
            )