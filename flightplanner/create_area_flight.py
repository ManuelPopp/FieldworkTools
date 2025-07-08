import os
import argparse
import tempfile
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument(
    "--latitude", "-lat", type = float,
    help = "Latitude of the plot center point."
    )
parser.add_argument(
    "--longitude", "-lon", type = float,
    help = "Longitude of the plot center point."
    )
parser.add_argument(
    "--destfile", "-dst", type = str,
    help = "Output file."
    )
parser.add_argument("--gsd", "-gsd", type = float, default = 4.,
    help = "Ground sampling distance in cm."
    )
parser.add_argument(
    "--sensorfactor", "-sf", type = float, default = 21.6888427734375,
    help = "Image width * focal length / sensor width. Defaults to 21.68 (Mavic 3M)."
    )
parser.add_argument("--altitude", "-alt", type = float, default = None,
    help = "Flight altitude. Defaults calculated based on sensor factor and GSD."
    )
parser.add_argument("--width", "-dx", type = float, default = 100.)
parser.add_argument("--height", "-dy", type = float, default = 100.)
parser.add_argument(
    "--sideoverlap", "-slap", type = float, default = .9,
    help = "Overlap between parallel flight paths as a fraction. Defaults to 0.9."
    )
parser.add_argument(
    "--spacing", "-ds", type = float, default = None,
    help = "Distance between paths of the flight pattern in m." +
    "By default calculated from camera specs and side overlap."
    )
parser.add_argument(
    "--buffer", "-buff", type = float, default = None,
    help = "Buffer around the AOI. Default is half of the path spacing."
    )
parser.add_argument(
    "--fieldofview", "-fov", type = float, default = 61.2,
    help = "UAV camera field of view in degrees. Defaults to 61.2 (Mavic M3M MS camera)."
    )
parser.add_argument(
    "--flightspeed", "-v", type = float, default = 2.,
    help = "UAV mission flight speed in m/s."
    )

args = parser.parse_args()

if os.path.splitext(args.destfile)[1].lower() != ".kmz":
    args.destfile = args.destfile + ".kmz"

if args.altitude is None:
    args.altitude = args.gsd * args.sensorfactor

if args.spacing is None:
    args.spacing = np.tan(
        (args.fieldofview / 2) * np.pi / 180
        ) * args.altitude * ((1 - args.sideoverlap) * 2)

if args.buffer is None:
    args.buffer = args.spacing / 2

print("== Settings ==")
for arg, value in args.__dict__.items():
    print(f"{arg}={value}")

# Functions
def get_heading_angle(p0, p1, utm_crs, src_crs = "EPSG:4326"):
    pdf = pd.DataFrame({
        "ID": [0, 1],
        "Latitude": p0[0],
        "Longitude": p0[1]
    })
    
    pgdf = gpd.GeoDataFrame(
        pdf,
        geometry = gpd.points_from_xy(pdf.Longitude, pdf.Latitude),
        crs = "EPSG:4326"
        )
    
    pgdf_utm = pgdf.to_crs(utm_crs)
    coords = pgdf_utm.get_coordinates()
    dx = coords.x[1] - coords.x[0]
    dy = coords.y[1] - coords.y[0]
    phi = np.arctan(dy / dx) / np.pi * 180
    
    return phi

# Create dataframe
df = pd.DataFrame({
    "ID": [1],
    "Latitude": [args.latitude],
    "Longitude": [args.longitude]
    })

gdf = gpd.GeoDataFrame(
    df,
    geometry = gpd.points_from_xy(df.Longitude, df.Latitude),
    crs = "EPSG:4326"
    )

# Transform coordinates to UTM
local_crs = gdf.estimate_utm_crs()
gdf_utm = gdf.to_crs(local_crs)
y_center = gdf_utm.get_coordinates().y[0]
x_center = gdf_utm.get_coordinates().x[0]
left = x_center - (args.width / 2)
right = x_center + (args.width / 2)
top = y_center + (args.height / 2)
bottom = y_center - (args.height / 2)

