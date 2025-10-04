# This is a python file to start regression analysis for the Guidon beacon based landing.

import matplotlib.pyplot as plt
from math import sqrt
import pandas as pd
import numpy as np
from BagToCsv import RosbagParser
import os
import math

## Input the ROS Bag Folder Here ##
# ros_bag_file = 'run_2025_09_18_13-21-17'
# ros_bag_file = 'run_2025_09_18_12-53-02' # Some database files are missing.
# ros_bag_file = 'run_2025_09_18_12-43-47'
# ros_bag_file = 'run_2025_09_18_13-10-27'
ros_bag_file = 'run_2025_09_18_16-20-20'


## Input the actual locaiton of the beacon here ##
beacon_lon = -79.6078958
beacon_lat = 40.3791014
beacon_alt = 325.281693

### Parse the Ros Bag to CSV ###
ros_bag_file_path = os.path.join('bags', ros_bag_file) # Use only the folder name, not the mcap file.
csv_output_dir = os.path.join('csv', ros_bag_file)
if not os.path.exists(csv_output_dir):
    os.makedirs(csv_output_dir)

### YOU ONLY NEED TO RUN THIS ONCE TO PARSE THE ROS BAG TO CSV ###
# parser = RosbagParser(bag_file_path=ros_bag_file_path, output_dir=csv_output_dir)
# parser.export_to_csv()

## End of Ros Bag Parsing ##

## Create a data frame of the aircraft GPS, velocity, and UWB predicted range distance ##
uwb_distance_file = os.path.join(csv_output_dir, 'bag_uwb_distance.csv')
uwb_distance_df = pd.read_csv(uwb_distance_file)
columns_to_keep = ['timestamp', 'distance']
uwb_distance_df = uwb_distance_df[columns_to_keep] # Keep only the timestamp and distance columns

aircraft_gps_file = os.path.join(csv_output_dir, 'bag_mavros_global_position_global.csv')
aircraft_gps_file_df = pd.read_csv(aircraft_gps_file)
columns_to_keep = ['timestamp', 'latitude', 'longitude', 'altitude']
aircraft_gps_file_df = aircraft_gps_file_df[columns_to_keep]

aircraft_velocity_file = os.path.join(csv_output_dir, 'bag_mavros_local_position_velocity_local.csv')
aircraft_velocity_df = pd.read_csv(aircraft_velocity_file)
columns_to_keep = ['timestamp', 'twist.linear.x', 'twist.linear.y', 'twist.linear.z']
aircraft_velocity_df = aircraft_velocity_df[columns_to_keep]

# Merge the data frames based on the timestamp, using linear interpolation to fill in missing values
merged_df = pd.merge_asof(uwb_distance_df.sort_values('timestamp'),
                          aircraft_gps_file_df.sort_values('timestamp'),
                            on='timestamp', direction='nearest')

merged_df = pd.merge_asof(merged_df.sort_values('timestamp'),
                          aircraft_velocity_df.sort_values('timestamp'),
                            on='timestamp', direction='nearest')

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Calculate actual distance from aircraft to beacon
merged_df['actual_distance'] = merged_df.apply(
    lambda row: haversine(row['latitude'], row['longitude'], beacon_lat, beacon_lon), axis=1
)

merged_df['beacon_error'] = merged_df['distance'] - merged_df['actual_distance']

# Function to calculate LOS unit vector from aircraft to beacon
def calculate_los_vector(aircraft_lat, aircraft_lon, aircraft_alt, beacon_lat, beacon_lon, beacon_alt):
    # Convert to local ENU coordinates (simplified)
    # For small distances, approximate with linear conversion
    R = 6371000  # Earth radius
    
    # Convert lat/lon differences to meters
    dlat = np.radians(beacon_lat - aircraft_lat) * R
    dlon = np.radians(beacon_lon - aircraft_lon) * R * np.cos(np.radians(aircraft_lat))
    dalt = beacon_alt - aircraft_alt
    
    # Create vector from aircraft to beacon
    los_vector = np.array([dlat, dlon, dalt])
    
    # Return unit vector
    return los_vector / np.linalg.norm(los_vector)

# Calculate LOS unit vector for each data point and radial velocity
def calculate_radial_velocity(row):
    los_unit = calculate_los_vector(row['latitude'], row['longitude'], row['altitude'], 
                                   beacon_lat, beacon_lon, beacon_alt)
    velocity = np.array([row['twist.linear.x'], row['twist.linear.y'], row['twist.linear.z']])
    return np.dot(velocity, los_unit)

merged_df['radial_velocity'] = merged_df.apply(calculate_radial_velocity, axis=1)

aircraft_gps_file_df['actual_distance'] = aircraft_gps_file_df.apply(
    lambda row: haversine(row['latitude'], row['longitude'], beacon_lat, beacon_lon), axis=1
)

# Create a folder to save plots by the ros bag file name
plot_output_dir = os.path.join('plots', ros_bag_file)
if not os.path.exists(plot_output_dir):
    os.makedirs(plot_output_dir)

state_file = os.path.join('/home/kris/src/ros-analytics/csv/run_2025_09_18_16-20-20/bag_uwb_state.csv')
uwb_state_df = pd.read_csv(state_file)
uwb_state_df = uwb_state_df[['timestamp','sigma', 'x', 'y']]
# filter all sigma values below 100
uwb_state_df = uwb_state_df[uwb_state_df['sigma'] < 100]
print(uwb_state_df.tail(10))

