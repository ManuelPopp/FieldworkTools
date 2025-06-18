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
plot = "Uttigen_01"
image_path = os.path.join(
    "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/Valais/img",
    "DJI_20250617112457_0001_Z.JPG"
)
image = H20Image(image_path)
image.target_location

import os, shutil, folium
dir_src = os.path.join(
    "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/Valais/img",
    plot
    )
dir_dst = os.path.join(
    "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/org/fieldwork/Valais/img",
    plot,
    "Images"
)

if not os.path.exists(dir_dst):
    os.makedirs(dir_dst)

if not os.path.exists(os.path.join(dir_dst, "files")):
    os.makedirs(os.path.join(dir_dst, "files"))

for file in os.listdir(dir_src):
    if file.endswith(".JPG"):
        src_file = os.path.join(dir_src, file)
        dst_file = os.path.join(dir_dst, "files", file)
        shutil.copy(src_file, dst_file)
        print(f"Copied {src_file} to {dst_file}")

points = []
for file in os.listdir(os.path.join(dir_dst, "files")):
    if file.endswith("_Z.JPG"):
        image = H20Image(os.path.join(dir_dst, "files", file))
        location = image.target_location
        points.append(
            {
                "name": file,
                "lon": location[0],
                "lat": location[1],
                "alt": location[2],
                "ctime": image.ctime.isoformat(),
                "image": "files/" + file
            }
        )

meanlat = np.mean([pt["lat"] for pt in points])
meanlon = np.mean([pt["lon"] for pt in points])

m = folium.Map(location = [meanlat, meanlon], zoom_start = 50)

for pt in points:
    html = f"""
    <b>{pt['name']}</b><br>
    Elevation: {pt['alt']} m<br>
    <img src='{pt['image']}' style='width:1024px; height:auto;'/>
    """
    folium.Marker(
        location = [pt["lat"], pt["lon"]],
        popup = folium.Popup(
            html
            ),
    ).add_to(m)

os.chdir(dir_dst)
m.save("image_map.html")