plot_points_utm = pd.DataFrame({
    "Latitude": [bottom, top, top, bottom],
    "Longitude": [left, left, right, right]
    })

plot_gdf_utm = gpd.GeoDataFrame(
    plot_points_utm,
    geometry = gpd.points_from_xy(plot_points_utm.Longitude, plot_points_utm.Latitude),
    crs = local_crs
    )

plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
plot_coordinates = plot_gdf.get_coordinates()

# Generate template.kml
with open(os.path.join(".", "template", "wpmz", "template.kml"), "r") as file:
    template_text = file.read()
    template = template_text.format(
        LONGITUDEMIN = np.round(min(plot_coordinates.x), 13),
        LONGITUDEMAX = np.round(max(plot_coordinates.x), 13),
        LATITUDEMIN = np.round(min(plot_coordinates.y), 13),
        LATITUDEMAX = np.round(max(plot_coordinates.y), 13)
        )

with zipfile.ZipFile(args.destfile, "a") as zf:
    with zf.open("wpmz/template.kml", "w") as f:
        f.write(template.encode("utf8"))

# Generate waylines.wpml
remainder = (top + 2 * args.buffer - bottom) // args.spacing
n_paths = int(np.floor((top + 2 * args.buffer - bottom) // args.spacing)) + 1
print(f"Number of flight paths: {n_paths}.")

x_values = [left - args.buffer, right + args.buffer]
x_coords = list()

for i in range(n_paths):
    x_coords.extend(x_values)
    x_values.reverse()

y_values = np.arange(
    bottom - args.buffer + remainder / 2, top + args.buffer,
    args.spacing
    )

wayline_points_utm = pd.DataFrame({
    "y_coords": np.repeat(y_values, 2),
    "x_coords": x_coords
    })

wayline_gdf_utm = gpd.GeoDataFrame(
    wayline_points_utm,
    geometry = gpd.points_from_xy(wayline_points_utm.x_coords, wayline_points_utm.y_coords),
    crs = local_crs
    )

wayline_gdf = wayline_gdf_utm.to_crs("EPSG:4326")
wayline_coordinates = wayline_gdf.get_coordinates()
wayline_coordinates = pd.concat([
    wayline_coordinates,
    pd.DataFrame({
        "x": [args.longitude],
        "y": [args.latitude]
        })
    ])

with open(os.path.join(".", "template", "template_placemark.txt"), "r") as file:
    template_placemark = file.read()

placemarks = ""

for index, (longitude, latitude) in wayline_coordinates.iterrows():
    if index == wayline_coordinates.shape[0]:
        heading_angle = get_heading_angle(
            p0 = (longitude, latitude),
            p1 = (wayline_coordinates.x[index+1], wayline_coordinates.y[index+1]),
            utm_crs = local_crs
            )
    else:
        heading_angle = 0
    
    placemark = template_placemark.format(
        LATITUDE = np.round(latitude, 13),
        LONGITUDE = np.round(longitude, 13),
        INDEX = index,
        EXECALTITUDE = args.altitude,
        WPHEADINGANGLE = heading_angle
        )
    
    placemarks += placemark

path_last = Point(longitude, latitude)

path_length = (max(x_values) - min(x_values))
total_distance = (args.spacing + path_length) * n_paths + path_last.distance(
    Point(args.longitude, args.latitude)
    )

with open(os.path.join(".", "template", "wpmz", "waylines.wpml"), "r") as file:
    waylines_text = file.read()
    waylines = waylines_text.format(
        PLACEMARKS = placemarks,
        TOTALDIST = total_distance,
        TOTALTIME = total_distance / args.flightspeed,
        AUTOFLIGHTSPEED = args.flightspeed
        )

with zipfile.ZipFile(args.destfile, "a") as zf:
    with zf.open("wpmz/waylines.wpml", "w") as f:
        f.write(waylines.encode("utf8"))
