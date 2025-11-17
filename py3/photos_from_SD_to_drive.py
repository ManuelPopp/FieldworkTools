import os
import shutil
import json
import subprocess
import numpy as np
import pandas as pd
import geopandas as gpd
from dateutil import parser

class Image():
    def __init__(self, image_path):
        self.set_path(image_path)
    
    @property
    def full_metadata(self):
        return self.get_exif_data()
    
    @property
    def target_location(self):
        targetlon = self.targetlon
        targetlat = self.targetlat
        targetalt = self.targetalt
        
        if targetlon is None or targetlat is None or targetalt is None:
            raise ValueError("Incomplete metadata.")
        
        return (targetlon, targetlat, targetalt)
    
    def set_path(self, image_path):
        self.image_path = image_path
        self.set_attributes()
    
    def set_attributes(self):
        metadata = self.full_metadata
    
    def _dms_to_decimal(self, dms_str):
        parts = dms_str.strip().split(" ")
        degrees = float(parts[0])
        minutes = float(parts[2].replace("'", ""))
        seconds = float(parts[3].replace('"', ""))
        direction = parts[4]
        
        decimal = degrees + minutes / 60 + seconds / 3600
        if direction in ["S", "W"]:
            decimal *= -1
        
        return decimal
    
    def get_exif_data(self):
        result = subprocess.run(
            ["exiftool", "-j", self.image_path],
            stdout = subprocess.PIPE,
            stderr = subprocess.PIPE,
            text = True
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)
        
        data = json.loads(result.stdout)
        return data[0]

class M4ProImage(Image):
    def __init__(self, image_path):
        Image.__init__(self, image_path)
    
    def set_attributes(self):
        metadata = self.full_metadata
        shortened = {
            "ctime" : parser.parse(metadata.get("CreateDate")),
            "gpslat" : self._dms_to_decimal(metadata.get("GPSLatitude")),
            "gpslon" : self._dms_to_decimal(metadata.get("GPSLongitude"))
        }
        self.__dict__.update(shortened)

class H30Image(Image):
    def __init__(self, image_path):
        Image.__init__(self, image_path)
    
    def set_attributes(self):
        metadata = self.full_metadata
        
        shortened = {
            "ctime" : parser.parse(metadata.get("CreateDate")),
            "gpspos" : metadata.get("GPSPosition"),
            "gpslat" : self._dms_to_decimal(metadata.get("GPSLatitude")),
            "gpslon" : self._dms_to_decimal(metadata.get("GPSLongitude")),
            "absalt" : np.float64(metadata.get("AbsoluteAltitude")),
            "gbdeg" : np.float64(
                np.array(metadata.get("GimbalDegree").split(","))
                ),
            "gbroll" : np.float64(metadata.get("GimbalRollDegree")),
            "gbyaw" : np.float64(metadata.get("GimbalYawDegree")),
            "gbpitch" : np.float64(metadata.get("GimbalPitchDegree")),
            "uavdeg" : np.float64(
                np.array(metadata.get("FlightDegree").split(","))
                ),
            "uavroll" : np.float64(metadata.get("FlightRollDegree")),
            "uavyaw" : np.float64(metadata.get("FlightYawDegree")),
            "uavpitch" : np.float64(metadata.get("FlightPitchDegree")),
            "targetdist" : np.float64(metadata.get("LRFTargetDistance")),
            "targetlon" : np.float64(metadata.get("LRFTargetLon")),
            "targetlat" : np.float64(metadata.get("LRFTargetLat")),
            "targetalt" : np.float64(metadata.get("LRFTargetAlt"))
        }
        self.__dict__.update(shortened)

# Get plot boundaries
fw_dir = os.path.join("D:", "FIELDWORK")
plots = gpd.GeoDataFrame()
for plot in os.listdir(fw_dir):
    bbox_file = os.path.join(fw_dir, plot, f"{plot}_boundary.gpkg")
    if os.path.isfile(bbox_file):
        bbox = gpd.read_file(bbox_file)
        bbox.insert(0, "ID", [plot])
        plots = gpd.GeoDataFrame(pd.concat([plots, bbox], ignore_index = True))

        if not os.path.exists(os.path.join(fw_dir, plot, "TOCPhotos")):
            os.makedirs(os.path.join(fw_dir, plot, "TOCPhotos"), exist_ok = True)

sd_dir = os.path.join("E:", "DCIM")
for path, n, filenames in os.walk(sd_dir):
    if isinstance(path, str):
        for filename in filenames:
            file = os.path.join(path, filename)
            if os.path.splitext(file)[1].lower() == ".jpg":
                print(f"File: {file}")
                try:
                    img = H30Image(file)
                    location = (img.targetlon, img.targetlat)
                except:
                    img = M4ProImage(file)
                    location = (img.gpslon, img.gpslat)
                point_gdf = gpd.GeoDataFrame(
                    pd.DataFrame({"Row": [0]}),
                    geometry = gpd.points_from_xy([location[0]], [location[1]]),
                    crs = "EPSG:4326"
                    )
                joined = point_gdf.sjoin(plots)
                if joined.shape[0] > 0:
                    plot = joined["ID"].iloc[0]
                    if not os.path.exists(os.path.join(fw_dir, plot, "TOCPhotos", filename)):
                        print(f"Copying {filename} from {plot}")
                        shutil.copyfile(file, os.path.join(fw_dir, plot, "TOCPhotos", filename))
                    else:
                        print("Exists in dst.")