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
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pyproj import Geod
from warnings import warn

# Inputs----------------------------------------------------------------
## Parse input arguments
parser = argparse.ArgumentParser()
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
    "--width", "-dx", type = float, default = 100,
    help = "Side 1 of the rectangular plot ('width') in m. Defaults to 100 m."
    )
parser.add_argument(
    "--height", "-dy", type = float, default = 100,
    help = "Side 2 of the rectangular plot ('height') in m. Defaults to 100 m."
    )
parser.add_argument(
    "--area", "-area", type = float, default = 10000,
    help = "Area of the rectangular plot in m^2." +
        "Defaults to {defaults.area}."
    )

args = parser.parse_args()

# Functions-------------------------------------------------------------
def rotate_gdf(gdf, x_centre, y_centre, angle):
    """
    Rotate a GeoDataFrame around a specified centre point by a given
    angle.

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
    rect_rotation_rad = np.deg2rad(360 - angle)
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

def get_plot(latitude, longitude, width, height, plotangle):
    df = pd.DataFrame({
        "ID": [1],
        "Latitude": [latitude],
        "Longitude": [longitude]
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
    left = x_centre - (width / 2)
    right = x_centre + (width / 2)
    top = y_centre + (height / 2)
    bottom = y_centre - (height / 2)

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
    if plotangle != 90:
        plot_gdf_utm = rotate_gdf(
            gdf = plot_gdf_utm,
            x_centre = x_centre, y_centre = y_centre,
            angle = plotangle - 90
            )
    
    return plot_gdf_utm

# Body------------------------------------------------------------------
if __name__ == "__main__":
    ## Create plot
    plot_gdf_utm = get_plot(
        latitude = args.latitude,
        longitude = args.longitude,
        width = args.width,
        height = args.height,
        plotangle = args.plotangle
    )
    plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
    dst = os.path.splitext(args.destfile)[0] + ".kml"
    plot_gdf.to_file(dst, driver = "KML")