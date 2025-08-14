import os
import time
import zipfile
import numpy as np
from config import keydict
from lib.utils import get_overlaps

def write_template_kml(
        horizontalfov,
        secondary_hfov,
        spacing,
        overlapsensor,
        side_overlap,
        front_overlap,
        plot_coordinates,
        flightspeed,
        imgsamplingmode,
        transitionspeed,
        altitude,
        tosecurealt,
        buffer,
        plotangle,
        lidar_returns,
        sampling_rate,
        scanning_mode,
        calibrateimu,
        template_kml_directory,
        destfile
        ):
    lsolaph, lsolapw, colaph, colapw = get_overlaps(
        horizontalfov, secondary_hfov, altitude, spacing,
        overlapsensor, side_overlap, front_overlap
        )
    
    with open(
        os.path.join(template_kml_directory, "template.kml"), "r"
        ) as file:
        template_text = file.read()
        template = template_text.format(
            TIMESTAMP = int(time.time() * 1000),
            X0 = np.round(plot_coordinates.x[0], 13),
            X1 = np.round(plot_coordinates.x[1], 13),
            X2 = np.round(plot_coordinates.x[2], 13),
            X3 = np.round(plot_coordinates.x[3], 13),
            Y0 = np.round(plot_coordinates.y[0], 13),
            Y1 = np.round(plot_coordinates.y[1], 13),
            Y2 = np.round(plot_coordinates.y[2], 13),
            Y3 = np.round(plot_coordinates.y[3], 13),
            AUTOFLIGHTSPEED = flightspeed,
            IMGSPLMODE = "time" if imgsamplingmode == "time" else "distance",
            TRANSITIONSPEED = transitionspeed,
            EXECALTITUDE = altitude,
            ALTITUDE = altitude,
            TOSECUREHEIGHT = tosecurealt,
            MARGIN = buffer,
            ANGLE = plotangle,
            LIDARRETURNS = keydict["lidar_returns"][lidar_returns],
            SAMPLINGRATE = sampling_rate,
            SCANNINGMODE = scanning_mode,
            LHOVERLAP = lsolaph,
            LWOVERLAP = lsolapw,
            CHOVERLAP = colaph,
            CWOVERLAP = colapw,
            IMUCALIBARATION = int(calibrateimu)
            )
    
    with zipfile.ZipFile(destfile, "a") as zf:
        with zf.open("wpmz/template.kml", "w") as f:
            f.write(template.encode("utf8"))

def write_wayline_wpml(
        template_directory,
        waypoint_template,
        waypoints,
        wpturnmode,
        total_distance,
        total_time,
        flightspeed,
        transitionspeed,
        altitude_mode,
        tosecurealt,
        destfile
        ):
    placemarks = []
    action_group_index = 0
    action_index = 0

    for index, wpt in enumerate(waypoints):
        out_xml = wpt.to_xml(
            template_file = waypoint_template,
            action_group_id = action_group_index,
            action_id_start_index = action_index,
            index = index
            )
        
        if wpt.has_actiongroup:
            action_group_index += wpt.num_action_groups
        
        placemarks.append(out_xml)
    
    with open(
        os.path.join(template_directory, "waylines.wpml"), "r"
        ) as file:
        waylines_text = file.read()
        waylines = waylines_text.format(
            TOSECUREHEIGHT = tosecurealt,
            TRANSITIONSPEED = transitionspeed,
            ALTITUDEMODE = altitude_mode,
            TOTALDIST = total_distance,
            TOTALTIME = total_time,
            AUTOFLIGHTSPEED = flightspeed,
            PLACEMARKS = "\n".join(placemarks)
            )
    
    with zipfile.ZipFile(destfile, "a") as zf:
        with zf.open("wpmz/waylines.wpml", "w") as f:
            f.write(waylines.encode("utf8"))