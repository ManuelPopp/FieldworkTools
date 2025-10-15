"""
Model exported as python.
Name : Create Sampling Plot
Group : Fieldwork Tools
With QGIS : 33802
"""

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterFile
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterDefinition
import processing


class CreateSamplingPlot(QgsProcessingAlgorithm):

    def initAlgorithm(self, config=None):
        param = QgsProcessingParameterPoint('angle_coordinate', 'Angle Coordinate', optional=True, defaultValue=None)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterPoint('centre_coordinate2', 'Centre Coordinate', defaultValue=None))
        self.addParameter(QgsProcessingParameterRasterLayer('dsm', 'DSM', defaultValue=None))
        param = QgsProcessingParameterNumber('height', 'Height', optional=True, type=QgsProcessingParameterNumber.Double, minValue=1, maxValue=6000, defaultValue=100)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)
        self.addParameter(QgsProcessingParameterFile('output_folder', 'Output Folder', behavior=QgsProcessingParameterFile.Folder, fileFilter='All files (*.*)', defaultValue=None))
        self.addParameter(QgsProcessingParameterString('plot_name', 'Plot Name', multiLine=False, defaultValue=None))
        param = QgsProcessingParameterNumber('width', 'Width', optional=True, type=QgsProcessingParameterNumber.Double, minValue=1, maxValue=6000, defaultValue=100)
        param.setFlags(param.flags() | QgsProcessingParameterDefinition.FlagAdvanced)
        self.addParameter(param)

    def processAlgorithm(self, parameters, context, model_feedback):
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(3, model_feedback)
        results = {}
        outputs = {}

        # String concatenation
        alg_params = {
            'INPUT_1': parameters['plot_name'],
            'INPUT_2': '_L2'
        }
        outputs['StringConcatenation'] = processing.run('native:stringconcatenation', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(1)
        if feedback.isCanceled():
            return {}

        # Matrice 400 Flightplan
        alg_params = {
            'ALTITUDE': 90,
            'ALTTYPE': 1,  # AGL: DSM follow
            'ANGLE': None,
            'BUFFER': None,
            'CALIBIMU': True,
            'DSM': parameters['dsm'],
            'FILENAME': outputs['StringConcatenation']['CONCATENATION'],
            'FLAP': None,
            'FLIGHTSPEED': None,
            'GRIDMODE': 2,  # Double grid
            'GSD': None,
            'HEIGHT': parameters['height'],
            'IMUCALTIME': None,
            'LATLON': parameters['centre_coordinate2'],
            'LATLON2': parameters['angle_coordinate'],
            'NSAMPLE': None,
            'OUTPUT': parameters['output_folder'],
            'SCANMODE': False,
            'SENSOR': 1,  # Zenmuse L2
            'SLAP': None,
            'SPACING': 20,
            'TOSECUREALT': None,
            'WIDTH': parameters['width'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Matrice400Flightplan'] = processing.run('script:create_plotplan', alg_params, context=context, feedback=feedback, is_child_algorithm=True)

        feedback.setCurrentStep(2)
        if feedback.isCanceled():
            return {}

        # Mavic 3M Flightplan
        alg_params = {
            'ALTITUDE': 90,
            'ALTTYPE': 1,  # AGL: DSM follow
            'ANGLE': None,
            'BUFFER': None,
            'CALIBIMU': False,
            'DSM': parameters['dsm'],
            'FILENAME': parameters['plot_name'],
            'FLAP': None,
            'FLIGHTSPEED': None,
            'GRIDMODE': 0,  # Lines
            'GSD': None,
            'HEIGHT': parameters['height'],
            'IMUCALTIME': None,
            'LATLON': parameters['centre_coordinate2'],
            'LATLON2': parameters['angle_coordinate'],
            'NSAMPLE': None,
            'OUTPUT': parameters['output_folder'],
            'SCANMODE': False,
            'SENSOR': 0,  # Mavic M3M
            'SLAP': None,
            'SPACING': None,
            'TOSECUREALT': None,
            'WIDTH': parameters['width'],
            'OUTPUT': QgsProcessing.TEMPORARY_OUTPUT
        }
        outputs['Mavic3mFlightplan'] = processing.run('script:create_plotplan', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        return results

    def name(self):
        return 'Create Full Sampling Plot'

    def displayName(self):
        return 'Create Full Sampling Plot'

    def group(self):
        return 'Fieldwork Tools'

    def groupId(self):
        return 'fieldworktools'

    def createInstance(self):
        return CreateSamplingPlot()
