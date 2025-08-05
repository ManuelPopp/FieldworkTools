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

from config import ParameterSet, Defaults, keydict

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
    "--imgsamplingmode", "-ism", type = str, default = defaults.imgsamplingmode,
    choices = ["time", "distance"],
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

## Set spacing if missing; else, overwrite side overlap
if args.spacing is None:
    """Not working! Not working! Not working! Not working! Not working!
    args.spacing = np.tan(
        (args.horizontalfov / 2) * np.pi / 180
        ) * args.altitude * (2 - args.sideoverlap)
    """
    c1, c2 = args.coefficients
    args.spacing = (c1 * args.sideoverlap * 100 + c2) * args.altitude
else:
    """Not working! Not working! Not working! Not working! Not working!
    args.sideoverlap = 2 - args.spacing / (
        np.tan((args.horizontalfov / 2) * np.pi / 180) * args.altitude
        )
    """
    c1, c2 = args.coefficients
    args.sideoverlap = (args.spacing / (args.altitude * 100) - c2) / c1
    warn(
        "Spacing set by user. This will override the side overlap. " +
        f"Side overlap is now {args.sideoverlap}."
        )

if args.sideoverlap < 0 or args.sideoverlap > 1:
    raise ValueError(
        "Side overlap (fraction) must be between 0 and 1. " +
        f"Got {args.sideoverlap}."
        )

## Compute a default buffer value if not set
if args.buffer is None:
    args.buffer = args.spacing / 2

args.buffer = int(round(args.buffer))

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

## Print input settings
print("== Settings ==")
for arg, value in args.__dict__.items():
    print(f"{arg}={value}")

