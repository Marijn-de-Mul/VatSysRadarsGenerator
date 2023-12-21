import os
import requests
import xml.etree.ElementTree as ET
from xml.dom import minidom

OUTPUT_DIR = 'Output'
RADARS_FILE = 'Radars.xml'
FULL_PATH = os.path.join(OUTPUT_DIR, RADARS_FILE)

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

if os.path.exists(FULL_PATH):
    os.remove(FULL_PATH)

def get_elevation_data(latitude, longitude):
    base_url = "https://api.open-meteo.com/v1/elevation"

    params = {
        "latitude": latitude,
        "longitude": longitude
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        elevation_in_meters = data["elevation"][0] 
        elevation_in_feet = elevation_in_meters * 3.28084

        return round(elevation_in_feet)  

    else:
        response.raise_for_status()

def dms_to_dd(dms):
    if len(dms) > 9: 
        degrees, minutes, seconds, direction = int(dms[:3]), int(dms[3:5]), float(dms[5:-1]), dms[-1]
    else:  
        degrees, minutes, seconds, direction = int(dms[:2]), int(dms[2:4]), float(dms[4:-1]), dms[-1]

    dd = degrees + minutes/60 + seconds/3600

    if direction in ('S','W'):
        dd *= -1

    return dd

def convert_coordinates(coord_string):
    lat_dms, lon_dms = coord_string.split()

    lat_dd = dms_to_dd(lat_dms)
    lon_dd = dms_to_dd(lon_dms)

    return "{:010.6f}{:+011.6f}".format(lat_dd, lon_dd)

def create_radar_element(name, elevation, max_range, lat_dd, lon_dd):
    radar = ET.Element('Radar')

    radar.set('Name', name)
    radar.set('Type', 'ADSB')
    radar.set('Elevation', str(elevation))
    radar.set('MaxRange', max_range)

    ET.SubElement(radar, 'Lat').text = "{:+010.6f}".format(lat_dd)
    ET.SubElement(radar, 'Long').text = "{:+011.6f}".format(lon_dd)

    return radar

root = ET.Element('Radars')

with open('Input/ADSB_Stations.txt', 'r') as f:
    next(f)  

    for line in f:
        fields = line.strip().split(',')
        if len(fields) != 6:
            print(f'Skipping line {fields[0]} due to improperly formatted line: {line.strip()}')
            continue
        no, location, lat_dms, lon_dms, coverage, _ = fields
        lat_dd = dms_to_dd(lat_dms)
        lon_dd = dms_to_dd(lon_dms)
        elevation = get_elevation_data(lat_dd, lon_dd)

        radar_adsb = create_radar_element(location, elevation, coverage, lat_dd, lon_dd)
        radar_adsb.set('Type', 'ADSB')
        root.append(radar_adsb)

with open('Input/SSR_Stations.txt', 'r') as f:
    next(f)  

    for line in f:
        fields = line.strip().split(',')
        if len(fields) != 6:
            print(f'Skipping line {fields[0]} due to improperly formatted line: {line.strip()}')
            continue
        no, location, lat_dms, lon_dms, coverage, _ = fields
        lat_dd = dms_to_dd(lat_dms)
        lon_dd = dms_to_dd(lon_dms)
        elevation = get_elevation_data(lat_dd, lon_dd)

        radar_ssr = create_radar_element(location, elevation, coverage, lat_dd, lon_dd)
        radar_ssr.set('Type', 'SSR_ModeC')
        root.append(radar_ssr)

with open('Input/PSR_Stations.txt', 'r') as f:
    next(f)  

    for line in f:
        fields = line.strip().split(',')
        if len(fields) != 6:
            print(f'Skipping line {fields[0]} due to improperly formatted line: {line.strip()}')
            continue
        no, location, lat_dms, lon_dms, coverage, _ = fields
        lat_dd = dms_to_dd(lat_dms)
        lon_dd = dms_to_dd(lon_dms)
        elevation = get_elevation_data(lat_dd, lon_dd)

        radar_psr = create_radar_element(location, elevation, coverage, lat_dd, lon_dd)
        radar_psr.set('Type', 'PRI')
        root.append(radar_psr)

with open('Input/SMR_Stations.txt', 'r') as f:
    for line in f:
        fields = line.strip().split(',')
        if fields[0] == 'A':
            location = fields[2].capitalize()  
            lat_dd = float(fields[3])
            lon_dd = float(fields[4])
            elevation = get_elevation_data(lat_dd, lon_dd)

            radar_smr = create_radar_element(location, elevation, '200', lat_dd, lon_dd)
            radar_smr.set('Type', 'SMR')
            root.append(radar_smr)

tree = ET.ElementTree(root)

xml_string = ET.tostring(root, 'utf-8')

parsed_xml = minidom.parseString(xml_string)

pretty_xml = parsed_xml.toprettyxml(indent="  ")

with open(FULL_PATH, 'w') as f:
    f.write(pretty_xml)