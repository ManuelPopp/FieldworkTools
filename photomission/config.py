# Save to: This PC\DJI RC 2\Internal shared storage\Android\data\dji.go.v5\files\waypoint
# Imports---------------------------------------------------------------
from dataclasses import dataclass, asdict, field
import argparse
import os
import numpy as np

missions = {
    "Photoroute01": "0FEC1DFE-95C9-44ED-8CD5-63283C1875CB"
}

# Dataclasses-----------------------------------------------------------
@dataclass
class Config:
    slots: dict = field(default_factory = lambda: missions)
    template_kml_directory: str = os.path.join(".", "templates")
    waypoint_template: str = os.path.join(
        ".", "templates", "placemark.template"
        )
    action_template: str = os.path.join(
        ".", "templates", "action.template"
    )
    action_group_template: str = os.path.join(
        ".", "templates", "actiongroup.template"
    )

@dataclass
class Defaults(Config):
    slot: int = 0
    flightaltitude: float = 60
    minimum_flightaltitude: float = 20
    photoaltitude: float = 10
    template_directory: str = os.path.join(".", "templates")
    safetybuffer: float = 10.0
    dsm_follow_segment_length: float = 20.0
    transitionspeed: float = 8.0