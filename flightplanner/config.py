# Imports---------------------------------------------------------------
from dataclasses import dataclass, asdict, field
import argparse
import os

# Dataclasses-----------------------------------------------------------
@dataclass
class Config:
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
    gridmode: bool = False

@dataclass
class Defaults(Config):
    sensor: str = "m3m"
    sensorchoices: list = field(default_factory = lambda: ["m3m", "l2"])
    template_directory: str = os.path.join(".", "templates")

@dataclass
class M3MConfig(Config):
    sensorfactor: float = 21.6888427734375
    sideoverlap: float = 0.9
    frontoverlap: float = 0.9
    overlapsensor: str = "MS"
    horizontalfov: float = 61.2
    verticalfov: float = 48.1
    secondary_hfov: float = 84.0
    secondary_vfov: float = None  # Unknown value, set to None
    coefficients: list = field(default_factory = lambda: [-0.0119347, 1.19347])
    flightspeed: float = 3.0
    template_directory: str = os.path.join(".", "templates", "m3m")

@dataclass
class Matrice400Config(Config):
    altitude: float = 70.0
    sideoverlap: float = 0.8
    frontoverlap: float = 0.75

@dataclass
class L2Config(Matrice400Config):
    horizontalfov: float = 70.0
    verticalfov: float = 75.0 # In non-repetitive mode
    secondary_hfov: float = 84.0
    secondary_vfov: float = None  # Unknown value, set to None
    coefficients: list = field(default_factory = lambda: [-0.01098424, 1.099605])
    flightspeed: float = 7.0
    overlapsensor: str = "LS"
    template_directory: str = os.path.join(".", "templates", "l2")
    lidar_returns: int = 5
    sampling_rate: int = 240000
    scanning_mode: str = "nonRepetitive"
    gridmode: bool = False # Else, it cannot be overwritten by the user

# Key dictionary--------------------------------------------------------
keydict = {
    "lidar_returns": {
        0: "singleReturnFirst",
        1: "singleReturnStrongest",
        2: "dualReturn",
        3: "tripleReturn",
        4: "quadrupleReturn",
        5: "quintupleReturn"
    }
}

# Classes---------------------------------------------------------------
class ParameterSet(argparse.Action):
    def __call__(self, parser, namespace, values, option_string = None):
        setattr(namespace, self.dest, values)
        config_map = {
            "m3m": M3MConfig(),
            "l2": L2Config()
        }
        config = config_map.get(values)
        if config is None:
            raise ValueError(f"Unknown UAV model: {values}.")
        
        for key, value in asdict(config).items():
            setattr(namespace, key, value)