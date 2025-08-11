import time
import zipfile
import numpy as np
from config import keydict
from lib.functions import get_overlaps

def write_template_kml(
        horizontalfov,
        secondary_hfov,
        altitude,
        spacing,
        overlapsensor,
        side_overlap,
        front_overlap,
        template_directory,
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
        destfile
        ):
    lsolaph, lsolapw, colaph, colapw = get_overlaps(
        horizontalfov, secondary_hfov, altitude, spacing,
        overlapsensor, side_overlap, front_overlap
        )

    with open(
        os.path.join(template_directory, "wpmz", "template.kml"), "r"
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