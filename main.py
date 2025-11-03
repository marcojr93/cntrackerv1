import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import pycountry
import calendar

# Função para obter o dataframe da aba SOON
def load_data():
    try:
        df = pd.read_excel('assets/CONTAINER.xlsx', sheet_name='SOON', header=1)
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

def generate_week_options():
    """Gera opções de semanas para os anos 2025, 2026 e 2027"""
    weeks = []
    for year in [2025, 2026, 2027]:
        # Primeira semana do ano
        jan1 = datetime(year, 1, 1)
        # Encontra a primeira segunda-feira do ano
        days_to_monday = (7 - jan1.weekday()) % 7
        if days_to_monday == 0 and jan1.weekday() != 0:
            days_to_monday = 7
        first_monday = jan1 + timedelta(days=days_to_monday)
        
        week_num = 1
        current_monday = first_monday
        
        while current_monday.year == year:
            friday = current_monday + timedelta(days=4)
            if friday.year != year:
                break
            
            week_label = f"{year} - Week {week_num:02d} ({current_monday.strftime('%b %d')}-{friday.strftime('%b %d')})"
            weeks.append((week_label, current_monday, friday))
            
            current_monday += timedelta(days=7)
            week_num += 1
    
    return weeks

def get_week_range():
    today = datetime.today()
    start = today - timedelta(days=today.weekday())
    end = start + timedelta(days=4)
    return start, end

def get_custom_week_range(selected_week_data):
    """Retorna o range da semana selecionada"""
    return selected_week_data[1], selected_week_data[2]  # monday, friday

def filter_by_week(df, date_col):
    start, end = get_week_range()
    mask = (df[date_col] >= start) & (df[date_col] <= end)
    return df[mask]

def filter_by_custom_week(df, date_col, week_start, week_end):
    """Filtra dados pela semana customizada selecionada"""
    mask = (df[date_col] >= week_start) & (df[date_col] <= week_end)
    return df[mask]

def filter_by_month(df, date_col):
    today = datetime.today()
    mask = (df[date_col].dt.month == today.month) & (df[date_col].dt.year == today.year)
    return df[mask]

def filter_by_custom_month(df, date_col, selected_date):
    """Filtra dados pelo mês da semana selecionada"""
    mask = (df[date_col].dt.month == selected_date.month) & (df[date_col].dt.year == selected_date.year)
    return df[mask]

import re

# Função para parsear datas no formato 'Week July 28th, 2025'
def parse_week_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
    # Remove 'Week' e espaços extras
    date_str = str(date_str).strip()
    match = re.search(r"Week ([A-Za-z]+) (\d{1,2})(?:st|nd|rd|th)?, (\d{4})", date_str)
    if match:
        month = match.group(1)
        day = match.group(2)
        year = match.group(3)
        try:
            return pd.to_datetime(f"{day} {month} {year}", format="%d %B %Y")
        except Exception:
            return pd.NaT
    # fallback para outros formatos
    try:
        return pd.to_datetime(date_str, errors='coerce')
    except Exception:
        return pd.NaT

