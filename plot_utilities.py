# This is a library to create plots for ultrawideband data from csv files
# The inputs to the function are the data frame and the ros bag file name, for labeling.
# Some functions require a merged data frame and some require the individual data frames.

import os
import matplotlib.pyplot as plt


## DESCRIBE THE UWB ERROR in Scatter Plots##

# Show the UWB error over time, coloring with radial velocitty
def plot_uwb_error_over_time(merged_df, ros_bag_file, plot_output_dir):
    plt.figure(figsize=(12, 8))
    plt.scatter(merged_df['timestamp'], merged_df['beacon_error'], c=merged_df['radial_velocity'], cmap='viridis', s=8, alpha=0.8)
    plt.xlabel('Timestamp')
    plt.ylabel('UWB Error (meters)')
    plt.colorbar(label='Radial Velocity (m/s)')
    plt.suptitle('UWB Error Over Time Colored by Radial Velocity', fontsize=14, fontweight='bold')
    plt.title(f'Run: {ros_bag_file}', fontsize=10)
    plt.grid(True)
    plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_time_colored_velocity.png'), dpi=300)
    plt.clf()
    plt.close()

# Create a scatter plot of the error by actual distance, coloring the scatter by radial velocity
def plot_uwb_error_over_actual_distance(merged_df, ros_bag_file, plot_output_dir):
    plt.figure(figsize=(12, 8))
    plt.scatter(merged_df['actual_distance'], merged_df['beacon_error'], c=merged_df['radial_velocity'], cmap='viridis', s=10)
    plt.colorbar(label='Radial Velocity (m/s)')
    plt.xlabel('Actual Distance (meters) - GPS measured to Beacon')
    plt.ylabel('UWB Error (meters)')
    
    #save the plot to the plot output dir
    plt.suptitle('UWB Error vs Actual Distance to Beacon', fontsize=14, fontweight='bold')
    plt.title(f'Run: {ros_bag_file}', fontsize = 10)
    plt.grid(True)
    plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_actual_distance.png'), dpi=300)
    plt.clf()
    plt.close()

# Create a combined scatter plot of uwb measured distance to gps measured actual distance
def plot_uwb_distance_vs_gps_actual_distance(uwb_distance_df, aircraft_gps_df, ros_bag_file, plot_output_dir):
    plt.figure(figsize=(12, 8))
    plt.scatter(uwb_distance_df['timestamp'], uwb_distance_df['distance'], c='blue', s=8, alpha=0.6, label='UWB Distance')
    plt.scatter(aircraft_gps_df['timestamp'], aircraft_gps_df['actual_distance'], c='red', s=8, alpha=0.6, label='GPS Actual Distance')
    plt.xlabel('UWB Distance (meters)')
    plt.ylabel('GPS Measured Actual Distance (meters)')
    plt.suptitle('UWB Distance vs GPS Measured Actual Distance', fontsize=14, fontweight='bold')
    plt.title(f'Run: {ros_bag_file}', fontsize = 10)
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(plot_output_dir, 'uwb_distance_vs_gps_actual_distance.png'), dpi=300)
    plt.clf()
    plt.close()

# Create the same UWB and GPS distance plot but from the merged data frame
def plot_uwb_distance_vs_gps_actual_distance_merged(merged_df, ros_bag_file, plot_output_dir):
    plt.figure(figsize=(12, 8))
    plt.scatter(merged_df['timestamp'], merged_df['distance'], c='blue', s=8, alpha=0.6, label='UWB Distance')
    plt.scatter(merged_df['timestamp'], merged_df['actual_distance'], c='red', s=8, alpha=0.6, label='GPS Actual Distance')
    plt.xlabel('Timestamp')
    plt.ylabel('Distance (m)')
    plt.suptitle('UWB vs GPS Distance Over Time (Merged Data)', fontsize=14, fontweight='bold')
    plt.title(f'Run: {ros_bag_file}', fontsize = 10)
    plt.grid(True)
    plt.legend()
    plt.savefig(os.path.join(plot_output_dir, 'uwb_distance_vs_gps_actual_distance_merged.png'), dpi=300)
    plt.clf()
    plt.close()

# Plot aircraft GPS path
def plot_aircraft_path(gps_df, beacon_lat, beacon_lon, commanded_landing, ros_bag_file, plot_output_dir):
    plt.figure(figsize=(12, 8))
    plt.plot(gps_df['longitude'], gps_df['latitude'], 'b-', linewidth=1, label='Aircraft Path')
    plt.scatter(gps_df['longitude'].iloc[0], gps_df['latitude'].iloc[0], c='green', s=100, marker='^', label='Start')
    plt.scatter(gps_df['longitude'].iloc[-1], gps_df['latitude'].iloc[-1], c='red', s=100, marker='v', label='End')
    plt.scatter(beacon_lon, beacon_lat, c='orange', s=150, marker='*', label='Beacon')
    
    if commanded_landing:
        plt.scatter(commanded_landing['lon'], commanded_landing['lat'], c='purple', s=100, marker='x', label='UWB Landing Est.')
    
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.suptitle('Aircraft Flight Path', fontsize=14, fontweight='bold')
    plt.title(f'Run: {ros_bag_file}', fontsize=10)
    plt.grid(True)
    plt.legend()
    plt.axis('equal')
    plt.savefig(os.path.join(plot_output_dir, 'aircraft_flight_path.png'), dpi=300)
    plt.clf()
    plt.close()

def plot_sigma_time (sigma_df, sigma_threshold, ros_bag_file, plot_output_dir):
    plt.figure(figsize=(12, 8))
    plt.scatter(sigma_df['timestamp'], sigma_df['sigma'], c='blue', s=10)
    plt.axhline(y=sigma_threshold, color='red', linestyle='--', label=f'Sigma Threshold: {sigma_threshold}')
    plt.xlabel('Timestamp')
    plt.ylabel('Sigma')
    plt.suptitle('Sigma Over Time', fontsize=14, fontweight='bold')
    plt.title(f'Run: {ros_bag_file}', fontsize=10)
    plt.grid(True)
    plt.savefig(os.path.join(plot_output_dir, 'sigma_over_time.png'), dpi=300)
    plt.clf()
    plt.close()


# # Compare the radial velocity to the UWB error
# plt.scatter(merged_df['radial_velocity'], merged_df['beacon_error'], s=8, alpha=0.8)
# plt.xlabel('Radial Velocity (m/s)')
# plt.ylabel('UWB Error (meters)')
# plt.title(f'Run: {ros_bag_file}')
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_velocity.png'), dpi=300)
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
# plt.scatter(merged_df['timestamp'], merged_df['beacon_error'], c=merged_df['radial_velocity'], cmap='viridis', s=8, alpha=0.8)
# plt.xlabel('Timestamp')
# plt.ylabel('UWB Error (meters)')
# plt.colorbar(label='Radial Velocity (m/s)')
# plt.title('UWB Error Over Time Colored by Radial Velocity')
# plt.suptitle(f'Run: {ros_bag_file}')
# plt.grid(True)
# plt.savefig(os.path.join(plot_output_dir, 'uwb_error_vs_time_colored_velocity.png'), dpi=300)
# plt.clf()
# plt.close()