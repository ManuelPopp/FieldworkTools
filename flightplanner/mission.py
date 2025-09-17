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
import copy
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from warnings import warn
import matplotlib as mpl
from matplotlib import pyplot as plt

from lib.utils import get_heading_angle, photo_trigger_intervals
from lib.io import write_template_kml, write_wayline_wpml, copy_dsm
from lib.validation import validate_args
from lib.waypoints import Waypoint
from lib.grid import simple_grid, double_grid, rotate_gdf
from lib.geo import (
    waypoint_distance, segment_duration, waypoint_altitude, segment_altitude
)
from lib.insert import interpolate_waypoints
from lib.actiongroups import (
    StartNadirMSMapping, StopNadirMSMapping,
    PrepareObliqueMSMapping,
    StartObliqueMSMapping, StopObliqueMSMapping,
    StartRecordPointCloud, StopRecordPointCloud,
    StartLiDARMapping,
    PrepareObliqueLiDARMapping,
    StartObliqueLiDARMapping, StopObliqueLiDARMapping
    )

from config import Config

config = Config()

class Mission():
    def __init__(self, args):
        self.args = args
        ## Convert overlaps to percentages
        self.args.side_overlap = int(args.sideoverlap * 100)
        self.args.front_overlap = int(args.frontoverlap * 100)

        ## Validate input arguments
        self.validate_args()

        ## Set plot extent
        self.set_plot()

        ## Initiate waypoint list
        self.waypoints = []

        # Relative DSM output directory
        self.dsm_out = None
    
    @property
    def template_kml_directory(self):
        dir_main = os.path.join("templates", self.args.sensor)
        if self.args.altitudetype.lower() == "rtf":
            return os.path.join(dir_main, "agl_rtf")
        if self.args.altitudetype.lower() == "dsm":
            return os.path.join(dir_main, "agl_dem")
        raise NotImplementedError(
            f"Altitude type '{self.args.altitudetype}' not implemented."
        )
    
    @property
    def distance(self):
        if self.waypoints == []:
            return 0
        return sum(
            waypoint_distance(self.waypoints[i], self.waypoints[i + 1])
                for i in range(len(self.waypoints) - 1)
                )
    
    @property
    def duration(self):
        if self.waypoints == []:
            return 0
        return sum(
            segment_duration(self.waypoints[i], self.waypoints[i + 1])
                for i in range(len(self.waypoints) - 1)
                )
    
    @property
    def altitude_mode(self):
        if self.args.altitudetype == "rtf":
            return "realTimeFollowSurface"
        if self.args.altitudetype == "constant":
            return "relativeToStartPoint"
        if self.args.altitudetype == "dsm":
            return "WGS84"
    
    @property
    def action_trigger_param(self):
        atp = photo_trigger_intervals(
            front_overlap = self.args.frontoverlap * 100,
            altitude = self.args.altitude,
            coefficient_0 = self.args.coefficients_atd[0],
            coefficient_1 = self.args.coefficients_atd[1]
        )
        return atp
    
    # Input validation--------------------------------------------------
    def validate_args(self):
        self.args = validate_args(self.args)
    
    # Plot properties---------------------------------------------------
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
        
        b = self.args.buffer
        plot_points_utm_buff = pd.DataFrame({
            "Latitude": [bottom - b, top + b, top + b, bottom - b],
            "Longitude": [left - b, left - b, right + b, right + b]
            })
        
        plot_gdf_utm = gpd.GeoDataFrame(
            plot_points_utm,
            geometry = gpd.points_from_xy(
                plot_points_utm.Longitude,
                plot_points_utm.Latitude
                ),
            crs = self.local_crs
            )
        
        plot_gdf_utm_buff = gpd.GeoDataFrame(
            plot_points_utm_buff,
            geometry = gpd.points_from_xy(
                plot_points_utm_buff.Longitude,
                plot_points_utm_buff.Latitude
                ),
            crs = self.local_crs
            )

        # Rotate plot if required
        if self.args.plotangle != 90:
            plot_gdf_utm = rotate_gdf(
                gdf = plot_gdf_utm,
                x_centre = x_centre, y_centre = y_centre,
                angle = self.args.plotangle - 90
                )
            plot_gdf_utm_buff = rotate_gdf(
                gdf = plot_gdf_utm_buff,
                x_centre = x_centre, y_centre = y_centre,
                angle = self.args.plotangle - 90
            )
        
        # Set mission attributes
        self.x_centre = x_centre
        self.y_centre = y_centre
        self.plot_gdf = plot_gdf_utm.to_crs("EPSG:4326")
        self.plot_gdf_utm = plot_gdf_utm
        self.plot_gdf_buff = plot_gdf_utm_buff.to_crs("EPSG:4326")
        self.plot_gdf_utm_buff = plot_gdf_utm_buff
        self.plot_coordinates = self.plot_gdf.get_coordinates()
        self._top = top
        self._bottom = bottom
        self._left = left
        self._right = right
    
    # Waypoints---------------------------------------------------------
    def add_waypoint(self, coordinates, altitude, velocity, **kwargs):
        waypoint = Waypoint(
            coordinates, altitude, velocity,
            mission = self,
            **kwargs
            )
        self.waypoints.append(waypoint)
    
    def _make_simple_grid(self):
        grid = simple_grid(
            top = self._top,
            bottom = self._bottom,
            left = self._left,
            right = self._right,
            x_centre = self.x_centre,
            y_centre = self.y_centre,
            local_crs = self.local_crs,
            spacing = self.args.spacing,
            buffer = self.args.buffer,
            plotangle = self.args.plotangle,
            gridmode = self.args.gridmode
        )
        from shapely.geometry import Point
        if grid.empty:
            raise ValueError(
                "No grid points were generated. " +
                "Check input geometry and parameters."
                )
        last_point = Point(grid.iloc[-1,].x, grid.iloc[-1,].y)
        corner_idx = self.plot_gdf_buff.distance(last_point).idxmin()
        x, y = self.plot_gdf_buff.get_coordinates().iloc[corner_idx]
        grid = pd.concat(
            [
                grid,
                pd.DataFrame({
                    "x" : [x, self.args.longitude],
                    "y" : [y, self.args.latitude]
                    })
                ],
            ignore_index = True
            )
        grid[["velocity"]] = self.args.flightspeed
        grid[["altitude"]] = self.args.altitude

        self._waypoint_df = gpd.GeoDataFrame(
            data = grid[["altitude", "velocity"]],
            geometry = gpd.points_from_xy(grid.x, grid.y)
            )
    def _make_double_grid(self):
        grid = double_grid(
            top = self._top,
            bottom = self._bottom,
            left = self._left,
            right = self._right,
            x_centre = self.x_centre,
            y_centre = self.y_centre,
            local_crs = self.local_crs,
            spacing = self.args.spacing,
            buffer = self.args.buffer,
            plotangle = self.args.plotangle
        )
        if grid.empty:
            raise ValueError(
                "No grid points were generated. " +
                "Check input geometry and parameters."
                )
        last_point = Point(grid.iloc[-1,].x, grid.iloc[-1,].y)
        corner_idx = self.plot_gdf_buff.distance(last_point).idxmin()
        x, y = self.plot_gdf_buff.get_coordinates().iloc[corner_idx]
        grid = pd.concat(
            [
                grid,
                pd.DataFrame({
                    "x" : [x, self.args.longitude],
                    "y" : [y, self.args.latitude]
                    })
                ],
            ignore_index = True
            )
        grid[["velocity"]] = self.args.flightspeed
        grid[["altitude"]] = self.args.altitude

        self._waypoint_df = gpd.GeoDataFrame(
            data = grid[["altitude", "velocity"]],
            geometry = gpd.points_from_xy(grid.x, grid.y)
            )
    
    def _grid_to_waypoints(self):
        for _, row in self._waypoint_df.iterrows():
            self.add_waypoint(
                coordinates = (row.geometry.x, row.geometry.y),
                altitude = row.altitude,
                velocity = row.velocity
            )
    
    def add_actions(self):
        if len(self.waypoints) < 2:
            raise ValueError(
                "At least two waypoints are required to add actions." +
                f" Found {len(self.waypoints)}."
                )
        
        if self.args.sensor == "m3m":
            self._default_ms_mapping()
        elif self.args.sensor == "l2":
            self._default_lidar_mapping()

    def _default_ms_mapping(self):
        self.waypoints[0].add_action_group(
            StartNadirMSMapping,
            action_trigger_param = self.action_trigger_param
            )
        self.waypoints[-3].add_action_group(StopNadirMSMapping)
        self.waypoints[-2].add_action_group(PrepareObliqueMSMapping)
        self.waypoints[-2].add_action_group(
            StartObliqueMSMapping,
            action_trigger_param = self.action_trigger_param
            )
        self.waypoints[-1].add_action_group(StopObliqueMSMapping)
        for i in [0, -3, -2, -1]:
            self.waypoints[i].set_turning_mode(
                "toPointAndStopWithDiscontinuityCurvature"
                )
    
    def _default_lidar_mapping(self):
        self.waypoints[0].add_action_group(StartRecordPointCloud)
        self.waypoints[0].add_action_group(
            StartLiDARMapping,
            action_trigger_param = self.action_trigger_param
            )
        self.waypoints[-3].add_action_group(StopRecordPointCloud)
        self.waypoints[-2].add_action_group(PrepareObliqueLiDARMapping)
        self.waypoints[-2].add_action_group(
            StartObliqueLiDARMapping,
            action_trigger_param = self.action_trigger_param
            )
        self.waypoints[-2].add_action_group(StopObliqueLiDARMapping)
    
    def waypoint_altitudes_from_dsm(self):
        if self.args.altitudetype.lower() == "rtf":
            warn(
                "Altitude mode is set to RTF. " +
                "The UAV will use its terrain-following capabilities."
                )
            return
        
        if self.args.altitudetype.lower() == "constant":
            warn("Altitude mode is set to constant.")
            return
        
        if not os.path.isfile(self.args.dsm_path):
            raise ValueError("DSM file not found.")
        
        if len(self.waypoints) < 2:
            raise ValueError(
                "At least two waypoints are required to calculate " +
                f"altitudes. Found {len(self.waypoints)}."
                )
        # First, get altitude for existing waypoints
        for wpt in self.waypoints:
            altitude = waypoint_altitude(
                dsm_path = self.args.dsm_path,
                wpt = wpt,
                altitude_agl = self.args.altitude
            )
            wpt.set_altitude(altitude)
        # Split with existing altitude information assuming straight
        # transect lines
        self.split_waylines(
            by = "distance", dmax = self.args.dsm_follow_segment_length
            )
        # Get new altitudes based on smaller segments
        for wp0, wp1 in zip(self.waypoints[:-1], self.waypoints[1:]):
            altitude = segment_altitude(
                dsm_path = self.args.dsm_path,
                wpt0 = wp0, wpt1 = wp1,
                altitude_agl = self.args.altitude,
                horizontal_safety_buffer_m = self.args.safetybuffer
            )
            wp0.set_altitude(altitude)
    
    def add_heading_angles(self):
        if len(self.waypoints) < 2:
            raise ValueError(
                "At least two waypoints are required to calculate heading angles."
                )
        for wp0, wp1 in zip(self.waypoints[:-1], self.waypoints[1:]):
            theta = get_heading_angle(wp0, wp1)
            wp0.set_heading_angle(theta)

        wp1.set_heading_angle(0)

    def add_imu_calibration_groups(self):
        cumulative_time = self.args.imucalibrationinterval
        self.split_waylines(
            by = "time", tmax = self.args.imucalibrationinterval
            )
        
        new_waypoints = []
        for wp0, wp1 in zip(self.waypoints[:-1], self.waypoints[1:]):
            if cumulative_time >= self.args.imucalibrationinterval:
                wp0.add_calibration()
                cumulative_time = 0
            
            new_waypoints.append(wp0)
            cumulative_time += segment_duration(wp0, wp1)
        
        new_waypoints.append(wp1)
        self.waypoints = new_waypoints
    
    def make_waypoints(self):
        warn("Clearing existing waypoints.")
        self.waypoints.clear()

        if self.args.gridmode in ["lines", "simple"]:
            self._make_simple_grid()
        elif self.args.gridmode == "double":
            self._make_double_grid()
        self._grid_to_waypoints()
    
    # Insert waypoints--------------------------------------------------
    def split_waylines(
            self, by = "time", tmax = None, dmax = None, **kwargs
            ):
        if by not in ["time", "distance"]:
            raise ValueError(f"Invalid split method: {by}")
        
        new_waypoints = []
        for wp0, wp1 in zip(self.waypoints[:-1], self.waypoints[1:]):
            new_waypoints.append(wp0)
            if by == "time":
                dt = segment_duration(wp0, wp1)
                num_wpts = max(0, int(dt // tmax))
            if by == "distance":
                dx = waypoint_distance(wp0, wp1)
                num_wpts = max(0, int(dx // dmax))
            if num_wpts > 0:
                new_wpts = interpolate_waypoints(wp0, wp1, num_wpts)
                new_waypoints.extend(new_wpts)
        
        new_waypoints.append(wp1)
        self.waypoints.clear()
        self.waypoints = new_waypoints
    
    # Visualisation-----------------------------------------------------
    def plot(self):
        if not hasattr(self, "plot_coordinates"):
            raise ValueError(
                "Plot coordinates not set. Call set_plot() first."
            )
        data = [
            {
                "geometry": Point(wp.coordinates),
                "altitude": wp.altitude,
                "velocity": wp.velocity,
                "has_actiongroup": wp.has_actiongroup,
                "perform_imu_calibration": wp.perform_imu_calibration
            }
            for wp in self.waypoints
            ]
        gdf = gpd.GeoDataFrame(data, crs = "EPSG:4326")
        
        lines = []
        velocities = []
        for i in range(len(gdf) - 1):
            line = LineString([
                gdf.geometry.iloc[i], gdf.geometry.iloc[i + 1]
            ])
            lines.append(line)
            velocities.append(gdf.velocity.iloc[i])
        
        lines_gdf = gpd.GeoDataFrame(
            {"geometry": lines, "velocity": velocities}, crs = gdf.crs
            )
        
        coords = [(pt.x, pt.y) for pt in self.plot_gdf.geometry]
        polygon = Polygon(coords)
        polygon_gdf = gpd.GeoDataFrame(
            [1], geometry = [polygon], crs = gdf.crs
            )
        
        fig, ax = plt.subplots(figsize = (10, 8))
        polygon_gdf.plot(
            ax = ax,
            facecolor = "blue",
            edgecolor = "blue",
            alpha = 0.2
        )
        
        lines_gdf.plot(
            ax = ax,
            column = "velocity",
            cmap = "viridis",
            linewidth = 2
        )
        sm_vel = plt.cm.ScalarMappable(
            cmap = "viridis", norm = plt.Normalize(
                vmin = lines_gdf["velocity"].min(),
                vmax = lines_gdf["velocity"].max()
                )
            )
        sm_vel._A = []
        cbar_vel = fig.colorbar(
            sm_vel, ax = ax, shrink = 0.6, label = "Velocity"
            )

        # Altitude points with shared scale
        vmin = gdf["altitude"].min()
        vmax = gdf["altitude"].max()
        if not gdf[gdf.has_actiongroup].empty:
            gdf[gdf.has_actiongroup].plot(
                ax = ax, column = "altitude", cmap = "plasma",
                vmin = vmin, vmax = vmax, marker = "s", markersize = 50
            )
        if not gdf[~gdf.has_actiongroup].empty:
            gdf[~gdf.has_actiongroup].plot(
                ax = ax, column = "altitude", cmap = "plasma",
                vmin = vmin, vmax = vmax, marker = "o", markersize = 50
            )
        if not gdf[gdf.perform_imu_calibration].empty:
            gdf[gdf.perform_imu_calibration].plot(
                ax = ax,
                facecolors = "none", edgecolor = "red",
                vmin = vmin, vmax = vmax, marker = "o", markersize = 150
            )
        sm_alt = plt.cm.ScalarMappable(
            cmap = "plasma",
            norm = plt.Normalize(vmin = vmin, vmax = vmax)
            )
        sm_alt._A = []
        cbar_alt = fig.colorbar(
            sm_alt, ax = ax,
            shrink = 0.6, label = "Altitude", location = "right"
            )

        # Marker legend for Action Group / No Action Group
        markers = [
            mpl.lines.Line2D(
                [0], [0],
                marker = "s", color = "w", markerfacecolor = "gray",
                markersize = 8,
                label = "Action Group"
                ),
            mpl.lines.Line2D(
                [0], [0],
                marker = "o", color = "w", markerfacecolor = "gray",
                markersize = 8,
                label = "No Action Group"
                )
        ]
        ax.legend(
            handles = markers, title = "Actions",
            loc = "upper left", bbox_to_anchor = (0.5, -0.05),
            ncol = 2,
            borderaxespad = 0
            )
        plt.show()
    
    # IO----------------------------------------------------------------
    def export_mission(self):
        if not hasattr(self, "plot_coordinates"):
            raise ValueError(
                "Plot coordinates not set. Call set_plot() first."
                )
        self.add_heading_angles()
        
        # Generate DSM path and copy DSM if altitude type is DSM
        if self.args.altitudetype.lower() == "dsm":
            self.dsm_out = "/".join([
                "wpmz", "res", "dsm",
                os.path.basename(self.args.dsm_path)
                ])
            copy_dsm(
                src = self.args.dsm_path, dst = self.args.destfile,
                rel_path = self.dsm_out
                )
        
        # Write template.kml file
        write_template_kml(
            horizontalfov = self.args.horizontalfov,
            secondary_hfov = self.args.secondary_hfov,
            spacing = self.args.spacing,
            overlapsensor = self.args.overlapsensor,
            side_overlap = self.args.side_overlap,
            front_overlap = self.args.front_overlap,
            template_kml_directory = self.template_kml_directory,
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
            destfile = self.args.destfile,
            dsm_path = self.dsm_out
            )
        
        # Write wayline.wpml file
        write_wayline_wpml(
            template_directory = self.template_kml_directory,
            waypoint_template = config.waypoint_template,
            waypoints = self.waypoints,
            wpturnmode = self.args.wpturnmode,
            total_distance = self.distance,
            total_time = self.duration,
            flightspeed = self.args.flightspeed,
            transitionspeed = self.args.transitionspeed,
            tosecurealt = self.args.tosecurealt,
            destfile = self.args.destfile,
            altitude_mode = self.altitude_mode
            )
        print(f"Mission exported to {self.args.destfile}.")