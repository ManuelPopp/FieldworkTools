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

# Debug
if False:
    import sys
    sys.argv = [
        "create_area_flight.py", "l2",
        "--latitude", "47.362158", "--longitude", "8.4562517",
        "--width", "50", "--height", "50",
        "--destfile", "C:/Users/poppman/Desktop/tmp/linetestL2.kmz",
        "--plotangle", "60",
        "--altitude", "60",
        "--gridmode", "double",
        "--calibrateimu",
        "--altitudetype", "rtf",
        "--dsm_path", "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/2025_06_WSL/dem/swissalti3d_Rameren_lonlat.tif",
        "--dsm_follow_segment_length", "10"
        ]
    import os
    os.chdir("D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/git/FieldworkTools/flightplanner")

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
from lib.utils import get_heading_angle

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
    help = "Flight altitude. Defaults calculated based on sensorfactor and GSD."
    )
parser.add_argument(
    "--altitudetype", "-altt", type = str, default = defaults.altitudetype,
    help = "Flight altitude type. Either 'rtf' (realtime follow), " +
        "'constant' (constant altitude), or a DSM (above DSM)." +
        f"Defaults to {defaults.altitudetype}."
    )
parser.add_argument(
    "--dsm_path", "-dsm", type = str,
    help = "Path to the DSM file (required when altitude type is 'dsm')."
    )
parser.add_argument(
    "--dsm_follow_segment_length", "-dsmseg", type = float,
    default = defaults.dsm_follow_segment_length,
    help = "Maximum segment length for DSM follow in m. " +
        f"Defaults to {defaults.dsm_follow_segment_length}."
    )
parser.add_argument(
    "--safetybuffer", "-sb", type = float, default = defaults.safetybuffer,
    help = "Horizontal safety buffer for DSM follow in m. " +\
        f"Defaults to {defaults.safetybuffer}."
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
    "--calibrateimu", "-cimu", action = "store_true",
    help = f"LiDAR sensor IMU calibration."
    )
parser.add_argument(
    "--imucalibrationinterval", "-imudt", type = float,
    default = defaults.imucalibrationinterval,
    help = "LiDAR sensor IMU calibration interval. " +
        f"Defaults to {defaults.imucalibrationinterval}."
    )
parser.add_argument(
    "--gridmode", "-gm", type = str, default = defaults.gridmode,
    help = "Flight pattern type (lines: 'lines', grid: 'simple'," +
    f" or double grid: 'double'). Defaults to {defaults.gridmode}"
)
parser.add_argument(
    "--template_directory", type = str,
    default = defaults.template_directory,
    help = argparse.SUPPRESS
    )

args = parser.parse_args()

# Body------------------------------------------------------------------
if __name__ == "__main__":
    ## Create dataframe
    mission = Mission(args)

    ## Create mission
    mission.make_waypoints()
    mission.add_actions()
    if mission.args.calibrateimu:
        mission.add_imu_calibration_groups()
    if mission.args.altitudetype == "dsm":
        mission.waypoint_altitudes_from_dsm()
    mission.plot()

    ## Export mission to KMZ
    mission.export_mission()