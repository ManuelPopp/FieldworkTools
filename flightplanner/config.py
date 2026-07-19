# Imports---------------------------------------------------------------
from dataclasses import dataclass, asdict, field
import argparse
import os
import numpy as np

# Dataclasses-----------------------------------------------------------
@dataclass
class SupportedSensors:
    all: list = field(default_factory = lambda: ["m3m", "m4t", "l2"])
    mapping: list = field(default_factory = lambda: ["m3m", "m4t"])
    lidar: list = field(default_factory = lambda: ["l2"])

@dataclass
class SupportedPlatforms:
    all: list = field(default_factory = lambda: ["m3m", "m4t", "m350", "m400"])
    mavic: list = field(default_factory = lambda: ["m3m"])
    matrice: list = field(default_factory = lambda: ["m4t", "m350", "m400"])

@dataclass
class Config:
    sensortypes: list = field(default_factory = list)
    gsd: float = 4.0
    sensorfactor: float = 21.6888427734375
    altitude: float = None
    tosecurealt: float = 85.0
    width: float = None
    height: float = None
    area: float = 10000.0
    sideoverlap: float = 0.9
    frontoverlap: float = 0.9
    spacing: float = None
    buffer: float = None
    horizontalfov: float = None
    verticalfov: float = None
    secondary_vfov: float = None
    secondary_hfov: float = None
    flightspeed: float = 3.0
    transitionspeed: float = 15.0
    wpturnmode: str = "toPointAndStopWithDiscontinuityCurvature"
    lidar_returns: int = 0
    sampling_rate: int = 240000
    scanning_mode: str = "nonRepetitive"
    imgsamplingmode: str = "distance"
    imucalibrationinterval: float = np.inf
    waypoint_template: str = "./templates/placemark_templates/template_placemark.txt"
    action_template: str = "./templates/placemark_templates/action.txt"
    action_group_template: str = "./templates/placemark_templates/actiongroup.txt"

@dataclass
class Defaults(Config):
    sensor: str = "m3m"
    sensorchoices: list = field(
        default_factory = lambda: ["m3m", "m4t", "l2"]
        )
    platform: str = "m3m"
    platformchoices: list = field(
        default_factory = lambda: ["m3m", "m4t", "m350", "m400"]
        )
    altitudetype: str = "rtf"
    template_directory: str = os.path.join(".", "templates")
    gridmode: str = "lines"
    safetybuffer: float = 10.0
    dtm_follow_segment_length: float = 20.0
    
    def __post_init__(self):
        self.setupchoices = (
            self.sensorchoices +
            self.platformchoices
        )

@dataclass
class M3MConfig(Config):
    platform: str = "m3m"
    droneid: int = 77
    dronesubid: int = 0
    sensor: str = "m3m"
    sensortypes: list = field(
        default_factory = lambda: ["visible", "narrow_band"]
        )
    sensorfactor: float = 21.6888427734375
    sideoverlap: float = 0.85
    frontoverlap: float = 0.9
    overlapsensor: str = "MS"
    horizontalfov: float = 61.2
    verticalfov: float = 48.1
    secondary_hfov: float = 84.0
    secondary_vfov: float = None  # Unknown value, set to None
    coefficients_sol: list = field(
        default_factory = lambda: [-0.0119347, 1.19347]
        )
    coefficients_atd: list = field(
        default_factory = lambda: [
            -0.00896313366070803, 0.8963133773348276
            ]
        )
    flightspeed: float = 4.0
    template_directory: str = os.path.join(".", "templates", "m3m")

#TODO Adjust other drone classes to include the platform and sensor IDs and subIDs
#TODO Include additional tags in templates, unify templates
@dataclass
class Matrice4TConfig(Config):
    platform: str = "m4t"
    droneid: int = 99
    dronesubid: int = 1
    payloadid: int = 89
    payloadsubid: int = 2
    payloadpositionidx: int = 0
    sensor: str = "m4t"
    sensortypes: list = field(default_factory = lambda: ["visible", "ir"])
    altitude: float = 50.0
    sensorfactor: float = 21.6888427734375
    sideoverlap: float = 0.8
    frontoverlap: float = 0.9
    overlapsensor: str = "MS"
    horizontalfov: float = 61.2
    verticalfov: float = 48.1
    secondary_hfov: float = 84.0
    secondary_vfov: float = None  # Unknown value, set to None
    coefficients_sol: list = field(
        default_factory = lambda: [-0.0119347, 1.19347]
        )
    coefficients_atd: list = field(
        default_factory = lambda: [
            -0.00896313366070803, 0.8963133773348276
            ]
        )
    flightspeed: float = 4.0
    template_directory: str = os.path.join(".", "templates", "m3m")

