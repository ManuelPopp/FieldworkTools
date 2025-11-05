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
import shutil
import json
from qgis.PyQt.QtCore import QProcess
from qgis.core import (
    QgsProcessingAlgorithm, QgsProcessingParameterPoint,
    QgsProcessingParameterFileDestination,
    QgsProcessingParameterString, QgsProcessingParameterNumber,
    QgsProcessingParameterFile, QgsProcessingParameterVectorLayer,
    QgsProcessingParameterFolderDestination, QgsProcessingParameterDefinition,
    QgsCoordinateTransform, QgsCoordinateReferenceSystem,
    QgsGeometry, QgsDistanceArea, QgsBearingUtils,
    Qgis, QgsMessageLog
    )
from qgis.PyQt.QtWidgets import QFileDialog

import subprocess

script_dir = "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/git/FieldworkTools/R"
script_name = "crop_las.R"
kwargs = {}
if platform.system() == "Windows":
    kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

# Store a settings file with the Rscript.exe path
try:
    TOOLBOX_DIR = os.path.dirname(__file__)
except NameError:
    TOOLBOX_DIR = os.getcwd()

CONFIG_FILE = os.path.join(TOOLBOX_DIR, "rscript_config.json")

def get_rscript_path(feedback = None):
    # 1. Try system PATH
    rscript_exe = shutil.which("Rscript")
    if rscript_exe:
        return rscript_exe
    
    # 2. Try saved config in script folder
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding = "utf-8") as f:
                cfg = json.load(f)
                if os.path.exists(cfg.get("rscript_path", "")):
                    return cfg["rscript_path"]
        except json.JSONDecodeError:
            if feedback:
                feedback.reportError("Config file is corrupted. Recreating it.")
            os.remove(CONFIG_FILE)
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding = "utf-8") as f:
            cfg = json.load(f)
            if os.path.exists(cfg.get("rscript_path", "")):
                return cfg["rscript_path"]
    
    # 3. Ask user interactively (QFileDialog)
    if feedback:
        feedback.pushInfo(
            "Rscript not found. Please select the Rscript executable manually."
            )
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.ExistingFile)
    dialog.setNameFilter("Rscript (Rscript.exe)")
    if dialog.exec_():
        rscript_exe = dialog.selectedFiles()[0]
        # Save permanently next to toolbox
        with open(CONFIG_FILE, "w", encoding = "utf-8") as f:
            json.dump({"rscript_path": rscript_exe}, f)
        return rscript_exe
    
    return None

##CropPointCloud----------------------------------------------------------------
class CropPointCloud(QgsProcessingAlgorithm):
    VECTOR = "VECTOR"
    POINTCLOUD = "POINTCLOUD"
    OUTPUT = "OUTPUT"
    
    def initAlgorithm(self, config = None):
        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.VECTOR, "Bounding box/vector file"
                )
        )
        self.addParameter(
            QgsProcessingParameterFile(self.POINTCLOUD, "Point cloud file")
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                "OUTPUT",
                "Output LAS file",
                fileFilter = "LAS files (*.las)"
            )
        )
    
    def processAlgorithm(self, parameters, context, feedback):
        vector_layer = self.parameterAsVectorLayer(
            parameters, self.VECTOR, context
            )
        vector_path = vector_layer.source().split("|")[0] \
            if vector_layer is not None else None
        las_path = self.parameterAsFile(parameters, self.POINTCLOUD, context)
        
        output_path = self.parameterAsFile(parameters, self.OUTPUT, context)
        
        # Path to your R script
        if not os.path.exists(os.path.join(script_dir, script_name)):
            feedback.reportError(f"R script not found: {script_dir}")
            return {}
        
        # Rscript executable
        rscript_exe = get_rscript_path(feedback)
        
        cmd = [rscript_exe, script_name, las_path, vector_path, output_path]
        feedback.pushInfo(f"Running R script:\n{' '.join(cmd)}")
        
        try:
            result = subprocess.run(
            cmd,
            cwd = script_dir,
            check = True,
            capture_output = True,
            text = True,
            **kwargs
            )
            feedback.pushInfo(result.stdout)
            if result.stderr:
                feedback.reportError(result.stderr)
        except subprocess.CalledProcessError as e:
            feedback.reportError(f"Command failed: {e.stderr}")
            raise e

        # Open output folder
        out_dir = os.path.dirname(output_path)
        if platform.system() == "Windows":
            os.startfile(out_dir)
        elif platform.system() == "Linux":
            subprocess.run(["xdg-open", out_dir])

        feedback.pushInfo(f"Cropped point cloud saved to {output_path}")
        return {}

    def name(self):
        return "crop_pointcloud"

    def displayName(self):
        return "Crop Point Cloud"

    def group(self):
        return "Point Cloud Tools"

    def groupId(self):
        return "pointcloud_tools"

    def createInstance(self):
        return CropPointCloud()