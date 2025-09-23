import streamlit as st
import os
import pandas as pd
import numpy as np
import math
import tempfile
from pathlib import Path
from BagToCsv import RosbagParser
from plot_utilities import (
    plot_uwb_error_over_time,
    plot_uwb_error_over_actual_distance,
    plot_uwb_distance_vs_gps_actual_distance_merged,
    plot_uwb_distance_vs_gps_actual_distance
)
from database_utils import save_flight_data

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def calculate_los_vector(aircraft_lat, aircraft_lon, aircraft_alt, beacon_lat, beacon_lon, beacon_alt):
    R = 6371000
    dlat = np.radians(beacon_lat - aircraft_lat) * R
    dlon = np.radians(beacon_lon - aircraft_lon) * R * np.cos(np.radians(aircraft_lat))
    dalt = beacon_alt - aircraft_alt
    los_vector = np.array([dlat, dlon, dalt])
    return los_vector / np.linalg.norm(los_vector)

def calculate_radial_velocity(row, beacon_lat, beacon_lon, beacon_alt):
    los_unit = calculate_los_vector(row['latitude'], row['longitude'], row['altitude'], 
                                   beacon_lat, beacon_lon, beacon_alt)
    velocity = np.array([row['twist.linear.x'], row['twist.linear.y'], row['twist.linear.z']])
    return np.dot(velocity, los_unit)

def process_bag_data(bag_path, csv_output_dir, beacon_lat, beacon_lon, beacon_alt):
    parser = RosbagParser(bag_file_path=bag_path, output_dir=csv_output_dir)
    parser.export_to_csv()
    
    bag_name = Path(bag_path).stem
    
    uwb_file = os.path.join(csv_output_dir, f'{bag_name}_uwb_distance.csv')
    gps_file = os.path.join(csv_output_dir, f'{bag_name}_mavros_global_position_global.csv')
    vel_file = os.path.join(csv_output_dir, f'{bag_name}_mavros_local_position_velocity_local.csv')
    
    if not all(os.path.exists(f) for f in [uwb_file, gps_file, vel_file]):
        st.error("Required CSV files not found.")
        return None, None, None
    
    uwb_df = pd.read_csv(uwb_file)[['timestamp', 'distance']]
    gps_df = pd.read_csv(gps_file)[['timestamp', 'latitude', 'longitude', 'altitude']]
    vel_df = pd.read_csv(vel_file)[['timestamp', 'twist.linear.x', 'twist.linear.y', 'twist.linear.z']]
    
    merged_df = pd.merge_asof(uwb_df.sort_values('timestamp'),
                              gps_df.sort_values('timestamp'),
                              on='timestamp', direction='nearest')
    
    merged_df = pd.merge_asof(merged_df.sort_values('timestamp'),
                              vel_df.sort_values('timestamp'),
                              on='timestamp', direction='nearest')
    
    merged_df['actual_distance'] = merged_df.apply(
        lambda row: haversine(row['latitude'], row['longitude'], beacon_lat, beacon_lon), axis=1
    )
    merged_df['beacon_error'] = merged_df['distance'] - merged_df['actual_distance']
    
    merged_df['radial_velocity'] = merged_df.apply(
        lambda row: calculate_radial_velocity(row, beacon_lat, beacon_lon, beacon_alt), axis=1
    )
    
    gps_df['actual_distance'] = gps_df.apply(
        lambda row: haversine(row['latitude'], row['longitude'], beacon_lat, beacon_lon), axis=1
    )
    
    return merged_df, uwb_df, gps_df

# Page content
st.title("Current Flight Analysis")
st.markdown("Upload a ROS2 bag folder to analyze UWB and GPS data")
st.markdown("Once you begin an upload, do not leave the page until the process has completed, the plots will be shown on the screen.")

st.sidebar.header("Beacon Configuration")
beacon_lat = st.sidebar.number_input("Beacon Latitude", value=40.3791014, format="%.7f")
beacon_lon = st.sidebar.number_input("Beacon Longitude", value=-79.6078958, format="%.7f")
beacon_alt = st.sidebar.number_input("Beacon Altitude (m)", value=325.281693, format="%.6f")

uploaded_files = st.file_uploader(
    "Upload ROS2 bag folder contents (.yaml and .mcap file)",
    accept_multiple_files=True,
    help="Select all files from your ROS2 bag folder"
)

if uploaded_files:
    bag_name = Path(uploaded_files[0].name).stem
    
    csv_dir = os.path.join("csv", bag_name)
    plot_dir = os.path.join("plots", bag_name)
    os.makedirs(csv_dir, exist_ok=True)
    os.makedirs(plot_dir, exist_ok=True)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        bag_dir = os.path.join(temp_dir, "bag")
        os.makedirs(bag_dir)
        
        for uploaded_file in uploaded_files:
            file_path = os.path.join(bag_dir, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
        
        if st.button("Process Bag Data"):
            with st.spinner("Processing ROS2 bag data..."):
                try:
                    merged_df, uwb_df, gps_df = process_bag_data(
                        bag_dir, csv_dir, beacon_lat, beacon_lon, beacon_alt
                    )
                    
                    if merged_df is not None:
                        st.success("Data processed successfully!")
                        
                        # Calculate metrics
                        mean_error = merged_df['beacon_error'].mean()
                        std_error = merged_df['beacon_error'].std()
                        total_points = len(merged_df)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total UWB Readings", total_points)
                        with col2:
                            st.metric("Mean UWB Error (m)", f"{mean_error:.3f}")
                        with col3:
                            st.metric("Std UWB Error (m)", f"{std_error:.3f}")
                        
                        # Generate plots
                        st.subheader("UWB Error Plots")
                        
                        plot_uwb_distance_vs_gps_actual_distance(uwb_df, gps_df, bag_name, plot_dir)
                        plot1_path = os.path.join(plot_dir, 'uwb_distance_vs_gps_actual_distance.png')
                        if os.path.exists(plot1_path):
                            st.image(plot1_path, caption="UWB Distance vs GPS Actual Distance")
                        
                        plot_uwb_error_over_time(merged_df, bag_name, plot_dir)
                        plot2_path = os.path.join(plot_dir, 'uwb_error_vs_time_colored_velocity.png')
                        if os.path.exists(plot2_path):
                            st.image(plot2_path, caption="UWB Error Over Time")
                        
                        plot_uwb_error_over_actual_distance(merged_df, bag_name, plot_dir)
                        plot3_path = os.path.join(plot_dir, 'uwb_error_vs_actual_distance.png')
                        if os.path.exists(plot3_path):
                            st.image(plot3_path, caption="UWB Error vs Actual Distance")
                        
                        plot_uwb_distance_vs_gps_actual_distance_merged(merged_df, bag_name, plot_dir)
                        plot4_path = os.path.join(plot_dir, 'uwb_distance_vs_gps_actual_distance_merged.png')
                        if os.path.exists(plot4_path):
                            st.image(plot4_path, caption="UWB vs GPS Distance Over Time")
                        
                        # Save to database
                        save_flight_data(bag_name, mean_error, std_error, total_points, 
                                       beacon_lat, beacon_lon, beacon_alt, plot_dir, 
                                       bag_dir, csv_dir)
                        
                        st.subheader("Data Preview")
                        st.dataframe(merged_df.head(100))
                        
                        csv_data = merged_df.to_csv(index=False)
                        st.download_button(
                            label="Download UWB Merged Data (CSV)",
                            data=csv_data,
                            file_name="processed_uwb_data.csv",
                            mime="text/csv"
                        )
                        
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")

else:
    st.info("Please upload ROS2 bag files to begin analysis.")