# Functions-------------------------------------------------------------
def get_heading_angle(p0, p1, utm_crs, src_crs = "EPSG:4326"):
    """
    Compute the heading angle (azimuth) between two waypoints.

    Parameters
    ----------
    p0 : tuple
        Coordinates of the first point (longitude, latitude).
    p1 : tuple
        Coordinates of the second point (longitude, latitude).
    utm_crs : str
        UTM coordinate reference system (CRS) to use for the calculation.
    src_crs : str, optional
        Source CRS of the input points, by default "EPSG:4326".
    
    Returns
    -------
    float
        Heading angle in degrees.
    
    """
    pdf = pd.DataFrame({
        "ID": [0, 1],
        "Latitude": [p0[0], p1[0]],
        "Longitude": [p0[1], p1[1]]
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

def rotate_gdf(gdf, x_centre, y_centre, angle):
    """
    Rotate a GeoDataFrame around a specified centre point by a given angle.

    Parameters
    ----------
    gdf : GeoDataFrame
        The GeoDataFrame containing the geometries to rotate.
    x_centre : float
        X coordinate of the centre point around which to rotate.
    y_centre : float
        Y coordinate of the centre point around which to rotate.
    angle : float
        Angle in degrees by which to rotate the geometries.
    """
    centre_utm = np.array([x_centre, y_centre])
    coords = np.array(gdf.get_coordinates())
    corners_rel_to_ctr = coords - centre_utm
    rect_rotation_rad = np.deg2rad(angle)
    rotation_matrix = np.array([
        [np.cos(rect_rotation_rad), -np.sin(rect_rotation_rad)],
        [np.sin(rect_rotation_rad), np.cos(rect_rotation_rad)]
    ])
    rotated_corners_rel_to_ctr = corners_rel_to_ctr @ rotation_matrix.T
    coords_rotated = rotated_corners_rel_to_ctr + centre_utm
    geometries = [Point(xy) for xy in coords_rotated]
    data = {
        "Latitude": coords_rotated[:, 1],
        "Longitude": coords_rotated[:, 0],
        "geometry": geometries
    }
    return gpd.GeoDataFrame(data, crs = gdf.crs)

def get_heading_angle(p0, p1):
    geod = Geod(ellps = "WGS84")
    azimuth, _, _ = geod.inv(p0[1], p0[0], p1[1], p1[0])

    return azimuth

def estimate_lidar_forward_overlap(velocity, altitude, theta_deg = 75.):
    """
    Estimate the forward overlap for LiDAR missions based on velocity
    and altitude. (Warning: Might not work. Currently not required.)
    
    Parameters
    ----------
    velocity : float
        Flight velocity in m/s.
    altitude : float
        Flight altitude in meters.
    theta_deg : float, optional
        Scan angle in degrees, by default 75.
    
    Returns
    -------
    float
        Forward overlap as a fraction.
    
    """
    effective_scan_revisit_rate = 0.23
    warn(
        f"Actual revisit rate is unknown. Using {effective_scan_revisit_rate} s."
        )
    
    theta_rad = np.radians(theta_deg)
    fo = 1 - (
        velocity / effective_scan_revisit_rate
        ) / (
            2 * altitude * np.tan(theta_rad / 2)
            )

    return fo

def get_overlaps(
        horizontalfov, secondary_hfov, altitude, spacing, overlapsensor,
        side_overlap, front_overlap
        ):
        """NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING!
        Calculate the overlaps for the flight pattern based on the
        horizontal field of view, secondary horizontal field of view,
        altitude, spacing, and overlap sensor.

        Parameters
        ----------
        horizontalfov : float
            Horizontal field of view in degrees.
        secondary_hfov : float
            Secondary horizontal field of view in degrees.
        altitude : float
            Flight altitude in meters.
        spacing : float
            Flight spacing in meters.
        overlapsensor : str
            Overlap sensor type.
        side_overlap : float
            Side overlap as a fraction (0 to 1).
        front_overlap : float
            Front overlap as a fraction (0 to 1).
        
        Returns
        -------
        tuple
            Tuple containing the left side overlap, left width overlap,
            centre side overlap, and centre width overlap.
        
        """
        if overlapsensor.lower() in ["rgb", "ms"]:
            lsolaph = colaph = front_overlap
            lsolapw = colapw = side_overlap

        if overlapsensor.lower() == "ls":
            #side_ol_main = 2 - spacing / (
            #    np.tan((horizontalfov / 2) * np.pi / 180) * altitude
            #    )
            try:
                side_ol_sec = (
                    2 - spacing / (
                        np.tan((secondary_hfov / 2) * np.pi / 180) * altitude
                        )
                    ) * 100
            except TypeError as e:
                warn(
                    f"Error calculating side overlap: {e}. Using side " +
                    f"overlap {side_overlap} for secondary sensor."
                    )
                side_ol_sec = side_overlap
            
            lsolaph = front_overlap
            lsolapw = side_overlap
            colaph = front_overlap
            colapw = side_ol_sec
        
        return (lsolaph, lsolapw, colaph, colapw)

def photo_trigger_intervals(
        front_overlap_fraction, vertical_fov, altitude, velocity
        ):
    """NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING! NOT WORKING!
    Calculate the time interval between photo triggers based on the
    front overlap fraction, vertical field of view, altitude, and velocity.
    
    Parameters
    ----------
    front_overlap_fraction : float
        Fraction of front overlap (0 to 1).
    vertical_fov : float
        Vertical field of view in degrees.
    altitude : float
        Flight altitude in meters.
    velocity : float
        Flight velocity in m/s.
    
    Returns
    -------
    float
        Time interval between photo triggers in seconds.
    
    """
    try:
        fov_half = vertical_fov / 2 * np.pi / 180
        delta_t = (
            2 - front_overlap_fraction
            ) * np.tan(fov_half) * altitude / velocity
        return delta_t
    except ZeroDivisionError as e:
        warn(f"Error calculating photo trigger intervals: {e}. Using default.")
    except TypeError as e:
        warn(f"Error calculating photo trigger intervals: {e}. Using default.")
    return 1.0

def get_mapping_vertical_fov():
    """
    Get the mapping for vertical field of view (FOV).
    """
    if args.overlapsensor.lower() in ["rgb", "ms"]:
        fov = args.verticalfov
    else:
        fov = args.secondary_vfov
    
    return fov

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
y_centre = gdf_utm.get_coordinates().y[0]
x_centre = gdf_utm.get_coordinates().x[0]
left = x_centre - (args.width / 2)
right = x_centre + (args.width / 2)
top = y_centre + (args.height / 2)
bottom = y_centre - (args.height / 2)

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

# Rotate plot if required
if args.plotangle != 90:
    plot_gdf_utm = rotate_gdf(
        gdf = plot_gdf_utm,
        x_centre = x_centre, y_centre = y_centre,
        angle = args.plotangle - 90
        )

plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
plot_coordinates = plot_gdf.get_coordinates()

## Generate template.kml
lsolaph, lsolapw, colaph, colapw = get_overlaps(
    args.horizontalfov, args.secondary_hfov, args.altitude, args.spacing,
    args.overlapsensor, side_overlap, front_overlap
    )

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
        IMGSPLMODE = "time" if args.imgsamplingmode == "time" else "distance",
        TRANSITIONSPEED = args.transitionspeed,
        EXECALTITUDE = args.altitude,
        ALTITUDE = args.altitude,
        TOSECUREHEIGHT = args.tosecurealt,
        MARGIN = args.buffer,
        ANGLE = args.plotangle,
        LIDARRETURNS = keydict["lidar_returns"][args.lidar_returns],
        SAMPLINGRATE = args.sampling_rate,
        SCANNINGMODE = args.scanning_mode,
        LHOVERLAP = lsolaph,
        LWOVERLAP = lsolapw,
        CHOVERLAP = colaph,
        CWOVERLAP = colapw
        )

with zipfile.ZipFile(args.destfile, "a") as zf:
    with zf.open("wpmz/template.kml", "w") as f:
        f.write(template.encode("utf8"))

## Generate waylines.wpml
top -= 0.5 * args.spacing
bottom += 0.5 * args.spacing
span = (top + 2 * args.buffer - bottom)
n_parts = int(span // args.spacing)
offset = (span - n_parts * args.spacing) / 2
start = bottom - args.buffer + offset
end = top + args.buffer
y_values = np.arange(start, end, args.spacing)[::-1]

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

final_point = gpd.GeoDataFrame(
    geometry = [Point(args.longitude, args.latitude)],
    crs = "EPSG:4326"
)

final_point_utm = final_point.to_crs(local_crs)

wayline_gdf_utm = pd.concat(
    [wayline_gdf_utm, final_point_utm], ignore_index = True
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