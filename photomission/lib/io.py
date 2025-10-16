import os
import time
import zipfile
import numpy as np
from lib.utils import get_overlaps

def write_template_kml(
        template_kml_directory,
        destfile
        ):
    with open(
        os.path.join(template_kml_directory, "template.kml"), "r"
        ) as file:
        template_text = file.read()
    
    with zipfile.ZipFile(destfile, "a") as zf:
        with zf.open("wpmz/template.kml", "w") as f:
            f.write(template_text.encode("utf8"))

def write_wayline_wpml(
        template_directory,
        waypoint_template,
        waypoints,
        flightspeed,
        transitionspeed,
        altitude_mode,
        destfile
        ):
    placemarks = []

    for index, wpt in enumerate(waypoints):
        out_xml = wpt.to_xml(
            template_file = waypoint_template,
            index = index
            )
        
        placemarks.append(out_xml)
    
    with open(
        os.path.join(template_directory, "waylines.template"), "r"
        ) as file:
        waylines_text = file.read()
        waylines = waylines_text.format(
            ALTITUDEMODE = altitude_mode,
            AUTOSPEED = transitionspeed,
            GLOBALSPEED = flightspeed,
            PLACEMARKS = "\n".join(placemarks)
            )
    
    with zipfile.ZipFile(destfile, "a") as zf:
        with zf.open("wpmz/waylines.wpml", "w") as f:
            f.write(waylines.encode("utf8"))

def copy_dsm(src, dst, rel_path = "wpmz/res/dsm"):
    if not os.path.exists(src):
        raise FileNotFoundError(f"Source DSM file not found: {src}")
    os.makedirs(os.path.dirname(dst), exist_ok = True)
    with zipfile.ZipFile(dst, "a") as zf:
        arcname = os.path.join(rel_path, os.path.basename(src))
        zf.write(src, arcname = arcname)