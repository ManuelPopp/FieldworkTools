# Imports---------------------------------------------------------------
import os
import time
import argparse
import tempfile
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

from config import ParameterSet, Defaults, keydict

# Inputs----------------------------------------------------------------
## Parse input arguments
defaults = Defaults()
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
parser.add_argument(
    "--sensor", "-sensor", choices = defaults.sensorchoices,
    action = ParameterSet,
    default = defaults.sensor,
    help = "Sensor model."
    )
parser.add_argument(
    "--gsd", "-gsd", type = float, default = defaults.gsd,
    help = "Ground sampling distance in cm."
    )
parser.add_argument(
    "--sensorfactor", "-sf", type = float, default = defaults.sensorfactor,
    help = "Image width * focal length / sensor width. " +
        f"Defaults to {defaults.sensorfactor} (Mavic M3M)."
    )
parser.add_argument(
    "--altitude", "-alt", type = float, default = defaults.altitude,
    help = "Flight altitude. Defaults calculated based on sensor factor and GSD."
    )
parser.add_argument(
    "--tosecurealt", "-tsa", type = float, default = defaults.tosecurealt,
    help = f"Take-off security altitude in m. Defaults to {defaults.tosecurealt}."
    )
parser.add_argument(
    "--width", "-dx", type = float, default = defaults.width,
    help = "Side 1 of the rectangular plot ('width') in m. Defaults to 100 m."
    )
parser.add_argument(
    "--height", "-dy", type = float, default = defaults.height,
    help = "Side 2 of the rectangular plot ('height') in m. Defaults to 100 m."
    )
parser.add_argument(
    "--area", "-area", type = float, default = defaults.area,
    help = "Area of the rectangular plot in m^2." +
        "Defaults to {defaults.area}."
    )
parser.add_argument(
    "--sideoverlap", "-slap", type = float, default = defaults.sideoverlap,
    help = "Overlap between parallel flight paths (fraction)." +
        f"Defaults to {defaults.sideoverlap}."
    )
parser.add_argument(
    "--frontoverlap", "-fol", type = float, default = None,
    help = "Overlap between images in direction of movement (fraction). " +
        f"Defaults to {defaults.frontoverlap}."
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
    "--horizontalfov", "-hfov", type = float, default = 61.2,
    help = "UAV camera field of view in degrees. " +
        f"Defaults to {defaults.horizontalfov} (Mavic 3M MS camera)."
    )
parser.add_argument(
    "--flightspeed", "-v", type = float, default = defaults.flightspeed,
    help = "UAV mission flight speed in m/s." +
        f"Defaults to {defaults.flightspeed}."
    )
parser.add_argument(
    "--transitionspeed", "-ts", type = float, default = defaults.transitionspeed,
    help = f"UAV transition speed in m/s. Defaults to {defaults.transitionspeed}."
    )
parser.add_argument(
    "--lidar_returns", "-lr", type = int, default = defaults.lidar_returns,
    help = f"Lidar returns mode. Defaults to {defaults.lidar_returns}."
    )
parser.add_argument(
    "--sampling_rate", "-sr", type = int, default = defaults.sampling_rate,
    help = f"LiDAR sampling rate. Defaults to {defaults.sampling_rate}."
    )
parser.add_argument(
    "--scanning_mode", "-sm", type = str, default = defaults.scanning_mode,
    choices = ["repetitive", "nonRepetitive"],
    help = f"LiDAR scanning mode. Defaults to {defaults.scanning_mode}."
    )
parser.add_argument(
    "--template_directory", type = str, default = defaults.template_directory,
    help = argparse.SUPPRESS
    )

args = parser.parse_args()

# Settings--------------------------------------------------------------
## Ensure the output is a .kmz file
if os.path.splitext(args.destfile)[1].lower() != ".kmz":
    args.destfile = args.destfile + ".kmz"

## Get altitude from sensor parameters and GSD if not set
if args.altitude is None:
    args.altitude = args.gsd * args.sensorfactor

## Set plot width and height if missing
if args.width is None and args.height is None:
    args.width = np.sqrt(args.area)
    args.height = np.sqrt(args.area)

if args.width is None:
    args.width = args.area / args.height

if args.height is None:
    args.height = args.area / args.width

## Set spacing if missing
if args.spacing is None:
    args.spacing = np.tan(
        (args.horizontalfov / 2) * np.pi / 180
        ) * args.altitude * (2 - args.sideoverlap)

if args.buffer is None:
    args.buffer = args.spacing / 2

## Use integers where possible (like DJI does)
if args.altitude == int(args.altitude):
    args.altitude = int(args.altitude)

if args.tosecurealt == int(args.tosecurealt):
    args.tosecurealt = int(args.tosecurealt)

if args.flightspeed == int(args.flightspeed):
    args.flightspeed = int(args.flightspeed)

if args.transitionspeed == int(args.transitionspeed):
    args.transitionspeed = int(args.transitionspeed)

