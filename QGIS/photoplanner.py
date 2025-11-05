from qgis.core import (
    QgsProcessing,
    QgsProcessingAlgorithm,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterVectorLayer,
    QgsProcessingParameterPoint,
    QgsProcessingParameterNumber,
    QgsProcessingParameterFolderDestination
)
import subprocess
import os
import sys

script_dir = "D:/onedrive/OneDrive - Eidg. Forschungsanstalt WSL/switchdrive/PhD/git/FieldworkTools/photomission"
script_path = os.path.join(script_dir, "photomission.py")

class PhotoMissionAlgorithm(QgsProcessingAlgorithm):
    DSM = "DSM"
    POI = "POI"
    COORD = "COORD"
    SLOT = "SLOT"
    ALT = "ALT"
    OUTPUT = "OUTPUT"

    def initAlgorithm(self, config = None):
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.DSM,
                "Digital Surface Model (DSM) [EPSG:4326]"
            )
        )

        self.addParameter(
            QgsProcessingParameterVectorLayer(
                self.POI,
                "Points of Interest (POI) [EPSG:4326]",
                [QgsProcessing.TypeVectorPoint]
            )
        )

        self.addParameter(
            QgsProcessingParameterPoint(
                self.COORD,
                "Takeoff coordinate (lon, lat) [EPSG:4326]"
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.SLOT,
                "Slot number (mission must exist on controller)",
                type = QgsProcessingParameterNumber.Integer,
                defaultValue = 0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ALT,
                "Flight altitude in meter",
                type = QgsProcessingParameterNumber.Double,
                defaultValue = 50.0
            )
        )

        self.addParameter(
            QgsProcessingParameterFolderDestination(
                self.OUTPUT,
                "Output directory"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        dsm_layer = self.parameterAsRasterLayer(parameters, self.DSM, context)
        poi_layer = self.parameterAsVectorLayer(parameters, self.POI, context)
        coord = self.parameterAsPoint(parameters, self.COORD, context)
        slot = self.parameterAsInt(parameters, self.SLOT, context)
        altitude = self.parameterAsDouble(parameters, self.ALT, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        cmd = [
            "python", script_path,
            "--slot", str(slot),
            "-dsm", dsm_layer.source(),
            "--poi_path", poi_layer.source().split("|")[0],
            "-out", output,
            "-tolat", str(coord.y()),
            "-tolon", str(coord.x()),
            "--flightaltitude", str(altitude)
        ]

        feedback.pushInfo("Running command: " + " ".join(cmd))

        process = subprocess.run(
            cmd,
            cwd = script_dir,
            capture_output = True,
            text = True
            )

        feedback.pushInfo("Output:\n" + process.stdout)
        if process.stderr:
            feedback.reportError(process.stderr)

        if process.returncode != 0:
            raise Exception("photomission.py failed. See log above.")

        return {self.OUTPUT: output}

    def name(self):
        return "photomission_planner"

    def displayName(self):
        return "Create Photo Mission"

    def group(self):
        return "Fieldwork Tools"

    def groupId(self):
        return "fieldworktools"

    def createInstance(self):
        return PhotoMissionAlgorithm()