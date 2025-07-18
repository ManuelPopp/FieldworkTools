import os
import platform
from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterPoint, 
    QgsProcessingParameterString, QgsProcessingParameterNumber,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterDefinition,
    QgsCoordinateTransform, QgsCoordinateReferenceSystem
    )

import subprocess

script_dir = "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/git/FieldworkTools/flightplanner"
script_name = "create_area_flight.py"
defaultname = "SamplingPlot"

# Functions
def get_unique_filename(folder, base = defaultname, ext = ".kmz"):
    i = 1
    filename = f"{base}{ext}"
    while os.path.exists(os.path.join(folder, filename)):
        filename = f"{base}_{i}{ext}"
        i += 1
    return filename

# Classes
class CreateFlightplan(QgsProcessingAlgorithm):
    LATLON = "LATLON"
    OUTPUT = "OUTPUT"
    FILENAME = "FILENAME"
    
    def initAlgorithm(self, config = None):
        self.addParameter(
            QgsProcessingParameterPoint(
                self.LATLON,
                "Location (click on map or enter lat/lon)",
                defaultValue = None
            )
        )
        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT,
                "Output folder"
            )
        )
        self.addParameter(
            QgsProcessingParameterString(
                self.FILENAME,
                "Output filename (optional – auto-generated if empty)",
                defaultValue = "",
                optional = True
            )
        )
        
        # Advanced parameters
        self.GSD = "GSD"
        self.SENSORFACTOR = "SENSORFACTOR"
        self.ALTITUDE = "ALTITUDE"
        self.WIDTH = "WIDTH"
        self.HEIGHT = "HEIGHT"
        self.SLAP = "SLAP"
        self.SPACING = "SPACING"
        self.BUFFER = "BUFFER"
        self.FOV = "FOV"
        self.FLIGHTSPEED = "FLIGHTSPEED"

        gsd_param = QgsProcessingParameterNumber(
            self.GSD,
            "Ground sampling distance in cm (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        gsd_param.setFlags(gsd_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        sfact_param = QgsProcessingParameterNumber(
            self.SENSORFACTOR,
            "Sensor factor (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        sfact_param.setFlags(sfact_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        alt_param = QgsProcessingParameterNumber(
            self.ALTITUDE,
            "Terrain follow altitude (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        alt_param.setFlags(alt_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        width_param = QgsProcessingParameterNumber(
            self.WIDTH,
            "Image width (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        width_param.setFlags(width_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        height_param = QgsProcessingParameterNumber(
            self.HEIGHT,
            "Image height (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        height_param.setFlags(height_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        slap_param = QgsProcessingParameterNumber(
            self.SLAP,
            "Side overlap fraction (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        slap_param.setFlags(slap_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        sping_param = QgsProcessingParameterNumber(
            self.SPACING,
            "Route spacing in m (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        sping_param.setFlags(sping_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        buff_param = QgsProcessingParameterNumber(
            self.BUFFER,
            "Buffer (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        buff_param.setFlags(buff_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        fov_param = QgsProcessingParameterNumber(
            self.FOV,
            "Field of view in degrees (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        fov_param.setFlags(fov_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        speed_param = QgsProcessingParameterNumber(
            self.FLIGHTSPEED,
            "Flight speed in m/s (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        speed_param.setFlags(speed_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        
        self.addParameter(gsd_param)
        self.addParameter(sfact_param)
        self.addParameter(alt_param)
        self.addParameter(width_param)
        self.addParameter(height_param)
        self.addParameter(slap_param)
        self.addParameter(sping_param)
        self.addParameter(buff_param)
        self.addParameter(fov_param)
        self.addParameter(speed_param)
    
    def processAlgorithm(self, parameters, context, feedback):
        point = self.parameterAsPoint(parameters, self.LATLON, context)
        source_crs = context.project().crs()
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(source_crs, target_crs, context.transformContext())
        point_wgs84 = transform.transform(point)

        lat = point_wgs84.y()
        lon = point_wgs84.x()
        
        out_dir = self.parameterAsString(parameters, self.OUTPUT, context)
        filename_input = self.parameterAsString(parameters, self.FILENAME, context)
        
        # Advanced parameters
        gsd = self.parameterAsDouble(parameters, self.GSD, context)
        sfact = self.parameterAsDouble(parameters, self.SENSORFACTOR, context)
        alt = self.parameterAsDouble(parameters, self.ALTITUDE, context)
        width = self.parameterAsDouble(parameters, self.WIDTH, context)
        height = self.parameterAsDouble(parameters, self.HEIGHT, context)
        slap = self.parameterAsDouble(parameters, self.SLAP, context)
        sping = self.parameterAsDouble(parameters, self.SPACING, context)
        buff = self.parameterAsDouble(parameters, self.BUFFER, context)
        fov = self.parameterAsDouble(parameters, self.FOV, context)
        speed = self.parameterAsDouble(parameters, self.FLIGHTSPEED, context)
        
        # If user kept default, adjust dynamically
        if not filename_input:
            filename_input = get_unique_filename(out_dir)
        
        full_output_path = os.path.join(out_dir, filename_input)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(full_output_path), exist_ok = True)
        
        # Generate command
        cmd = [
            "python", script_name, 
            "-lat", str(lat), 
            "-lon", str(lon), 
            "-dst", full_output_path
            ]
        
        # Check advanced parameters
        if parameters[self.GSD] is not None:
            cmd.extend(["-gsd", str(gsd)])
        if parameters[self.SENSORFACTOR] is not None:
            cmd.extend(["-sf", str(sfact)])
        if parameters[self.ALTITUDE] is not None:
            cmd.extend(["-alt", str(alt)])
        if parameters[self.WIDTH] is not None:
            cmd.extend(["-dx", str(width)])
        if parameters[self.HEIGHT] is not None:
            cmd.extend(["-dy", str(height)])
        if parameters[self.SLAP] is not None:
            cmd.extend(["-slap", str(slap)])
        if parameters[self.SPACING] is not None:
            cmd.extend(["-sp", str(alt)])
        if parameters[self.BUFFER] is not None:
            cmd.extend(["-buff", str(alt)])
        if parameters[self.FOV] is not None:
            cmd.extend(["-fov", str(alt)])
        if parameters[self.FLIGHTSPEED] is not None:
            cmd.extend(["-v", str(alt)])

        feedback.pushInfo(f"Running command: {' '.join(cmd)}")

        try:
            result = subprocess.run(
            cmd,
            cwd = script_dir,
            check = True,
            capture_output = True,
            text = True
            )
            feedback.pushInfo(result.stdout)
            if result.stderr:
                feedback.reportError(result.stderr)
        except subprocess.CalledProcessError as e:
            feedback.reportError(f"Command failed: {e.stderr}")
            raise e
        
        if platform.system() == "Windows":
            try:
                os.startfile(out_dir)
            except Exception as e:
                feedback.reportError(f"Could not open output folder: {e}")
        
        return {}

    def name(self):
        return "create_flightplan"

    def displayName(self):
        return "Create Flightplan"

    def group(self):
        return "Fieldwork Tools"

    def groupId(self):
        return "fieldworktools"

    def createInstance(self):
        return CreateFlightplan()