## Convert overlaps to percentages
side_overlap = int(args.sideoverlap * 100)
front_overlap = int(args.frontoverlap * 100)

if args.overlapsensor in ["RGB", "MS"]:
    lsolaph = colaph = side_overlap
    lsolapw = colapw = front_overlap

if args.overlapsensor == "LS":
    lsolaph = side_overlap
    lsolapw = front_overlap
    colaph = secondary_soverlap
    colapw = secondary_foverlap

## Print input settings
print("== Settings ==")
for arg, value in args.__dict__.items():
    print(f"{arg}={value}")

# Functions-------------------------------------------------------------
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

# Body------------------------------------------------------------------
## Create dataframe
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

## Transform coordinates to UTM
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
    geometry = gpd.points_from_xy(
        plot_points_utm.Longitude,
        plot_points_utm.Latitude
        ),
    crs = local_crs
    )

plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
plot_coordinates = plot_gdf.get_coordinates()

## Generate template.kml
with open(
    os.path.join(args.template_directory, "wpmz", "template.kml"), "r"
    ) as file:
    template_text = file.read()
    template = template_text.format(
        TIMESTAMP = int(time.time() * 1000),
        LONGITUDEMIN = np.round(min(plot_coordinates.x), 13),
        LONGITUDEMAX = np.round(max(plot_coordinates.x), 13),
        LATITUDEMIN = np.round(min(plot_coordinates.y), 13),
        LATITUDEMAX = np.round(max(plot_coordinates.y), 13),
        AUTOFLIGHTSPEED = args.flightspeed,
        TRANSITIONSPEED = args.transitionspeed,
        EXECALTITUDE = args.altitude,
        ALTITUDE = args.altitude,
        TOSECUREHEIGHT = args.tosecurealt,
        LIDARRETURNS = keydict["lidar_returns"][args.lidar_returns],
        SAMPLINGRATE = args.sampling_rate,
        SCANNINGMODE = args.scanning_mode,
        LHOVERLAP = lhoverlap,
        LWOVERLAP = lwoverlap,
        CHOVERLAP = choverlap,
        CWOVERLAP = cwoverlap
        )

with zipfile.ZipFile(args.destfile, "a") as zf:
    with zf.open("wpmz/template.kml", "w") as f:
        f.write(template.encode("utf8"))

## Generate waylines.wpml
remainder = (top + 2 * args.buffer - bottom) // args.spacing
y_values = np.arange(
    bottom - args.buffer + remainder / 2, top + args.buffer,
    args.spacing
    )

n_paths = len(y_values)

print(f"Number of flight paths: {n_paths}.")

x_values = [left - args.buffer, right + args.buffer]
x_coords = list()

for i in range(n_paths):
    x_coords.extend(x_values)
    x_values.reverse()

wayline_points_utm = pd.DataFrame({
    "y_coords": np.repeat(y_values, 2),
    "x_coords": x_coords
    })

wayline_gdf_utm = gpd.GeoDataFrame(
    wayline_points_utm,
    geometry = gpd.points_from_xy(
        wayline_points_utm.x_coords, wayline_points_utm.y_coords
        ),
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

with open(
    os.path.join(args.template_directory, "template_placemark.txt"), "r"
    ) as file:
    template_placemark = file.read()

placemarks = ""

for index, (longitude, latitude) in wayline_coordinates.iterrows():
    if index == wayline_coordinates.shape[0]:
        heading_angle = get_heading_angle(
            p0 = (longitude, latitude),
            p1 = (
                wayline_coordinates.x[index + 1],
                wayline_coordinates.y[index + 1]
                ),
            utm_crs = local_crs
            )
    else:
        heading_angle = 0
    
    placemark = template_placemark.format(
        LATITUDE = np.round(latitude, 13),
        LONGITUDE = np.round(longitude, 13),
        INDEX = index,
        EXECALTITUDE = args.altitude,
        WPSPEED = args.flightspeed,
        WPHEADINGANGLE = heading_angle
        )
    
    placemarks += placemark

path_last = Point(longitude, latitude)

path_length = (max(x_values) - min(x_values))
total_distance = (args.spacing + path_length) * n_paths + path_last.distance(
    Point(args.longitude, args.latitude)
    )

with open(
    os.path.join(args.template_directory, "wpmz", "waylines.wpml"), "r"
    ) as file:
    waylines_text = file.read()
    waylines = waylines_text.format(
        PLACEMARKS = placemarks,
        TOTALDIST = total_distance,
        TOTALTIME = total_distance / args.flightspeed,
        AUTOFLIGHTSPEED = args.flightspeed,
        TRANSITIONSPEED = args.transitionspeed,
        TOSECUREHEIGHT = args.tosecurealt
        )

with zipfile.ZipFile(args.destfile, "a") as zf:
    with zf.open("wpmz/waylines.wpml", "w") as f:
        f.write(waylines.encode("utf8"))
