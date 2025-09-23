import streamlit as st
import pandas as pd
import os
from database_utils import get_all_flights, get_flight_data

st.title("Historical Flight Data")
st.markdown("View and analyze previous flight results")

# Get all flights from database
flights = get_all_flights()

if flights:
    # Flight selection
    flight_names = [f[1] for f in flights]  # flight_name column
    selected_flight = st.selectbox("Select Flight", flight_names)
    
    if selected_flight:
        # Get flight data
        flight_data = get_flight_data(selected_flight)
        
        if flight_data:
            st.subheader(f"Flight: {selected_flight}")
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean UWB Error (m)", f"{flight_data['mean_error']:.3f}")
            with col2:
                st.metric("Std UWB Error (m)", f"{flight_data['std_error']:.3f}")
            with col3:
                st.metric("Total Points", flight_data['total_points'])
            with col4:
                st.metric("Date", flight_data['date'])
            
            # Display beacon configuration
            st.subheader("Beacon Configuration")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"Latitude: {flight_data['beacon_lat']:.7f}")
            with col2:
                st.write(f"Longitude: {flight_data['beacon_lon']:.7f}")
            with col3:
                st.write(f"Altitude: {flight_data['beacon_alt']:.3f} m")
            
            # Display plots
            st.subheader("Flight Analysis Plots")
            plot_dir = flight_data['plot_path']
            
            plot_files = [
                ('uwb_distance_vs_gps_actual_distance.png', 'UWB Distance vs GPS Actual Distance'),
                ('uwb_error_vs_time_colored_velocity.png', 'UWB Error Over Time'),
                ('uwb_error_vs_actual_distance.png', 'UWB Error vs Actual Distance'),
                ('uwb_distance_vs_gps_actual_distance_merged.png', 'UWB vs GPS Distance Over Time')
            ]
            
            for plot_file, caption in plot_files:
                plot_path = os.path.join(plot_dir, plot_file)
                if os.path.exists(plot_path):
                    st.image(plot_path, caption=caption)
                else:
                    st.warning(f"Plot not found: {plot_file}")
    
    # Summary statistics
    st.subheader("Flight Summary Statistics")
    df = pd.DataFrame(flights, columns=['ID', 'Flight Name', 'Mean Error', 'Std Error', 'Total Points', 'Date', 'Beacon Lat', 'Beacon Lon', 'Beacon Alt', 'Plot Path'])
    st.dataframe(df[['Flight Name', 'Mean Error', 'Std Error', 'Total Points', 'Date']])
    
else:
    st.info("No historical flight data found. Process some flights first!")