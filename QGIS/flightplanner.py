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
    QgsProcessingParameterString, QgsProcessingParameterNumber,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterDefinition,
    QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsGeometry, QgsDistanceArea, QgsBearingUtils,
    Qgis, QgsMessageLog
    )

import subprocess

script_dir = "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/git/FieldworkTools/flightplanner"
script_name = "create_area_flight.py"
defaultname = "SamplingPlot"
sensor_options = ["m3m", "l2"]

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
                "Output filename (optional – auto-generated if empty)",
                defaultValue = "",
                optional = True
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                self.SENSOR,
                "Sensor model",
                options = sensor_options,
                defaultValue = "m3m"
            )
        )
        
        # Advanced parameters
        self.GSD = "GSD"
        self.SENSORFACTOR = "SENSORFACTOR"
        self.ALTITUDE = "ALTITUDE"
        self.TOSECUREALT = "TOSECUREALT"
        self.WIDTH = "WIDTH"
        self.HEIGHT = "HEIGHT"
        self.ANGLE = "ANGLE"
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
        gsd_param.setFlags(
            gsd_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        sfact_param = QgsProcessingParameterNumber(
            self.SENSORFACTOR,
            "Sensor factor (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        sfact_param.setFlags(
            sfact_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        alt_param = QgsProcessingParameterNumber(
            self.ALTITUDE,
            "Terrain follow altitude (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        alt_param.setFlags(
            alt_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        toalt_param = QgsProcessingParameterNumber(
            self.TOSECUREALT,
            "Secure take-off altitude (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        toalt_param.setFlags(
            toalt_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        width_param = QgsProcessingParameterNumber(
            self.WIDTH,
            "Plot width in m (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        width_param.setFlags(
            width_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        height_param = QgsProcessingParameterNumber(
            self.HEIGHT,
            "Plot height in m (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        height_param.setFlags(
            height_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        angle_param = QgsProcessingParameterNumber(
            self.ANGLE,
            "Rotation angle in degrees (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
            )
        angle_param.setFlags(
            angle_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        slap_param = QgsProcessingParameterNumber(
            self.SLAP,
            "Side overlap fraction (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        slap_param.setFlags(
            slap_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        sping_param = QgsProcessingParameterNumber(
            self.SPACING,
            "Route spacing in m (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        sping_param.setFlags(
            sping_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        buff_param = QgsProcessingParameterNumber(
            self.BUFFER,
            "Buffer (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        buff_param.setFlags(
            buff_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        fov_param = QgsProcessingParameterNumber(
            self.FOV,
            "Field of view in degrees (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        fov_param.setFlags(
            fov_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        speed_param = QgsProcessingParameterNumber(
            self.FLIGHTSPEED,
            "Flight speed in m/s (optional, advanced)",
            type = QgsProcessingParameterNumber.Double,
            optional = True
        )
        speed_param.setFlags(
            speed_param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        
        self.addParameter(gsd_param)
        self.addParameter(sfact_param)
        self.addParameter(alt_param)
        self.addParameter(toalt_param)
        self.addParameter(width_param)
        self.addParameter(height_param)
        self.addParameter(angle_param)
        self.addParameter(slap_param)
        self.addParameter(sping_param)
        self.addParameter(buff_param)
        self.addParameter(fov_param)
        self.addParameter(speed_param)
    
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
        sfact = self.parameterAsDouble(parameters, self.SENSORFACTOR, context)
        alt = self.parameterAsDouble(parameters, self.ALTITUDE, context)
        toalt = self.parameterAsDouble(parameters, self.TOSECUREALT, context)
        width = parameters[self.WIDTH] if self.WIDTH in parameters else None
        height = parameters[self.HEIGHT] if self.HEIGHT in parameters else None
        angle_deg = parameters[self.ANGLE] if self.ANGLE in parameters else None
        slap = self.parameterAsDouble(parameters, self.SLAP, context)
        sping = self.parameterAsDouble(parameters, self.SPACING, context)
        buff = self.parameterAsDouble(parameters, self.BUFFER, context)
        fov = self.parameterAsDouble(parameters, self.FOV, context)
        speed = self.parameterAsDouble(parameters, self.FLIGHTSPEED, context)
        
        # Compute centre point and plot width (if two points provided)
        if point2 is not None and not point2.isEmpty():
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
        sensor = sensor_options[sensor_index]
        
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
            "-dst", full_output_path
            ]
        
        # Check advanced parameters
        if parameters[self.GSD] is not None:
            cmd.extend(["-gsd", str(gsd)])
        if parameters[self.SENSORFACTOR] is not None:
            cmd.extend(["-sf", str(sfact)])
        if parameters[self.ALTITUDE] is not None:
            cmd.extend(["-alt", str(alt)])
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
            cmd.extend(["-sp", str(sping)])
        if parameters[self.BUFFER] is not None:
            cmd.extend(["-buff", str(buff)])
        if parameters[self.FOV] is not None:
            cmd.extend(["-fov", str(fov)])
        if parameters[self.FLIGHTSPEED] is not None:
            cmd.extend(["-v", str(speed)])

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