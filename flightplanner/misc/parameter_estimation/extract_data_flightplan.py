import geopandas as gpd
from shapely.geometry import Point
import re
from matplotlib import pyplot as plt
from shapely.geometry import LineString, Point
import numpy as np

def parallel_line_distance(p1, p2, q1, q2):
    line1 = LineString([p1, p2])
    point_on_line2 = Point(q1)
    return line1.distance(point_on_line2)

def extract_coordinates_to_gdf(file_path):
    with open(file_path, encoding = "utf-8") as f:
        text = f.read()
    
    matches = re.findall(r"<coordinates>\s*([0-9\.\-]+),([0-9\.\-]+)\s*</coordinates>", text)
    
    geometries = [Point(float(lon), float(lat)) for lon, lat in matches]
    return gpd.GeoDataFrame(geometry = geometries, crs = "EPSG:4326")

gdf = extract_coordinates_to_gdf("C:\\Users\\poppman\\Desktop\\tmp\\40_90\\waylines.wpml")
local_crs = gdf.estimate_utm_crs()
gdf_utm = gdf.to_crs(local_crs)
coords = gdf_utm.get_coordinates()

p1 = coords.iloc[0]
p2 = coords.iloc[1]
q1 = coords.iloc[2]
q2 = coords.iloc[3]

distance = parallel_line_distance(p1, p2, q1, q2)
print("Distance:", distance)