@dataclass
class Matrice350Config(Config):
    platform: str = "m350"
    droneid: int = 89
    dronesubid: int = 0
    altitude: float = 70.0
    altitudetype: str = ""
    sideoverlap: float = 0.8
    frontoverlap: float = 0.75

@dataclass
class Matrice400Config(Config):
    platform: str = "m400"
    droneid: int = 103
    dronesubid: int = 0
    altitude: float = 70.0
    sideoverlap: float = 0.8
    frontoverlap: float = 0.75

@dataclass
class L2M350Config(Matrice350Config):
    sensor: str = "l2"
    sensortypes: list = field(default_factory = lambda: [])
    frontoverlap: float = 0.9
    horizontalfov: float = 70.0
    verticalfov: float = 75.0 # In non-repetitive mode
    secondary_hfov: float = 84.0
    secondary_vfov: float = None  # Unknown value, set to None
    coefficients_sol: list = field(
        default_factory = lambda: [-0.01098424, 1.099605]
        )
    coefficients_atd: list = field(
        default_factory = lambda: [
            -0.010626525878906256, 1.0626525878906254
            ]
        )
    flightspeed: float = 4.0
    overlapsensor: str = "LS"
    template_directory: str = os.path.join(".", "templates", "l2")
    lidar_returns: int = 5
    sampling_rate: int = 240000
    scanning_mode: str = "nonRepetitive"
    gridmode: bool = False # Else, it cannot be overwritten by the user
    imucalibrationinterval: float = 200.

@dataclass
class L2M400Config(Matrice400Config):
    sensor: str = "l2"
    sensortypes: list = field(default_factory = lambda: [])
    frontoverlap: float = 0.9
    horizontalfov: float = 70.0
    verticalfov: float = 75.0 # In non-repetitive mode
    secondary_hfov: float = 84.0
    secondary_vfov: float = None  # Unknown value, set to None
    coefficients_sol: list = field(
        default_factory = lambda: [-0.01098424, 1.099605]
        )
    coefficients_atd: list = field(
        default_factory = lambda: [
            -0.010626525878906256, 1.0626525878906254
            ]
        )
    flightspeed: float = 4.0
    overlapsensor: str = "LS"
    template_directory: str = os.path.join(".", "templates", "l2")
    lidar_returns: int = 5
    sampling_rate: int = 240000
    scanning_mode: str = "nonRepetitive"
    gridmode: bool = False # Else, it cannot be overwritten by the user
    imucalibrationinterval: float = 200.

# Key dictionary--------------------------------------------------------
keydict = {
    "lidar_returns": {
        0: "singleReturnFirst",
        1: "singleReturnStrongest",
        2: "dualReturn",
        3: "tripleReturn",
        4: "quadrupleReturn",
        5: "quintupleReturn"
    },
    "altitude_mode": {
        "rtf": "realTimeFollowSurface",
        "constant": "relativeToStartPoint",
        "dtm": "WGS84"
    }
}

# Classes---------------------------------------------------------------
class ParameterSet(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, values)
        config_map = {
            "m3m": M3MConfig(),
            "m4t": Matrice4TConfig(),
            "l2": L2M400Config(),
            "m350l2": L2M350Config(),
            "m400l2": L2M400Config()
        }
        # Normalize argparse values
        if isinstance(values, list):
            if len(values) == 1:
                values = values[0]
            elif len(values) == 2:
                platform, sensor = values
                D = Defaults()
                if not platform in D.platformchoices:
                    raise ValueError(f"Unknown platform: {platform}.")
                if not sensor in D.sensorchoices:
                    raise ValueError(f"Unknown sensor: {sensor}.")
                values = "".join(values)
            else:
                raise ValueError(f"Setup must be of length 1 or 2. Got {values}")
        
        config = config_map.get(values)
        setattr(namespace, self.dest, values)

        for key, value in asdict(config).items():
            setattr(namespace, key, value)