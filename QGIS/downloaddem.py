from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum, QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber, QgsApplication, QgsAuthMethodConfig
    )
import os
import requests

class GetDEMFromOpenTopography(QgsProcessingAlgorithm):

    def initAlgorithm(self, config = None):
        self.dem_options = [
            "SRTMGL3", "SRTMGL1", "SRTMGL1_E", "AW3D30", "AW3D30_E", "SRTM15Plus",
            "NASADEM", "COP30", "COP90", "EU_DTM", "GEDI_L3", "GEBCOIceTopo",
            "GEBCOSubIceTopo", "CA_MRDEM_DSM", "CA_MRDEM_DTM"
        ]

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                "POLYGON",
                "Input polygon",
                [QgsProcessing.TypeVectorPolygon]
            )
        )
        self.addParameter(
            QgsProcessingParameterEnum(
                "DEM_TYPE",
                "DEM type",
                options = self.dem_options,
                defaultValue = self.dem_options.index("AW3D30")
            )
        )
        self.addParameter(
            QgsProcessingParameterNumber(
                "BUFFER",
                "Buffer (°)",
                type = QgsProcessingParameterNumber.Double,
                defaultValue = 0.01
            )
        )
        self.addParameter(
            QgsProcessingParameterFileDestination(
                "OUTPUT",
                "Output DEM",
                fileFilter = "GeoTIFF (*.tif)"
            )
        )

    def processAlgorithm(self, parameters, context, feedback):
        auth_manager = QgsApplication.authManager()
        available_configs = auth_manager.availableAuthMethodConfigs()
        auth_id = "opentopography"
        for cfg_id, cfg in available_configs.items():
            if cfg.name() == auth_id:
                auth_id = cfg_id
                break
        if not auth_id:
            raise Exception(
            f"Authentication config with name '{auth_name_to_find}' not found." +
            " Set an API key under that name in Settings > Options > Authentication."
            )
        mconfig = QgsAuthMethodConfig()
        result = QgsApplication.authManager().loadAuthenticationConfig(
            authcfg = auth_id,
            mconfig = mconfig,
            full = True
            )
        
        if isinstance(result, tuple):
            success, mconfig = result
            if not success:
                raise Exception(f"Failed to load auth config {auth_id}")
        else:
            # Some QGIS versions just return None
            success = True
        
        apikey = mconfig.config("key") 
        
        polygon = self.parameterAsSource(parameters, "POLYGON", context)
        dem_type = self.dem_options[self.parameterAsEnum(parameters, "DEM_TYPE", context)]
        buffer_deg = self.parameterAsDouble(parameters, "BUFFER", context)
        output_file = self.parameterAsFileOutput(parameters, "OUTPUT", context)

        extent = polygon.sourceExtent()
        west  = extent.xMinimum() - buffer_deg
        east  = extent.xMaximum() + buffer_deg
        south = extent.yMinimum() - buffer_deg
        north = extent.yMaximum() + buffer_deg

        url = (
            f"https://portal.opentopography.org/API/globaldem?"
            f"demtype={dem_type}&south={south}&north={north}"
            f"&west={west}&east={east}&outputFormat=GTiff&API_Key={apikey}"
        )

        feedback.pushInfo(f"Requesting DEM: {url}")
        response = requests.get(url, headers = {"accept": "*/*"})
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "application/json" in content_type:
            try:
                data = response.json()
            except ValueError:
                feedback.pushInfo(f"Response is not valid JSON:\n{response.text}")
                raise Exception("API returned invalid JSON")
            download_url = data.get("result", {}).get("URL")
            if not download_url:
                feedback.pushInfo(f"API response:\n{data}")
                raise Exception("No download URL found in JSON response")
            
            feedback.pushInfo(f"Downloading from URL: {download_url}")
            r = requests.get(download_url, stream = True)
            r.raise_for_status()
            content_stream = r
        else:
            # Response is the file itself
            feedback.pushInfo("Response contains the DEM file directly")
            content_stream = response

        # Write the file
        with open(output_file, "wb") as f:
            for chunk in content_stream.iter_content(chunk_size = 8192):
                f.write(chunk)
        feedback.pushInfo("Download complete.")
        return {"OUTPUT": output_file}

    def name(self):
        return "get_dem_from_opentopography"

    def displayName(self):
        return "Get DEM from OpenTopography"

    def group(self):
        return "Fieldwork Tools"

    def groupId(self):
        return "fieldworktools"

    def createInstance(self):
        return GetDEMFromOpenTopography()