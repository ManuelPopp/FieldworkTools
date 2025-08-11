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
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from pyproj import Geod
from warnings import warn

from lib.functions import *
from lib.io import write_template_kml
from lib.validation import validate_args

class Mission():
    def __init__(self, args):
        self.args = args
        ## Convert overlaps to percentages
        self.args.side_overlap = int(args.sideoverlap * 100)
        self.args.front_overlap = int(args.frontoverlap * 100)

        ## Validate input arguments
        self.validate_args()

        ## Initiate waypoint list
        self.waypoints = []
    
    def validate_args(self):
        self.args = validate_args(self.args)
    
    def set_plot(self):
        df = pd.DataFrame({
            "ID": [1],
            "Latitude": [self.args.latitude],
            "Longitude": [self.args.longitude]
            })
        
        gdf = gpd.GeoDataFrame(
            df,
            geometry = gpd.points_from_xy(df.Longitude, df.Latitude),
            crs = "EPSG:4326"
            )
        
        ## Transform coordinates to UTM
        self.local_crs = gdf.estimate_utm_crs()
        gdf_utm = gdf.to_crs(self.local_crs)
        y_centre = gdf_utm.get_coordinates().y[0]
        x_centre = gdf_utm.get_coordinates().x[0]
        left = x_centre - (self.args.width / 2)
        right = x_centre + (self.args.width / 2)
        top = y_centre + (self.args.height / 2)
        bottom = y_centre - (self.args.height / 2)

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
        if self.args.plotangle != 90:
            plot_gdf_utm = rotate_gdf(
                gdf = plot_gdf_utm,
                x_centre = x_centre, y_centre = y_centre,
                angle = self.args.plotangle - 90
                )
        # Set mission attributes
        self.x_centre = x_centre
        self.y_centre = y_centre
        self.plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
        self.plot_gdf_utm = plot_gdf_utm
        self.plot_coordinates = self.plot_gdf.get_coordinates()
    
    def write_template_kml(self):
        if not hasattr(self, "plot_coordinates"):
            raise ValueError("Plot coordinates not set. Call set_plot() first.")
        
        write_template_kml(
            horizontalfov = self.args.horizontalfov,
            secondary_hfov = self.args.secondary_hfov,
            altitude = self.args.altitude,
            spacing = self.args.spacing,
            overlapsensor = self.args.overlapsensor,
            side_overlap = self.args.side_overlap,
            front_overlap = self.args.front_overlap,
            template_directory = self.args.template_directory,
            plot_coordinates = self.plot_coordinates,
            flightspeed = self.args.flightspeed,
            imgsamplingmode = self.args.imgsamplingmode,
            transitionspeed = self.args.transitionspeed,
            altitude = self.args.altitude,
            tosecurealt = self.args.tosecurealt,
            buffer = self.args.buffer,
            plotangle = self.args.plotangle,
            lidar_returns = self.args.lidar_returns,
            sampling_rate = self.args.sampling_rate,
            scanning_mode = self.args.scanning_mode,
            calibrateimu = self.args.calibrateimu,
            destfile = self.args.destfile
            )