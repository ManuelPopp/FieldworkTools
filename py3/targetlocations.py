import subprocess
import json
import numpy as np
from dateutil import parser

class H20Image():
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

# Example usage
image_path = "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/Valais/img/Fladerich_01/DJI_20250617112457_0001_Z.JPG"
image = H20Image(image_path)
image.target_location
