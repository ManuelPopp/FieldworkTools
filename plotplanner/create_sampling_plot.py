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
    "--output_format", "-of", type = str, default = None,
    help = "Output file format."
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
parser.add_argument(
    "--numpoints", "-n", type = int, default = 8,
    help = "Number of points to sample within the plot area. Defaults to 8."
    )
parser.add_argument(
    "--addgpx", "-gpx", action = "store_true",
    help = "Enable additional GPX output."
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
        "x": coords_rotated[:, 0],
        "y": coords_rotated[:, 1],
        "geometry": geometries
    }
    return gpd.GeoDataFrame(data, crs = gdf.crs)

def get_plot(latitude, longitude, width, height, plotangle):
    df = pd.DataFrame({
        "ID": [1],
        "x": [longitude],
        "y": [latitude]
        })
    
    gdf = gpd.GeoDataFrame(
        df,
        geometry = gpd.points_from_xy(df.x, df.y),
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
        "x": [left, left, right, right],
        "y": [bottom, top, top, bottom]
        })
    
    plot_gdf_utm = gpd.GeoDataFrame(
        plot_points_utm,
        geometry = gpd.points_from_xy(
            plot_points_utm.x,
            plot_points_utm.y
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
    coords = list(zip(plot_gdf_utm.geometry.x, plot_gdf_utm.geometry.y))
    polygon = Polygon(coords)
    plot_polygon_gdf = gpd.GeoDataFrame(
        {"ID": [1]}, geometry = [polygon], crs = plot_gdf_utm.crs
    )
    return plot_polygon_gdf

def optimal_point_distribution(width, height, N):
    if not (isinstance(N, int) and N > 0):
        raise ValueError("N must be a positive integer.")
    if N == 1:
        return np.array([[width / 2, height / 2]])
    
    if N == 2:
        if width >= height:
            return np.array(
                [[width / 4, height / 2], [3 * width / 4, height / 2]]
                )
        else:
            return np.array(
                [[width / 2, height / 4], [width / 2, 3 * height / 4]]
            )
    if N == 3:
        return np.array(
            [
                [width / 4, height / 4],
                [3 * width / 4, height / 4],
                [width / 2, 3 * height / 4]
            ]
        )
    if N == 4:
        return np.array(
            [
                [width / 4, height / 4],
                [3 * width / 4, height / 4],
                [width / 4, 3 * height / 4],
                [3 * width / 4, 3 * height / 4]
            ]
        )
    if N == 5:
        return np.array(
            [
                [width / 4, height / 4],
                [3 * width / 4, height / 4],
                [width / 2, height / 2],
                [width / 4, 3 * height / 4],
                [3 * width / 4, 3 * height / 4]
            ]
        )
    if N == 6:
        if width >= height:
            return np.array([
                [width / 4, height / 4],
                [width / 2, height / 4],
                [3 * width / 4, height / 4],
                [width / 4, 3 * height / 4],
                [width / 2, 3 * height / 4],
                [3 * width / 4, 3 * height / 4]
            ])
        else:
            return np.array([
                [width / 4, height / 4],
                [width / 4, height / 2],
                [width / 4, 3 * height / 4],
                [3 * width / 4, height / 4],
                [3 * width / 4, height / 2],
                [3 * width / 4, 3 * height / 4]
            ])
    if N == 8:
        if width > 2 / 3 * height and height > 2 / 3 * width:
            return np.array([
                [width / 4, height / 4],
                [width / 4, height / 2],
                [width / 4, 3 * height / 4],
                [width / 2, height / 4],
                [width / 2, 3 * height / 4],
                [3 * width / 4, height / 4],
                [3 * width / 4, height / 2],
                [3 * width / 4, 3 * height / 4],
            ])
        if width >= 2 * height and width < 3 * height:
            return np.array([
                [width / 5, height / 3],
                [width / 5, 2 * height / 3],
                [2 * width / 5, height / 3],
                [2 * width / 5, 2 * height / 3],
                [3 * width / 5, height / 3],
                [3 * width / 5, 2 * height / 3],
                [4 * width / 5, height / 3],
                [4 * width / 5, 2 * height / 3]
            ])
        if height >= 2 * width and height < 3 * width:
            return np.array([
                [width / 3, height / 5],
                [width / 3, 2 * height / 5],
                [width / 3, 3 * height / 5],
                [width / 3, 4 * height / 5],
                [2 * width / 3, height / 5],
                [2 * width / 3, 2 * height / 5],
                [2 * width / 3, 3 * height / 5],
                [2 * width / 3, 4 * height / 5]
            ])
        if height >= 3 * width:
            return np.array([
                [width / 2, height / 9],
                [width / 2, 2 * height / 9],
                [width / 2, 3 * height / 9],
                [width / 2, 4 * height / 9],
                [width / 2, 5 * height / 9],
                [width / 2, 6 * height / 9],
                [width / 2, 7 * height / 9],
                [width / 2, 8 * height / 9]
            ])
        if width >= 3 * height:
            return np.array([
                [width / 9, height / 2],
                [2 * width / 9, height / 2],
                [3 * width / 9, height / 2],
                [4 * width / 9, height / 2],
                [5 * width / 9, height / 2],
                [6 * width / 9, height / 2],
                [7 * width / 9, height / 2],
                [8 * width / 9, height / 2]
            ])
    if N == 9:
        if width > 2 / 3 * height and height > 2 / 3 * width:
            return np.array([
                [width / 4, height / 4],
                [width / 4, height / 2],
                [width / 4, 3 * height / 4],
                [width / 2, height / 4],
                [width / 2, height / 2],
                [width / 2, 3 * height / 4],
                [3 * width / 4, height / 4],
                [3 * width / 4, height / 2],
                [3 * width / 4, 3 * height / 4],
            ])
        else:
            raise NotImplementedError(
                "Optimal distribution for N=9 is only implemented for " +
                "approximately square areas."
            )
    
def get_point_locations(
        longitude, latitude, width, height, N, plotangle,
        label = "{i}{j}"
        ):
    points = optimal_point_distribution(width, height, N)
    order = np.lexsort((points[:, 0], points[:, 1]))
    points = points[order]
    rows, row_ids = np.unique(points[:, 1], return_inverse = True)
    cols, col_ids = np.unique(points[:, 0], return_inverse = True)
    row_ids = row_ids.max() - row_ids
    labels = np.array([
        label.format(
            i = chr(ord("A") + r), j = c + 1
            ) for r, c in zip(row_ids, col_ids)
        ])
    gdf = gpd.GeoDataFrame(
        data = pd.DataFrame({"id": [1]}),
        geometry = gpd.points_from_xy([longitude], [latitude]),
        crs = "EPSG:4326"
        )
    utm_crs = gdf.estimate_utm_crs()
    gdf_utm = gdf.to_crs(utm_crs)

    points_centered = points - np.array([width / 2, height / 2])
    points_utm = points_centered + np.array([
        gdf_utm.geometry.x[0], gdf_utm.geometry.y[0]
        ])
    points_utm_df = pd.DataFrame(points_utm, columns = ["x", "y"])
    points_utm_gdf = gpd.GeoDataFrame(
        points_utm_df,
        geometry = gpd.points_from_xy(points_utm_df.x, points_utm_df.y),
        crs = utm_crs
    )
    if plotangle != 90:
        points_utm_gdf = rotate_gdf(
            points_utm_gdf,
            x_centre = gdf_utm.geometry.x[0],
            y_centre = gdf_utm.geometry.y[0],
            angle = plotangle - 90
            )
    points_gdf = points_utm_gdf.to_crs("EPSG:4326")
    points_gdf["label"] = labels

    return points_gdf

# Body------------------------------------------------------------------
if __name__ == "__main__":
    ## Create plot boundaries
    plot_gdf_utm = get_plot(
        latitude = args.latitude,
        longitude = args.longitude,
        width = args.width,
        height = args.height,
        plotangle = args.plotangle
    )
    plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
    if args.output_format is None:
        output_format = os.path.splitext(
            args.destfile
            )[1].lower().replace(".", "")
    else:
        output_format = args.output_format.lower()
    
    if output_format not in ["gpkg", "kml", "kmz"]:
        raise ValueError(
            f"Invalid output format {args.output_format}. " +
            "Supported formats are: gpkg, kml"
            )
    elif output_format == "gpkg":
        out_ext = ".gpkg"
    elif output_format == "kml":
        out_ext = ".kml"
    elif output_format == "kmz":
        warn(
            "Warning: Unsupported output format KMZ requested. Writing KML."
            )
        out_ext = ".kml"
    
    dst = os.path.splitext(args.destfile)[0] + out_ext
    
    ## Get measurement locations
    points = get_point_locations(
        longitude = args.longitude,
        latitude = args.latitude,
        width = args.width,
        height = args.height,
        N = args.numpoints,
        plotangle = args.plotangle,
        label = os.path.basename(
            os.path.splitext(args.destfile)[0]
         ) + "{i}{j}"
    )
    points = points[["label", "geometry"]]
    
    plot_gdf[["label"]] = "Boundary"
    plot_gdf = plot_gdf[points.columns]
    ## Write output
    if output_format == "gpkg":
        print("Writing to GPKG...")
        plot_gdf.to_file(dst, layer = "polygons", driver = "GPKG")
        points.to_file(dst, layer = "points", driver = "GPKG")
    elif output_format in ["kml", "kmz"]:
        print("Writing to KML...")
        combined = pd.concat([plot_gdf, points], ignore_index = True)
        combined = gpd.GeoDataFrame(
            combined, geometry = "geometry", crs = plot_gdf.crs
            )
        combined["label"] = combined["label"].astype(str)
        combined = combined.rename(columns = {"label": "Name"})
        combined["Name"] = combined["Name"].astype(str)
        combined[["Name", "geometry"]].to_file(dst, driver = "KML")
    if args.addgpx:
        print("Writing additional GPX output...")
        points_gpx = points.rename(columns = {"label": "name"})
        points_gpx["name"] = points_gpx["name"].astype(str)
        points_gpx["ele"] = 0
        points_gpx["time"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            )
        points_gpx["magvar"] = 0
        points_gpx["geoidheight"] = 0
        points_gpx = points_gpx[
            ["geometry", "ele", "time", "magvar", "geoidheight", "name"]
            ]
        dst_gpx = os.path.splitext(args.destfile)[0] + ".gpx"
        points_gpx.to_file(
            dst_gpx,
            driver = "GPX",
            layer = "waypoints",
            **{"GPX_USE_EXTENSIONS": "YES"}
            )

    print(f"Output written to {dst}.")