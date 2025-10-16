#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Manuel"
__date__ = "Wed Oct 15 17:20:06 2025"
__credits__ = ["Manuel R. Popp"]
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
from warnings import warn

from config import Defaults
from mission import Mission
from lib.utils import get_heading_angle

# Inputs----------------------------------------------------------------
## Parse input arguments
defaults = Defaults()
parser = argparse.ArgumentParser()
parser.add_argument(
    "--slot", "-slt", type = int, default = defaults.slot,
    help = "Mission slot index."
    )
parser.add_argument(
    "--flightaltitude", "-flalt", type = float,
    default = defaults.flightaltitude,
    help = "Flight altitude between photo locations."
    )
parser.add_argument(
    "--minimum_flightaltitude", "-mflalt", type = float,
    default = defaults.minimum_flightaltitude,
    help = "Minimum flight altitude between photo locations (relative to DSM)."
    )
parser.add_argument(
    "--photoaltitude", "-phalt", type = float,
    default = defaults.photoaltitude,
    help = "Photo altitude."
    )
parser.add_argument(
    "--dsm_path", "-dsm", type = str,
    help = "Path to the DSM file."
    )
parser.add_argument(
    "--poi_path", "-poi", type = str,
    help = "Path to the point location file."
    )
parser.add_argument(
    "--takeoff_latitude", "-tolat", type = float,
    default = None,
    help = "Latitude of the takeoff location."
    )
parser.add_argument(
    "--takeoff_longitude", "-tolon", type = float,
    default = None,
    help = "Longitude of the takeoff location."
    )
parser.add_argument(
    "--out_dir", "-out", type = str,
    help = "Path to the output directory."
    )
parser.add_argument(
    "--safetybuffer", "-sb", type = float, default = defaults.safetybuffer,
    help = "Horizontal safety buffer for DSM follow in m. " +\
        f"Defaults to {defaults.safetybuffer}."
    )
parser.add_argument(
    "--transitionspeed", "-ts", type = float,
    default = defaults.transitionspeed,
    help = "UAV transition speed in m/s. " +
        f"Defaults to {defaults.transitionspeed}."
    )

args = parser.parse_args()

# Body------------------------------------------------------------------
if __name__ == "__main__":
    ## Create mission object
    mission = Mission(args)
    
    ## Add waypoints and actions
    mission.make_waypoints()

    ## Export mission to KMZ
    mission.export_mission()