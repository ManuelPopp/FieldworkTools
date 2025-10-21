from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (
    QgsProcessing, QgsProcessingAlgorithm, QgsProcessingParameterFeatureSource,
    QgsProcessingParameterEnum, QgsProcessingParameterFileDestination,
    QgsProcessingParameterNumber, QgsApplication, QgsAuthMethodConfig,
    QgsRasterLayer, QgsCoordinateReferenceSystem
    )
from qgis import processing
import os
import time
import math
import tempfile
import requests
import zipfile

def get_aster_dem(west, south, east, north, output_file, user, password):
    appeears_api = "https://appeears.earthdatacloud.nasa.gov/api/"
    response = requests.post(
        "https://appeears.earthdatacloud.nasa.gov/api/login",
        auth = (user, password)
    )
    token_info = response.json()
    del user, password
    headers = {
        "Authorization": "Bearer {0}".format(token_info["token"]),
        "Content-Type": "application/json"
        }

    task_payload = {
    "params": {
        "geo": {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                [west, south],
                [west, north],
                [east, north],
                [east, south],
                [west, south]
                ]
            ]
            },
            "properties": {}
        }]
        },
        "dates": [{
        "endDate": "09-30-2018",
        "startDate": "05-01-2017",
        "recurring": False,
        "yearRange": [2000, 2050]
        }],
        "layers": [{
        "layer": "ASTER_GDEM_DEM",
        "product": "ASTGTM_NC.003"
        }],
        "output": {
        "format": {
            "type": "geotiff"
        },
        "projection": "native"
        }
    },
    "task_name": "Area Example",
    "task_type": "area"
    }

    response = requests.post(
        appeears_api + "task", headers = headers, json = task_payload
        )
    task_id = response.json()["task_id"]

    while True:
        status_response = requests.get(
            f"{appeears_api}task/{task_id}", headers = headers
            )
        status = status_response.json()['status']
        print("Task status:", status)
        if status in ["done", "failed"]:
            break
        time.sleep(30)

    if status == "done":
        url = f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}"
        out_name = "C:/Users/poppman/Desktop/tmp/RamerenM3M/test.tif"
        r = requests.get(
            url, headers = {"Authorization": f"Bearer {token_info['token']}"}
            )
        files = r.json()["files"]

        for f in files:
            filename = f["file_name"]
            
            if "ASTGTM_NC.003" in filename:
                file_id = f["file_id"]
                file_url = f"https://appeears.earthdatacloud.nasa.gov/api/bundle/{task_id}/{file_id}"

                response = requests.get(
                    file_url,
                    headers = {
                        "Authorization": "Bearer {0}".format(token_info["token"])
                        },
                    allow_redirects = True,
                    stream = True
                )
                with open(output_file, "wb") as fd:
                    for chunk in response.iter_content(chunk_size = 8192):
                        fd.write(chunk)
                print(f"Downloaded {out_name}")

class GetDEMFromOpenTopography(QgsProcessingAlgorithm):
    def initAlgorithm(self, config = None):
        self.dem_options = [
            "SRTMGL3", "SRTMGL1", "SRTMGL1_E", "AW3D30", "AW3D30_E", "SRTM15Plus",
            "NASADEM", "COP30", "COP90", "EU_DTM", "GEDI_L3", "GEBCOIceTopo",
            "GEBCOSubIceTopo", "CA_MRDEM_DSM", "CA_MRDEM_DTM", "ASTGTM_V003"
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
                defaultValue = self.dem_options.index("ASTGTM_V003")
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
        polygon = self.parameterAsSource(parameters, "POLYGON", context)
        dem_type = self.dem_options[
            self.parameterAsEnum(parameters, "DEM_TYPE", context)
            ]
        buffer_deg = self.parameterAsDouble(parameters, "BUFFER", context)
        output_file = self.parameterAsFileOutput(parameters, "OUTPUT", context)
        
        extent = polygon.sourceExtent()
        west = extent.xMinimum() - buffer_deg
        east = extent.xMaximum() + buffer_deg
        south = extent.yMinimum() - buffer_deg
        north = extent.yMaximum() + buffer_deg
        
        auth_manager = QgsApplication.authManager()
        available_configs = auth_manager.availableAuthMethodConfigs()
        auth_id = "nasa" if dem_type == "ASTGTM_V003" else "opentopography"
        
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
        
        # ASTER GDEM download
        if dem_type == "ASTGTM_V003":
            user = mconfig.config("username")
            password = mconfig.config("password")
            if user is None or password is None:
                raise Exception(
                    "Username or password for NASA Earthdata not set in " +
                    "Authentication config 'nasa'."
                )
            get_aster_dem(west, south, east, north, output_file, user, password)
            feedback.pushInfo("Download complete.")
            return {"OUTPUT": output_file}
        
        apikey = mconfig.config("key")
        
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