#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Manuel"
__date__ = "Mon Jul 18 10:34:06 2025"
__credits__ = ["Manuel R. Popp", "Elena Plekhanova"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

# Imports---------------------------------------------------------------
import os
import time
import argparse
import zipfile
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pyproj import Geod
from warnings import warn

from config import ParameterSet, Defaults
from mission import Mission
from lib.functions import *

# Inputs----------------------------------------------------------------
## Parse input arguments
defaults = Defaults()
parser = argparse.ArgumentParser()
parser.add_argument(
    "sensor", choices = defaults.sensorchoices, action = ParameterSet,
    default = defaults.sensor,
    help = "Sensor model."
    )
parser.add_argument(
    "--latitude", "-lat", type = float,
    help = "Latitude of the plot centre point."
    )
parser.add_argument(
    "--longitude", "-lon", type = float,
    help = "Longitude of the plot centre point."
    )
parser.add_argument(
    "--destfile", "-dst", type = str,
    help = "Output file."
    )
parser.add_argument(
    "--plotangle", "-ra", type = int, default = 90,
    help = "Route angle (relative to a South-North vector) in degrees." +
        "Defaults to 90 degrees (West-East direction)."
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
    help = "Take-off security altitude in m. " +
        f"Defaults to {defaults.tosecurealt}."
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
    "--verticalfov", "-vfov", type = float, default = 48.1,
    help = "UAV camera field of view in degrees. " +
        f"Defaults to {defaults.verticalfov} (Mavic 3M MS camera)."
    )
parser.add_argument(
    "--secondary_hfov", "-shfov", type = float, default = 84.0,
    help = "UAV secondary camera horizontal field of view in degrees. " +
        f"Defaults to {defaults.secondary_hfov} (Mavic 3M RGB camera)."
    )
parser.add_argument(
    "--secondary_vfov", "-svfov", type = float, default = None,
    help = "UAV secondary camera vertical field of view in degrees. " +
        f"Defaults to {defaults.secondary_vfov} (Mavic 3M RGB camera)."
    )
parser.add_argument(
    "--coefficients", "-coefs", type = float, nargs = 4, default = None,
    help = "A list of empirical coefficients to calculate side overlap."
    )
parser.add_argument(
    "--flightspeed", "-v", type = float, default = defaults.flightspeed,
    help = "UAV mission flight speed in m/s." +
        f"Defaults to {defaults.flightspeed}."
    )
parser.add_argument(
    "--transitionspeed", "-ts", type = float,
    default = defaults.transitionspeed,
    help = "UAV transition speed in m/s. " +
        f"Defaults to {defaults.transitionspeed}."
    )
parser.add_argument(
    "--wpturnmode", "-wptm", type = str,
    choices = [
        "toPointAndStopWithDiscontinuityCurvature",
        "toPointAndStopWithContinuityCurvature",
        "toPointAndPassWithContinuityCurvature",
        "coordinateTurn"
        ],
    default = defaults.wpturnmode,
    help = "\n".join([
        "Waypoint turn mode. Options:",
        "toPointAndStopWithDiscontinuityCurvature: " +
        "Fly in a straight line and the aircraft stops at the point.",
        "toPointAndStopWithContinuityCurvature: " +
        "Fly in a curve and the aircraft stops at the point.",
        "toPointAndPassWithContinuityCurvature: " +
        "Fly in a curve and the aircraft will not stop at the point.",
        "coordinateTurn: " +
        "Coordinated turns, no dips, early turns.",
        f"Defaults to {defaults.wpturnmode}."
    ])
)
parser.add_argument(
    "--imgsamplingmode", "-ism", type = str,
    choices = ["time", "distance"],
    default = defaults.imgsamplingmode,
    help = f"Image sampling mode. Defaults to {defaults.imgsamplingmode}."
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
    "--calibrateimu", "-cimu", type = str, action = "store_true",
    help = f"LiDAR sensor IMU calibration."
    )
parser.add_argument(
    "--gridmode", "-gm", action = "store_true",
    help = "Use grid mode for the flight pattern. " +
        "This will create a grid of flight paths instead of parallel lines."
)
parser.add_argument(
    "--template_directory", type = str, default = defaults.template_directory,
    help = argparse.SUPPRESS
    )

args = parser.parse_args()

# Body------------------------------------------------------------------
## Create dataframe
mission = Mission(args)

## Generate template.kml
mission.write_template_kml()

## Generate waylines.wpml
top -= 0.5 * args.spacing
bottom += 0.5 * args.spacing
span = (top + 2 * args.buffer - bottom)
n_parts = int(span // args.spacing)
offset = (span - n_parts * args.spacing) / 2
start = bottom - args.buffer + offset
end = top + args.buffer

wayline_gdf_utm = lines_horizontal(
    left = left,
    right = right,
    start = start,
    end = end
)

if args.gridmode:
    wayline_gdf_utm = wayline_gdf_utm.iloc[:-1]
    right -= 0.5 * args.spacing
    left += 0.5 * args.spacing
    span = (right + 2 * args.buffer - left)
    n_parts = int(span // args.spacing)
    offset = (span - n_parts * args.spacing) / 2
    start = left - args.buffer + offset
    end = right + args.buffer

    wayline_gdf_utm_vertical = lines_vertical(
        top = top,
        bottom = bottom,
        start = start,
        end = end,
        start_x = wayline_gdf_utm.get_coordinates().iloc[-1, 0]
    )

    wayline_gdf_utm = pd.concat(
        [wayline_gdf_utm, wayline_gdf_utm_vertical], ignore_index = True
        )

# Rotate flight paths if required
if args.plotangle != 90:
    wayline_gdf_utm = rotate_gdf(
        gdf = wayline_gdf_utm,
        x_centre = x_centre, y_centre = y_centre,
        angle = args.plotangle - 90
    )

# Convert wayline coordinates to EPSG:4326 and generate placemarks
wayline_gdf = wayline_gdf_utm.to_crs("EPSG:4326")
wayline_coordinates = wayline_gdf.get_coordinates()

action_trigger = photo_trigger_intervals(
    front_overlap_fraction = colapw / 100,
    vertical_fov = get_mapping_vertical_fov(),
    altitude = args.altitude,
    velocity = args.flightspeed
    )

with open(
    os.path.join(args.template_directory, "template_placemark.txt"), "r"
    ) as file:
    template_placemark = file.read()

placemarks = ""

for index, (longitude, latitude) in wayline_coordinates.iterrows():
    if index == wayline_coordinates.shape[0] - 1:
        heading_angle = 0
    else:
        heading_angle = get_heading_angle(
            p0 = (longitude, latitude),
            p1 = (
                wayline_coordinates.x[index + 1],
                wayline_coordinates.y[index + 1]
                )
            )
    
    placemark = template_placemark.format(
        LATITUDE = np.round(latitude, 13),
        LONGITUDE = np.round(longitude, 13),
        INDEX = index,
        EXECALTITUDE = args.altitude,
        WPSPEED = args.flightspeed,
        WPTURNMODE = args.wpturnmode,
        WPHEADINGANGLE = heading_angle,
        ACTIONMODE = "multipleTime" if args.imgsamplingmode == "time" \
            else "multipleDistance",
        ACTIONTRIGGER = action_trigger
        )
    
    placemarks += placemark

path_last = Point(longitude, latitude)

flightroute = LineString(wayline_gdf_utm.geometry.tolist())
total_distance = flightroute.length

print(f"Total distance of flight route: {total_distance:.2f} m.")
print(f"Estimated flight duration: {total_distance / args.flightspeed:.2f} s.")

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


from matplotlib import pyplot as plt

plot_polygon = Polygon(plot_gdf_utm.geometry.tolist())
poly_gdf = gpd.GeoDataFrame(geometry = [plot_polygon], crs = plot_gdf_utm.crs)
ax = poly_gdf.plot(color = "none", edgecolor = "blue")

wayline_gdf = gpd.GeoDataFrame(geometry = [flightroute], crs = wayline_gdf_utm.crs)
wayline_gdf.plot(ax = ax, color = "red")
plt.show()