def main():
    st.set_page_config(page_title='Ships Dashboard', layout='wide')
    
    # Logo centralizada no topo
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.image('assets/logo.png', width=80)
    
    st.title('Ships Monitoring Dashboard')

    # Botão para carregar dados
    if st.button("Load data", type="primary"):
        df = load_data()
        if df is None:
            return
        st.session_state.df = df
        
        # Encontrar a semana atual ao carregar dados
        week_options = generate_week_options()
        current_week_index = 0
        today = datetime.today()
        for i, (label, start, end) in enumerate(week_options):
            if start <= today <= end:
                current_week_index = i
                break
        st.session_state.week_index = current_week_index
        
        st.success("Data loaded successfully!")
    
    if 'df' not in st.session_state:
        st.info("Click 'Load data' to start the analysis.")
        return
    
    df = st.session_state.df

    tab1, tab2 = st.tabs(["Dashboard", "Map"])

    with tab1:
        # Sidebar para seleção de semana
        st.sidebar.title("Week Selection")
        week_options = generate_week_options()
        
        # Encontrar a semana atual como padrão
        current_week_index = 0
        today = datetime.today()
        for i, (label, start, end) in enumerate(week_options):
            if start <= today <= end:
                current_week_index = i
                break
        
        # Initialize session state for week index
        if 'week_index' not in st.session_state:
            st.session_state.week_index = current_week_index
        
        # Previous and Next week buttons
        col_prev, col_next = st.sidebar.columns(2)
        
        with col_prev:
            if st.button("Previous Week", use_container_width=True):
                if st.session_state.week_index > 0:
                    st.session_state.week_index -= 1
        
        with col_next:
            if st.button("Next Week", use_container_width=True):
                if st.session_state.week_index < len(week_options) - 1:
                    st.session_state.week_index += 1
        
        # Week dropdown selection
        selected_week_label = st.sidebar.selectbox(
            "Choose analysis week:",
            options=[label for label, _, _ in week_options],
            index=st.session_state.week_index,
            key="week_selector"
        )
        
        # Update session state if dropdown changes
        for i, (label, _, _) in enumerate(week_options):
            if label == selected_week_label:
                st.session_state.week_index = i
                break
        
        # Analysis interval option
        st.sidebar.markdown("---")
        analysis_interval = st.sidebar.selectbox(
            "Analysis Interval:",
            options=["Selected Week Only", "Monthly View", "Quarterly View"],
            index=0
        )
        
        # Se Monthly View for selecionado, mostrar dropdown de meses
        selected_month_date = None
        if analysis_interval == "Monthly View":
            # Gerar opções de mês/ano para os próximos 24 meses
            month_options = []
            current_date = datetime(2025, 1, 1)
            for i in range(36):  # 3 anos de opções
                month_label = current_date.strftime("%B %Y")
                month_options.append((month_label, current_date))
                # Próximo mês
                if current_date.month == 12:
                    current_date = current_date.replace(year=current_date.year + 1, month=1)
                else:
                    current_date = current_date.replace(month=current_date.month + 1)
            
            # Encontrar o mês atual como padrão
            today = datetime.today()
            default_month_index = 0
            for i, (label, date) in enumerate(month_options):
                if date.year == today.year and date.month == today.month:
                    default_month_index = i
                    break
            
            selected_month_label = st.sidebar.selectbox(
                "Choose month:",
                options=[label for label, _ in month_options],
                index=default_month_index
            )
            
            # Encontrar a data do mês selecionado
            for label, date in month_options:
                if label == selected_month_label:
                    selected_month_date = date
                    break
        
        # Encontrar dados da semana selecionada
        selected_week_data = None
        for label, start, end in week_options:
            if label == selected_week_label:
                selected_week_data = (label, start, end)
                break
        
        # Aplica o parser inteligente para a coluna de datas (coluna T)
        df['DELIVERY_DATE'] = df.iloc[:, 19].apply(parse_week_date)  # ETA FINAL PORT (coluna T)
        df['AMOUNT'] = pd.to_numeric(df.iloc[:, 23], errors='coerce')  # Coluna X

        week_start, week_end = get_custom_week_range(selected_week_data)
        
        # Adjust date range based on analysis interval
        if analysis_interval == "Monthly View":
            if selected_month_date:
                month_start = selected_month_date.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                analysis_start, analysis_end = month_start, month_end
                interval_label = f"Month of {selected_month_date.strftime('%B %Y')}"
            else:
                month_start = week_start.replace(day=1)
                month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                analysis_start, analysis_end = month_start, month_end
                interval_label = f"Month of {week_start.strftime('%B %Y')}"
        elif analysis_interval == "Quarterly View":
            quarter = (week_start.month - 1) // 3 + 1
            quarter_start = datetime(week_start.year, (quarter - 1) * 3 + 1, 1)
            quarter_end = datetime(week_start.year, quarter * 3 + 1, 1) - timedelta(days=1) if quarter < 4 else datetime(week_start.year, 12, 31)
            analysis_start, analysis_end = quarter_start, quarter_end
            interval_label = f"Q{quarter} {week_start.year}"
        else:  # Selected Week Only
            analysis_start, analysis_end = week_start, week_end
            interval_label = f"Week {week_start.strftime('%d-%b')} to {week_end.strftime('%d-%b')}"

        st.subheader(f'Analysis Period: {interval_label}')

        # Filters usando o intervalo selecionado
        df_period = filter_by_custom_week(df, 'DELIVERY_DATE', analysis_start, analysis_end)
        
        # Para df_month, usar o mês selecionado se estiver em Monthly View
        if analysis_interval == "Monthly View" and selected_month_date:
            df_month = filter_by_custom_month(df, 'DELIVERY_DATE', selected_month_date)
        else:
            df_month = filter_by_custom_month(df, 'DELIVERY_DATE', week_start)

        # Função para determinar se é navio ou caminhão
        def is_truck(destination_value):
            if pd.isna(destination_value):
                return False
            destination_str = str(destination_value).strip().upper()
            return destination_str == 'TO DOOR'
        
        # Calcular estatísticas por tipo de transporte
        df_period['IS_TRUCK'] = df_period.iloc[:, 20].apply(is_truck)  # Coluna U
        df_month['IS_TRUCK'] = df_month.iloc[:, 20].apply(is_truck)    # Coluna U
        
        # Contadores por período
        ships_period = len(df_period[~df_period['IS_TRUCK']])
        trucks_period = len(df_period[df_period['IS_TRUCK']])
        
        # Contadores por mês
        ships_month = len(df_month[~df_month['IS_TRUCK']])
        trucks_month = len(df_month[df_month['IS_TRUCK']])
        
        # KPIs
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        col1.metric('🚢 Ships (Period)', ships_period)
        col2.metric('🚛 Trucks (Period)', trucks_period)
        col3.metric('🚢 Ships (Month)', ships_month)
        col4.metric('🚛 Trucks (Month)', trucks_month)
        
        # Métricas de valor com fonte menor
        with col5:
            st.markdown("**💰 Value (Period)**")
            st.markdown(f"<div style='font-size: 18px; font-weight: bold;'>$ {df_period['AMOUNT'].sum():,.0f}</div>", unsafe_allow_html=True)
        
        with col6:
            st.markdown("**💰 Value (Month)**") 
            st.markdown(f"<div style='font-size: 18px; font-weight: bold;'>$ {df_month['AMOUNT'].sum():,.0f}</div>", unsafe_allow_html=True)

        # Gráfico de barras horizontal
        st.markdown('---')
        st.subheader(f'Delivery Forecast - {interval_label}')

        # Filter deliveries for selected period and remove invalid dates
        df_graf = df_period.dropna(subset=['DELIVERY_DATE'])
        if not df_graf.empty:
            # Calculate days until arrival from today
            today = datetime.now()
            df_graf['DAYS_UNTIL_ARRIVAL'] = (df_graf['DELIVERY_DATE'] - today).dt.days
            
            # Debug: Check for zero or NaN values
            df_graf = df_graf.dropna(subset=['DAYS_UNTIL_ARRIVAL'])
            
            # Function to get transport emoji based on DESTINATION column
            def get_transport_emoji(destination_value):
                if pd.isna(destination_value):
                    return '🚢'
                destination_str = str(destination_value).strip().upper()
                if destination_str == 'TO DOOR':
                    return '🚛'
                return '🚢'
            
            # Create new label with appropriate transport emoji: PO - Product - Supplier
            df_graf['TRANSPORT_EMOJI'] = df_graf.iloc[:, 20].apply(get_transport_emoji)  # Coluna U (índice 20)
            df_graf['LABEL'] = (
                df_graf['TRANSPORT_EMOJI'] + ' ' +
                df_graf.iloc[:, 1].astype(str) + ' - ' +  # PO number (column B)
                df_graf.iloc[:, 4].astype(str) + ' - ' +  # Product (column E)
                df_graf.iloc[:, 0].astype(str)            # Supplier (column A)
            )
            
            # Sort by delivery date (closest first) - REVERSED for proper display
            df_graf = df_graf.sort_values('DELIVERY_DATE', ascending=False)
            
            # Plotly for horizontal bars
            import plotly.graph_objects as go
            fig = go.Figure()
            for idx, row in df_graf.iterrows():
                # Define color based on days until arrival (red for delayed ships)
                bar_color = '#8B0000' if row['DAYS_UNTIL_ARRIVAL'] < 0 else 'steelblue'
                
                # Ensure minimum bar width for visibility
                bar_value = row['DAYS_UNTIL_ARRIVAL'] if abs(row['DAYS_UNTIL_ARRIVAL']) >= 0.1 else (0.1 if row['DAYS_UNTIL_ARRIVAL'] >= 0 else -0.1)
                
                fig.add_trace(go.Bar(
                    y=[row['LABEL']],
                    x=[bar_value],
                    orientation='h',
                    text=[row['LABEL']],
                    textposition='inside',
                    marker_color=bar_color,
                    hovertemplate=f"Delivery date: {row['DELIVERY_DATE'].strftime('%d/%m/%Y')}<br>Value: $ {row['AMOUNT']:,.2f}<br>Days until arrival: {row['DAYS_UNTIL_ARRIVAL']}<extra></extra>"
                ))
            fig.update_layout(
                xaxis=dict(
                    title='Days until arrival',
                    tickmode='linear',
                    dtick=1
                ),
                yaxis=dict(title='Transport (PO - Product - Supplier)'),
                height=40*len(df_graf)+200,
                showlegend=False,
                margin=dict(l=0, r=0, t=30, b=0)
            )
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.info(f'No deliveries scheduled for the selected period ({interval_label}).')

        # Optional DataFrame display (movido para depois do gráfico)
        with st.expander('Show DataFrame'):
            st.dataframe(df)

    with tab2:
        from maps import render_map_tab
        # Passar dados da semana selecionada para a aba de mapas
        week_start, week_end = get_custom_week_range(selected_week_data)
        week_label = f"Week {week_start.strftime('%d-%b')} to {week_end.strftime('%d-%b')}"
        render_map_tab(None, week_start, week_end, week_label)


# Garante execução do app Streamlit
if __name__ == "__main__":
    main()