# # Create a scatter plot of the error by distance, coloring the scatter by radial velocity
# plt.scatter(merged_df['actual_distance'], merged_df['beacon_error'], c=merged_df['radial_velocity'], cmap='viridis', s=10)
# plt.colorbar(label='Radial Velocity (m/s)')
# plt.xlabel('Actual Distance (meters) - GPS measured to Beacon')
# plt.ylabel('UWB Error (meters)')
# #save the plot to the plot output dir
# plt.title('UWB Error vs Actual Distance to Beacon')
# plt.suptitle(f'Run: {ros_bag_file}')
# plt.grid(True)
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_actual_distance.png'), dpi=300)
# plt.clf()
# plt.close()


# # Compare the radial velocity to the UWB error
# plt.scatter(merged_df['radial_velocity'], merged_df['beacon_error'], s=8, alpha=0.8)
# plt.xlabel('Radial Velocity (m/s)')
# plt.ylabel('UWB Error (meters)')
# plt.title(f'Run: {ros_bag_file}')
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_velocity.png'), dpi=300)
# plt.clf()
# plt.close()

# # Create combined scatter plot
# plt.figure(figsize=(12, 8))
# plt.scatter(uwb_distance_df['timestamp'], uwb_distance_df['distance'], c='blue', s=10, alpha=0.6, label='UWB Distance')
# plt.scatter(aircraft_gps_file_df['timestamp'], aircraft_gps_file_df['actual_distance'], c='red', s=10, alpha=0.6, label='GPS Actual Distance')
# # plt.scatter(uwb_distance_df['timestamp'], uwb_distance_df['distance']-.5, c='green', s=10, alpha=0.6, label='UWB Offset' )
# plt.xlabel('Timestamp')
# plt.ylabel('Distance (m)')
# plt.title('UWB vs GPS Distance Over Time')
# plt.suptitle(f'Run: {ros_bag_file}')
# plt.grid(True)
# plt.legend()
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_GPS.png'), dpi=300)
# plt.clf()
# plt.close()

# # Create the same UWB and GPS distance plot but from the merged data frame
# plt.figure(figsize=(12, 8))
# plt.scatter(merged_df['timestamp'], merged_df['distance'], c='blue', s=10, alpha=0.6, label='UWB Distance')
# # Make the color of the GPS actual distance points a gradient based on the radial velocity
# plt.scatter(merged_df['timestamp'], merged_df['actual_distance'], c=merged_df['radial_velocity'], cmap='viridis', s=10, alpha=0.6, label='GPS Actual Distance')
# plt.colorbar(label='Radial Velocity (m/s)')
# # plt.scatter(merged_df['timestamp'], merged_df['actual_distance'], c='red', s=10, alpha=0.6, label='GPS Actual Distance')
# plt.xlabel('Timestamp')
# plt.ylabel('Distance (m)')
# plt.title('UWB vs GPS Distance Over Time (Merged Data)')
# plt.suptitle(f'Run: {ros_bag_file}')
# plt.grid(True)
# plt.legend()
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_GPS_merged.png'), dpi=300)
# plt.clf()
# plt.close()

# # Plot the UWB error over time
# plt.scatter(merged_df['timestamp'], merged_df['beacon_error'], s=8, alpha=0.8)
# plt.xlabel('Timestamp')
# plt.ylabel('UWB Error (meters)')
# plt.title('UWB Error Over Time')
# plt.suptitle(f'Run: {ros_bag_file}')
# plt.grid(True)
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_time.png'), dpi=300)
# plt.clf()
# plt.close()

# # Compare UWB error to aircraft speed
# plt.scatter(merged_df['radial_velocity'], merged_df['beacon_error'], s=8, alpha=0.8)
# plt.xlabel('Radial Velocity (m/s)')
# plt.ylabel('UWB Error (meters)')
# plt.title('UWB Error vs Radial Velocity')
# plt.suptitle(f'Run: {ros_bag_file}')
# plt.grid(True)
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_radial_speed_merged.png'), dpi=300)
# plt.clf()
# plt.close()

# Compare UWB error over time, coloring with radial velocitty
plt.scatter(merged_df['timestamp'], merged_df['beacon_error'], c=merged_df['radial_velocity'], cmap='viridis', s=8, alpha=0.8)
plt.xlabel('Timestamp')
plt.ylabel('UWB Error (meters)')
plt.colorbar(label='Radial Velocity (m/s)')
plt.title('UWB Error Over Time Colored by Radial Velocity')
plt.suptitle(f'Run: {ros_bag_file}')
plt.grid(True)
plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_time_colored_velocity.png'), dpi=300)
plt.clf()
plt.close()

# Sort the merged data frame by the uwb_error
merged_df = merged_df.sort_values(by='beacon_error', ascending=False)
# Import and use the KMZ creation function

from create_kmz import create_kmz_from_dataframe

# Create KMZ file with GPS points colored by beacon error
# change the output filename to include the ros bag file name
output_filename = os.path.join('kmz', f'{ros_bag_file}_aircraft_track.kmz')
if not os.path.exists('kmz'):
    os.makedirs('kmz')
create_kmz_from_dataframe(merged_df, output_filename, beacon_lat, beacon_lon)