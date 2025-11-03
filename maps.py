import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import pycountry
import re

def parse_week_date(date_str):
    if pd.isna(date_str):
        return pd.NaT
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
    try:
        return pd.to_datetime(date_str, errors='coerce')
    except Exception:
        return pd.NaT

def get_country_coordinates(country_name):
    country_coords = {
        'USA': (39.8283, -98.5795),
        'UNITED STATES': (39.8283, -98.5795),
        'Canada': (56.1304, -106.3468),
        'Brazil': (-14.2350, -51.9253),
        'Germany': (51.1657, 10.4515),
        'France': (46.6034, 1.8883),
        'Italy': (41.8719, 12.5674),
        'Spain': (40.4637, -3.7492),
        'UK': (55.3781, -3.4360),
        'United Kingdom': (55.3781, -3.4360),
        'Japan': (36.2048, 138.2529),
        'China': (35.8617, 104.1954),
        'India': (20.5937, 78.9629),
        'Australia': (-25.2744, 133.7751),
        'Mexico': (23.6345, -102.5528),
        'Argentina': (-38.4161, -63.6167),
        'Russia': (61.5240, 105.3188),
        'South Korea': (35.9078, 127.7669),
        'Netherlands': (52.1326, 5.2913),
        'Belgium': (50.5039, 4.4699),
        'Sweden': (60.1282, 18.6435),
        'Norway': (60.4720, 8.4689),
        'Denmark': (56.2639, 9.5018),
        'Finland': (61.9241, 25.7482),
        'Poland': (51.9194, 19.1451),
        'Turkey': (38.9637, 35.2433),
        'South Africa': (-30.5595, 22.9375),
        'Egypt': (26.0975, 30.0444),
        'Thailand': (15.8700, 100.9925),
        'Vietnam': (14.0583, 108.2772),
        'Singapore': (1.3521, 103.8198),
        'Malaysia': (4.2105, 101.9758),
        'Indonesia': (-0.7893, 113.9213),
        'Philippines': (12.8797, 121.7740),
        'Chile': (-35.6751, -71.5430),
        'Peru': (-9.1900, -75.0152),
        'Colombia': (4.5709, -74.2973),
        'Venezuela': (6.4238, -66.5897)
    }
    
    return country_coords.get(country_name.upper(), None)

def render_map_tab(uploaded_file, week_start, week_end, week_label):
    st.subheader(f'Ships Map View - {week_label}')
    
    # Carregar dados do arquivo fixo
    try:
        df = pd.read_excel('assets/CONTAINER.xlsx', sheet_name='SOON', header=1)
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return
    
    # Parse das datas
    df['DELIVERY_DATE'] = df.iloc[:, 19].apply(parse_week_date)
    
    # Filtrar pelos dados da semana selecionada
    mask = (df['DELIVERY_DATE'] >= week_start) & (df['DELIVERY_DATE'] <= week_end)
    df_filtered = df[mask]
    
    if df_filtered.empty:
        st.warning(f"No ships scheduled for the selected week ({week_label})")
        return
    
    # Contar containers por país (coluna J)
    country_counts = df_filtered.iloc[:, 9].value_counts()
    
    if country_counts.empty:
        st.warning("No countries found with scheduled deliveries")
        return
    
    # Filtro por país
    selected_country = st.selectbox(
        "Select a country to view details:",
        options=['All Countries'] + list(country_counts.index)
    )
    
    # Criar mapa
    m = folium.Map(location=[20, 0], zoom_start=2)
    
    # Adicionar marcadores para cada país
    for country, count in country_counts.items():
        coords = get_country_coordinates(str(country))
        if coords:
            # Destacar país selecionado
            color = 'red' if selected_country == country else 'blue'
            size = 15 if selected_country == country else 10
            
            folium.CircleMarker(
                location=coords,
                radius=size,
                popup=f"{country}: {count} containers",
                color=color,
                fill=True,
                fillColor=color,
                fillOpacity=0.7
            ).add_to(m)
    
    # Focar no país selecionado
    if selected_country != 'All Countries':
        coords = get_country_coordinates(selected_country)
        if coords:
            m = folium.Map(location=coords, zoom_start=6)
            folium.CircleMarker(
                location=coords,
                radius=15,
                popup=f"{selected_country}: {country_counts[selected_country]} containers",
                color='red',
                fill=True,
                fillColor='red',
                fillOpacity=0.7
            ).add_to(m)
    
    # Exibir mapa
    folium_static(m)
    
    # Mostrar detalhes do país selecionado
    if selected_country != 'All Countries':
        st.subheader(f'Ships scheduled for {selected_country} in selected week')
        
        # Filtrar dados do país selecionado
        country_data = df_filtered[df_filtered.iloc[:, 9] == selected_country]
        
        # Preparar dados para exibição
        details_df = pd.DataFrame({
            'Container ID': country_data.iloc[:, 5],      # Coluna F
            'Destination': country_data.iloc[:, 19],      # Coluna T
            'Amount ($)': ['${:,.2f}'.format(x) if pd.notna(x) else 'N/A' 
                          for x in pd.to_numeric(country_data.iloc[:, 22], errors='coerce')],  # Coluna W
            'Delivery Date': country_data['DELIVERY_DATE'].dt.strftime('%d/%m/%Y'),  # Coluna U
            'Supplier': country_data.iloc[:, 0],          # Coluna A
            'Product': country_data.iloc[:, 4]            # Coluna E
        })
        
        st.dataframe(details_df, use_container_width=True)
        st.info(f"Total containers for {selected_country}: {len(country_data)}")
    else:
        st.subheader('Summary by Country')
        summary_df = pd.DataFrame({
            'Country': country_counts.index,
            'Container Count': country_counts.values
        })
        st.dataframe(summary_df, use_container_width=True)
