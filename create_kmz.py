import pandas as pd
import numpy as np
import zipfile
import os
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def create_kmz_from_dataframe(df, output_filename, beacon_lat, beacon_lon):
    """Create KMZ file with GPS points colored by beacon error"""
    
    # Create KML root
    kml = Element('kml', xmlns="http://www.opengis.net/kml/2.2")
    document = SubElement(kml, 'Document')
    SubElement(document, 'name').text = 'Aircraft GPS Track with Beacon Error'
    
    # Create color styles for different error ranges
    error_ranges = [
        (-float('inf'), -10.0, 'ff0000ff', 'Large Negative Error'),  # Red
        (-10.0, -3.0, 'ff0080ff', 'Medium Negative Error'),          # Orange
        (-3.0, -0.5, 'ff00ffff', 'Small Negative Error'),           # Yellow
        (-0.5, 0.5, 'ff00ff00', 'Good Accuracy'),                   # Green
        (0.5, 3.0, 'ffffff00', 'Small Positive Error'),             # Cyan
        (3.0, 10.0, 'ffff8000', 'Medium Positive Error'),            # Blue
        (10.0, float('inf'), 'ff0000ff', 'Large Positive Error')     # Purple
    ]
    
    # Create styles
    for i, (min_err, max_err, color, name) in enumerate(error_ranges):
        style = SubElement(document, 'Style', id=f'error_style_{i}')
        icon_style = SubElement(style, 'IconStyle')
        SubElement(icon_style, 'color').text = color
        SubElement(icon_style, 'scale').text = '0.8'
        icon = SubElement(icon_style, 'Icon')
        SubElement(icon, 'href').text = 'http://maps.google.com/mapfiles/kml/shapes/shaded_dot.png'
    
    # Add beacon location
    beacon_placemark = SubElement(document, 'Placemark')
    SubElement(beacon_placemark, 'name').text = 'Beacon Location'
    SubElement(beacon_placemark, 'description').text = f'Beacon at {beacon_lat:.6f}, {beacon_lon:.6f}'
    beacon_style = SubElement(document, 'Style', id='beacon_style')
    beacon_icon_style = SubElement(beacon_style, 'IconStyle')
    SubElement(beacon_icon_style, 'color').text = 'ff000000'  # Black
    SubElement(beacon_icon_style, 'scale').text = '1.5'
    beacon_icon = SubElement(beacon_icon_style, 'Icon')
    SubElement(beacon_icon, 'href').text = 'http://maps.google.com/mapfiles/kml/shapes/target.png'
    SubElement(beacon_placemark, 'styleUrl').text = '#beacon_style'
    beacon_point = SubElement(beacon_placemark, 'Point')
    SubElement(beacon_point, 'coordinates').text = f'{beacon_lon},{beacon_lat},0'
    
    # Add GPS points
    for idx, row in df.iterrows():
        if pd.isna(row['latitude']) or pd.isna(row['longitude']) or pd.isna(row['beacon_error']):
            continue
            
        # Determine style based on error
        style_id = 'error_style_3'  # Default to good accuracy
        for i, (min_err, max_err, color, name) in enumerate(error_ranges):
            if min_err <= row['beacon_error'] < max_err:
                style_id = f'error_style_{i}'
                break
        
        placemark = SubElement(document, 'Placemark')
        SubElement(placemark, 'name').text = f'Point {idx}'
        description = f"""
        Timestamp: {row['timestamp']}
        UWB Distance: {row['distance']:.2f}m
        GPS Distance: {row['actual_distance']:.2f}m
        Beacon Error: {row['beacon_error']:.2f}m
        Altitude: {row['altitude']:.1f}m
        """
        SubElement(placemark, 'description').text = description.strip()
        SubElement(placemark, 'styleUrl').text = f'#{style_id}'
        
        point = SubElement(placemark, 'Point')
        SubElement(point, 'coordinates').text = f'{row["longitude"]},{row["latitude"]},{row["altitude"]}'
    
    # Create KML string
    rough_string = tostring(kml, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    kml_str = reparsed.toprettyxml(indent="  ")
    
    # Create KMZ file
    kml_filename = 'doc.kml'
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as kmz:
        kmz.writestr(kml_filename, kml_str)
    
    print(f"KMZ file created: {output_filename}")

# Usage example (add this to your main script):
# create_kmz_from_dataframe(merged_df, 'aircraft_track.kmz', beacon_lat, beacon_lon)