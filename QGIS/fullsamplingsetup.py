"""
Combined processing algorithm to create sampling plots for both
DJI Mavic 3M and DJI Matrice 400.
Name : Create Sampling Plot
Group : Fieldwork Tools
"""

from anyio import Path
from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFolderDestination
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterDefinition
import processing
from pathlib import Path

class CreateSamplingPlot(QgsProcessingAlgorithm):
    def initAlgorithm(self, config = None):
        param = QgsProcessingParameterPoint(
            "angle_coordinate", "Angle Coordinate",
            optional = True, defaultValue = None
            )
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterPoint(
                "centre_coordinate2", "Centre Coordinate", defaultValue = None
                )
            )
        self.addParameter(
            QgsProcessingParameterRasterLayer(
                "dtm", "DTM", optional = True, defaultValue = None
                )
            )
        param = QgsProcessingParameterNumber(
            "height", "Height",
            optional = True, type = QgsProcessingParameterNumber.Double,
            minValue = 1, maxValue = 6000, defaultValue = 100
            )
        param.setFlags(
            param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        self.addParameter(param)
        self.addParameter(
            QgsProcessingParameterFolderDestination("OUTPUT", "Output folder")
            )
        self.addParameter(
            QgsProcessingParameterString(
                "plot_name", "Plot Name", multiLine = False, defaultValue = None
                )
            )
        param = QgsProcessingParameterNumber(
            "width", "Width", optional = True,
            type = QgsProcessingParameterNumber.Double,
            minValue = 1, maxValue = 6000, defaultValue = 100
            )
        param.setFlags(
            param.flags() | QgsProcessingParameterDefinition.FlagAdvanced
            )
        self.addParameter(param)

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # String concatenation
        alg_params = {
            "INPUT_1": parameters["plot_name"],
            "INPUT_2": "_L2"
        }
        outputs["StringConcatenation"] = processing.run(
            "native:stringconcatenation",
            alg_params,
            context = context,
            feedback = feedback,
            is_child_algorithm = True
            )

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Matrice 400 Flightplan
        alg_params = {
            "ALTITUDE": 85,
            "ALTTYPE": 0 if parameters["dtm"] is None else 1,  # AGL: RTF=0, DTM follow=1
            "ANGLE": None,
            "BUFFER": None,
            "CALIBIMU": True,
            "DTM": parameters["dtm"].source() if hasattr(
                parameters["dtm"], "source"
                ) else parameters["dtm"],
            "FILENAME": outputs["StringConcatenation"]["CONCATENATION"],
            "FLAP": None,
            "FLIGHTSPEED": None,
            "GRIDMODE": 2,  # Double grid
            "GSD": None,
            "HEIGHT": parameters["height"],
            "IMUCALTIME": None,
            "LATLON": parameters["centre_coordinate2"],
            "LATLON2": parameters["angle_coordinate"],
            "NSAMPLE": None,
            "OUTPUT": parameters["OUTPUT"],
            "SCANMODE": False,
            "SENSOR": 1,  # Zenmuse L2
            "SLAP": None,
            "SPACING": 20,
            "TOSECUREALT": None,
            "WIDTH": parameters["width"]
        }
        outputs["Matrice400Flightplan"] = processing.run(
            "script:create_plotplan",
            alg_params,
            context = context,
            feedback = feedback,
            is_child_algorithm = False
            )

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Mavic 3M Flightplan
        # Spacing at 85 m AGL DEM follow and 85 % side overlap is 15.5 m
        alg_params = {
            "ALTITUDE": 85,
            "ALTTYPE": 0 if parameters["dtm"] is None else 1,  # AGL: RTF=0, DTM follow=1
            "ANGLE": None,
            "BUFFER": None,
            "CALIBIMU": False,
            "DTM": parameters["dtm"].source() if hasattr(
                parameters["dtm"], "source"
                ) else parameters["dtm"],
            "FILENAME": parameters["plot_name"],
            "FLAP": None,
            "FLIGHTSPEED": None,
            "GRIDMODE": 0,  # Lines
            "GSD": None,
            "HEIGHT": parameters["height"],
            "IMUCALTIME": None,
            "LATLON": parameters["centre_coordinate2"],
            "LATLON2": parameters["angle_coordinate"],
            "NSAMPLE": None,
            "OUTPUT": parameters["OUTPUT"],
            "SCANMODE": False,
            "SENSOR": 0,  # Mavic M3M
            "SLAP": None,
            "SPACING": None,
            "TOSECUREALT": None,
            "WIDTH": parameters["width"]
        }
        outputs["Mavic3mFlightplan"] = processing.run(
            "script:create_plotplan",
            alg_params,
            context = context,
            feedback = feedback,
            is_child_algorithm = False
            )
        
        # Remove and rename files
        out_name = str(parameters["plot_name"])
        out_dir = Path(parameters["OUTPUT"])

        m3mkmz = next(out_dir.glob(out_name + ".kmz"), None)
        if m3mkmz and m3mkmz.exists():
            m3mkmz.rename(m3mkmz.with_name(out_name + "_M3M.kmz"))
        else:
            feedback.pushInfo("WARNING: No Mavic 3M KMZ file found.")
        
        # Remove duplicate files from L2 output
        for f in out_dir.glob("*_L2.kml"):
            f.unlink()
        for f in out_dir.glob("*_L2.gpx"):
            f.unlink()
        
        for report in out_dir.glob("*_report.txt"):
            if "_L2" not in report.stem:
                report.rename(report.with_name(report.stem + "_M3M.txt"))
        
        return results

    def name(self):
        return "Create Full Sampling Plot"

    def displayName(self):
        return "Create Full Sampling Plot"

    def group(self):
        return "Fieldwork Tools"

    def groupId(self):
        return "fieldworktools"

    def createInstance(self):
        return CreateSamplingPlot()
