#!/usr/bin/env python3
# -*- coding: utf-8 -*-
__author__ = "Manuel"
__date__ = "Mon Jul 18 12:43:42 2025"
__credits__ = ["Manuel R. Popp"]
__license__ = "Unlicense"
__version__ = "1.0.1"
__maintainer__ = "Manuel R. Popp"
__email__ = "requests@cdpopp.de"
__status__ = "Development"

import os
import platform
from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterPoint,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterString, QgsProcessingParameterNumber,
    QgsProcessingParameterEnum, QgsProcessingParameterRasterLayer,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterDefinition,
    QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsGeometry, QgsDistanceArea, QgsBearingUtils,
    Qgis, QgsMessageLog
    )

import subprocess

script_dir = "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/git/FieldworkTools/flightplanner"
script_name = "create_area_flight.py"
defaultname = "SamplingPlot"

sensor_options = ["Mavic M3M", "Zenmuse L2"]
sensor_options_short = ["m3m", "l2"]

altitude_options = [
    "AGL: Real time terrain follow",
    "AGL: DSM follow",
    "Constant"
    ]
altitude_options_short = ["rtf", "dsm", "constant"]

grid_options = ["Lines", "Simple grid", "Double grid"]
grid_options_short = ["lines", "simple", "double"]

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
    LATLON2 = "LATLON2"
    OUTPUT = "OUTPUT"
    FILENAME = "FILENAME"
    SENSOR = "SENSOR"
    ALTTYPE = "ALTTYPE"
    GRIDMODE = "GRIDMODE"
    CALIBIMU = "CALIBIMU"
    
    def initAlgorithm(self, config = None):
        self.addParameter(
            QgsProcessingParameterPoint(
                self.LATLON,
                "Location (click on map or enter lat/lon)",
                defaultValue = None
            )
        )
        self.addParameter(
            QgsProcessingParameterPoint(
                self.LATLON2,
                "Additional location (click on map or enter lat/lon)",
                defaultValue = "",
                optional = True
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
                "Output filename (auto-generated if empty)",
                defaultValue = "",
                optional = True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.SENSOR,
                "Sensor model",
                options = sensor_options,
                defaultValue = sensor_options[0]
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.ALTTYPE,
                "Altitude type",
                options = altitude_options,
                defaultValue = altitude_options[0]
            )
        )
        
        self.addParameter(
            QgsProcessingParameterEnum(
                self.GRIDMODE,
                "Flight pattern type",
                options = grid_options,
                defaultValue = grid_options[0]
            )
        )
        calibimu_param = QgsProcessingParameterBoolean(
            self.CALIBIMU,
            "Calibrate IMU",
            defaultValue = False
        )
        self.addParameter(calibimu_param)
        
        # Advanced parameters
        self.GSD = "GSD"
        self.ALTITUDE = "ALTITUDE"
        self.DSM = "DSM"
        self.TOSECUREALT = "TOSECUREALT"
        self.WIDTH = "WIDTH"
        self.HEIGHT = "HEIGHT"
        self.ANGLE = "ANGLE"
        self.SLAP = "SLAP"
        self.SPACING = "SPACING"
        self.BUFFER = "BUFFER"
        self.FLIGHTSPEED = "FLIGHTSPEED"
        self.IMUCALTIME = "IMUCALTIME"
        self.SCANMODE = "SCANMODE"

        gsd_param = QgsProcessingParameterNumber(
            self.GSD,
            "Ground sampling distance in cm",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        gsd_param.setFlags(
            gsd_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        alt_param = QgsProcessingParameterNumber(
            self.ALTITUDE,
            "Terrain follow altitude in m",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        alt_param.setFlags(
            alt_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        dsm_param = QgsProcessingParameterRasterLayer(
            self.DSM,
            "Raster file for DSM follow altitude",
            optional = True
        )
        dsm_param.setFlags(
            dsm_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        toalt_param = QgsProcessingParameterNumber(
            self.TOSECUREALT,
            "Secure take-off altitude in m",
            type = QgsProcessingParameterNumber.Integer,
            optional = True
        )
        toalt_param.setFlags(
            toalt_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        width_param = QgsProcessingParameterNumber(
            self.WIDTH,
            'Plot sidelength X ("width") in m',
            type = QgsProcessingParameterNumber.Integer,
            optional = True
        )
        width_param.setFlags(
            width_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        height_param = QgsProcessingParameterNumber(
            self.HEIGHT,
            'Plot sidelength Y ("height") in m',
            type = QgsProcessingParameterNumber.Integer,
            optional = True
        )
        height_param.setFlags(
            height_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        angle_param = QgsProcessingParameterNumber(
            self.ANGLE,
            "Rotation angle in degrees",
            type = QgsProcessingParameterNumber.Integer,
            optional = True
            )
        angle_param.setFlags(
            angle_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        slap_param = QgsProcessingParameterNumber(
            self.SLAP,
            "Side overlap fraction",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        slap_param.setFlags(
            slap_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        sping_param = QgsProcessingParameterNumber(
            self.SPACING,
            "Route spacing in m",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        sping_param.setFlags(
            sping_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        buff_param = QgsProcessingParameterNumber(
            self.BUFFER,
            "Plot buffer in m",
            type = QgsProcessingParameterNumber.Integer,
            optional = True
        )
        buff_param.setFlags(
            buff_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        speed_param = QgsProcessingParameterNumber(
            self.FLIGHTSPEED,
            "Flight speed in m/s",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        speed_param.setFlags(
            speed_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        imutime_param = QgsProcessingParameterNumber(
            self.IMUCALTIME,
            "Max flight time beteen IMU calibrations in s",
            type = QgsProcessingParameterNumber.Integer,
            optional = True
        )
        imutime_param.setFlags(
            imutime_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        scanmode_param = QgsProcessingParameterBoolean(
            self.SCANMODE,
            "Use repetitive LiDAR scanning mode",
            defaultValue = False
        )
        scanmode_param.setFlags(
            scanmode_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        self.addParameter(gsd_param)
        self.addParameter(alt_param)
        self.addParameter(dsm_param)
        self.addParameter(toalt_param)
        self.addParameter(width_param)
        self.addParameter(height_param)
        self.addParameter(angle_param)
        self.addParameter(slap_param)
        self.addParameter(sping_param)
        self.addParameter(buff_param)
        self.addParameter(speed_param)
        self.addParameter(imutime_param)
        self.addParameter(scanmode_param)
    
    def processAlgorithm(self, parameters, context, feedback):
        # Main parameters
        sensor = self.parameterAsString(parameters, self.SENSOR, context)
        point = self.parameterAsPoint(parameters, self.LATLON, context)
        point2 = self.parameterAsPoint(parameters, self.LATLON2, context)
        source_crs = context.project().crs()
        target_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(
            source_crs, target_crs, context.transformContext()
            )
        point_wgs84 = transform.transform(point)
        
        # Advanced parameters
        gsd = self.parameterAsDouble(parameters, self.GSD, context)
        alt = self.parameterAsDouble(parameters, self.ALTITUDE, context)
        dsm_layer = self.parameterAsRasterLayer(parameters, self.DSM, context)
        toalt = self.parameterAsDouble(parameters, self.TOSECUREALT, context)
        width = parameters[self.WIDTH] if self.WIDTH in parameters else None
        height = parameters[self.HEIGHT] if self.HEIGHT in parameters else None
        angle_deg = parameters[self.ANGLE] if self.ANGLE in parameters else None
        slap = self.parameterAsDouble(parameters, self.SLAP, context)
        sping = self.parameterAsDouble(parameters, self.SPACING, context)
        buff = self.parameterAsDouble(parameters, self.BUFFER, context)
        imutime = self.parameterAsInt(parameters, self.IMUCALTIME, context)
        speed = self.parameterAsDouble(parameters, self.FLIGHTSPEED, context)
        
        # Compute centre point and plot width (if two points provided)
        if (point2 is not None) and (not point2.isEmpty()):
            point2_wgs84 = transform.transform(point2)
            lat2 = point2_wgs84.y()
            lon2 = point2_wgs84.x()
            
            d = QgsDistanceArea()
            d.setEllipsoid("WGS84")
            line = QgsGeometry.fromPolylineXY([point_wgs84, point2_wgs84])
            mid = line.interpolate(line.length() / 2).asPoint()
            
            if width is None:
                width = d.measureLine(point_wgs84, point2_wgs84)
                feedback.pushInfo(f"Selected segment width: {width} m.")
            
            if angle_deg is None:
                angle_deg = d.bearing(
                    point_wgs84, point2_wgs84
                    ) * 180 / 3.141592653589793
                angle_deg = int(angle_deg)
                feedback.pushInfo(f"Computed plot angle {angle_deg}°.")
            else:
                feedback.pushInfo(f"User-set plot angle {angle_deg}°.")
            
            # Overwrite centre point
            point_wgs84 = mid
        
        lat = point_wgs84.y()
        lon = point_wgs84.x()
        
        # Set output directory
        out_dir = self.parameterAsString(parameters, self.OUTPUT, context)
        filename_input = self.parameterAsString(
            parameters, self.FILENAME, context
            )
        
        # Get sensor type
        sensor_index = self.parameterAsEnum(parameters, "SENSOR", context)
        sensor = sensor_options_short[sensor_index]
        
        # Get altitude type
        alttype_index = self.parameterAsEnum(parameters, "ALTTYPE", context)
        alttype = altitude_options_short[alttype_index]
        
        # Get grid type
        grid_index = self.parameterAsEnum(parameters, "GRIDMODE", context)
        gridmode = grid_options_short[grid_index]
        
        # If user kept default, adjust dynamically
        if not filename_input:
            filename_input = get_unique_filename(out_dir)
        
        full_output_path = os.path.join(out_dir, filename_input)
        
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(full_output_path), exist_ok = True)
        
        # Generate command
        cmd = [
            "python", script_name,
            sensor,
            "-lat", str(lat),
            "-lon", str(lon),
            "-dst", full_output_path,
            "-altt", alttype,
            "-gm", gridmode
            ]
        
        # Check advanced parameters
        if parameters[self.GSD] is not None:
            cmd.extend(["-gsd", str(gsd)])
        if parameters[self.ALTITUDE] is not None:
            cmd.extend(["-alt", str(alt)])
        if dsm_layer is not None and dsm_layer.isValid():
            dsm_path = dsm_layer.source()
            cmd.extend(["-dsm", dsm_path])
        if parameters[self.TOSECUREALT] is not None:
            cmd.extend(["-tsa", str(toalt)])
        if width is not None:
            cmd.extend(["-dx", str(width)])
        if height is not None:
            cmd.extend(["-dy", str(height)])
        if isinstance(angle_deg, (int, float)):
            cmd.extend(["-ra", str(angle_deg)])
        if parameters[self.SLAP] is not None:
            cmd.extend(["-slap", str(slap)])
        if parameters[self.SPACING] is not None:
            cmd.extend(["-ds", str(sping)])
        if parameters[self.BUFFER] is not None:
            cmd.extend(["-buff", str(buff)])
        if parameters[self.FLIGHTSPEED] is not None:
            cmd.extend(["-v", str(speed)])
        if parameters[self.IMUCALTIME] is not None:
            cmd.extend(["-imudt", str(imutime)])
        if self.parameterAsBool(parameters, self.SCANMODE, context):
            cmd.extend(["-sm", "repetitive"])
        if self.parameterAsBool(parameters, self.CALIBIMU, context):
            cmd.append("--calibrateimu")

        feedback.pushInfo(f"Running command: {' '.join(cmd)}\n")

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