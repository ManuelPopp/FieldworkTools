#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Manuel"
__date__ = "Mon Jul 18 10:34:06 2025"
__credits__ = ["Manuel R. Popp"]
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

from lib.utils import get_heading_angle
from lib.io import write_template_kml, write_wayline_wpml, copy_dsm
from lib.waypointgroups import Photogroup
from lib.waypoints import Waypoint
from lib.geo import (
    waypoint_distance, segment_duration, waypoint_altitude, segment_altitude
)

from config import Config

config = Config()

class Mission():
    def __init__(self, args):
        self.args = args
        self.mission_slot = list(config.slots.values())[args.slot]
        self.args.destfile = os.path.join(
            args.out_dir,
            self.mission_slot,
            f"{self.mission_slot}.kmz"
            )
        self.args.altitudetype = "relative"
        self.args.wpturnmode = "toPointAndPassWithContinuityCurvature"
        self.template_kml_directory = config.template_kml_directory
        self._takeoff_altitude = None
        self.num_photos = self.args.num_photos
        self.photo_radius = self.args.photo_radius

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
        if self.args.altitudetype == "relative":
            return "relativeToStartPoint"
        if self.args.altitudetype == "dsm":
            return "WGS84"
    
    @property
    def takeoff_altitude(self):
        if self.args.dsm_path == "fixed_altitude":
            return 0.0
        
        if self._takeoff_altitude is None:
            if self.args.takeoff_latitude is None \
                or self.args.takeoff_longitude is None:
                raise ValueError(
                    "Takeoff latitude and longitude must be provided."
                    )
            if not os.path.isfile(self.args.dsm_path):
                raise ValueError("DSM file not found.")
            takeoff_wpt = Waypoint(
                coordinates = (
                    self.args.takeoff_longitude, self.args.takeoff_latitude
                    ),
                altitude = None,
                velocity = 0,
                wp_type = "takeoff"
                )
            altitude = waypoint_altitude(
                dsm_path = self.args.dsm_path,
                wpt = takeoff_wpt,
                altitude_agl = 0.0
                )
            self._takeoff_altitude = altitude
        return self._takeoff_altitude

    # Waypoints---------------------------------------------------------
    def add_waypoint(self, coordinates, altitude, velocity, **kwargs):
        waypoint = Waypoint(
            coordinates, altitude, velocity,
            mission = self,
            **kwargs
            )
        self.waypoints.append(waypoint)
    
    def add_actions(self):
        if len(self.waypoints) < 2:
            raise ValueError(
                "At least two waypoints are required to add actions." +
                f" Found {len(self.waypoints)}."
                )
    
    def waypoint_altitudes_from_dsm(self):
        if not os.path.isfile(self.args.dsm_path):
            if self.args.dsm_path != "fixed_altitude":
                raise ValueError("DSM file not found.")
        
        if len(self.waypoints) < 2:
            raise ValueError(
                "At least two waypoints are required to calculate " +
                f"altitudes. Found {len(self.waypoints)}."
                )
        
        for wpt in self.waypoints:
            if wpt.wp_type == "fly":
                offset = max(
                    self.args.flightaltitude, self.args.minimum_flightaltitude
                    )
            elif wpt.wp_type == "photo":
                offset = self.args.photoaltitude
            elif wpt.wp_type == "takeoff":
                offset = 0.0
            else:
                raise ValueError(f"Unknown waypoint type: {wpt.wp_type}.")
            
            altitude = waypoint_altitude(
                dsm_path = self.args.dsm_path,
                wpt = wpt,
                altitude_agl = offset
            )
            wpt.set_altitude(altitude)
    
    def add_heading_angles(self):
        if len(self.waypoints) < 2:
            raise ValueError(
                "At least two waypoints are required to calculate heading angles."
                )
        for wp0, wp1 in zip(self.waypoints[:-1], self.waypoints[1:]):
            theta = get_heading_angle(wp0, wp1)
            wp0.set_heading_angle(theta)

        wp1.set_heading_angle(0)
    
    def make_waypoints(self):
        # Open input POI file and create waypoints from coordinates
        if not os.path.isfile(self.args.poi_path):
            raise ValueError("POI file not found.")
        poi_gdf = gpd.read_file(self.args.poi_path)
        if poi_gdf.crs is None:
            raise ValueError("POI file has no CRS defined.")
        if poi_gdf.crs.to_epsg() != 4326:
            poi_gdf = poi_gdf.to_crs(epsg = 4326)
        if not all(poi_gdf.geometry.type == "Point"):
            raise ValueError("POI file must contain only point geometries.")
        self.waypoints = [
            Waypoint(
                coordinates = (pt.x, pt.y),
                altitude = None,
                velocity = self.args.transitionspeed
                )
            for pt in poi_gdf.geometry
            ]
        
        # Add photo waypoints
        new_waypoints = []
        for wpt in self.waypoints:
            photogroup = Photogroup(
                wpt, num_photos = self.num_photos, radius = self.photo_radius
                )
            waypoints = photogroup.create_waypoint_group()
            new_waypoints.extend(waypoints)
        self.waypoints = new_waypoints
        # Set stable waypoint indices
        for i, wpt in enumerate(self.waypoints):
            wpt._index = i
        
        # Set waypoint altitudes based on DSM
        self.waypoint_altitudes_from_dsm()
    
    # IO----------------------------------------------------------------
    def export_mission(self):
        self.add_heading_angles()
        
        # Adjust waypoint altitudes for relative altitude mode
        print("Adjusting waypoint altitudes relative to takeoff altitude...")
        for wpt in self.waypoints:
            if not wpt.altitude_adjusted:
                relative_altitude = wpt.altitude - self.takeoff_altitude
                print(f"{relative_altitude=}")
                wpt.set_altitude(relative_altitude)
                wpt.altitude_adjusted = True
        
        # Ensure waypoint index
        for i, wpt in enumerate(self.waypoints):
            wpt._index = i
        
        # Set action start index
        start_index = 1
        for wpt in self.waypoints:
            wpt.action_start_index = start_index
            start_index += wpt.num_actions
        
        # Create parent directory if not existent
        os.makedirs(os.path.dirname(self.args.destfile), exist_ok = True)

        # Write template.kml file
        write_template_kml(
            destfile = self.args.destfile,
            template_kml_directory = self.template_kml_directory
            )
        
        # Write wayline.wpml file
        write_wayline_wpml(
            template_directory = self.template_kml_directory,
            waypoint_template = config.waypoint_template,
            waypoints = self.waypoints,
            flightspeed = self.args.transitionspeed,
            transitionspeed = self.args.transitionspeed,
            altitude_mode = self.altitude_mode,
            destfile = self.args.destfile
            )
        print(f"Mission exported to {self.args.destfile}.")