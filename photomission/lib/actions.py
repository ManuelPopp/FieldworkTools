#==============================================================================
# Imports
import warnings
from config import Config

config = Config()
warnings.simplefilter("once", append = True)

#==============================================================================
# Functions
def create_action(action_id: int, action: str, action_params: dict):
    action_params_str = "\n".join([
        " " * 14 + f"<wpml:{k}>{action_params[k]}</wpml:{k}>"
        for k in action_params
        ])
    
    with open(config.action_template, "r") as action_template:
        action_text = action_template.read()
        return action_text.format(
            ACTION_ID = action_id,
            ACTION = action,
            ACTION_PARAMS = action_params_str
            )

#==============================================================================
# Classes
#------------------------------------------------------------------------------
## Action main class
class Action():
    def __init__(self, action_group):
        self.action_group = action_group
        self.default = self.params = {}
        self._action_id = None
    
    @property
    def action_id(self):
        if self._action_id is not None:
            return self._action_id
        try:
            return self.action_group.actions.index(self)
        except:
            return 0
    
    @property
    def compiled(self):
        return self.compile_xml()
    
    def compile_xml(self, **kwargs):
        if "action_id" in kwargs.keys():
            self._action_id = kwargs["action_id"]
        
        return create_action(self.action_id, self.name, self.params)
    
    def __repr__(self):
        return f"{self.name}, id: {self.action_id}:\n" + "\n".join(
            [f"\t{k}: {self.params[k]}" for k in self.params]
        ) + "\n"
    
    def check(self):
        for k in self.params.keys():
            if k not in self.default.keys():
                warnings.warn(
                    f"Check: Invalid parameter '{k}' will be dropped."
                    )
                del self.params[k]

#------------------------------------------------------------------------------
## Specific action classes
class AircraftCalibration(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "aircraftCalibration"
        self.default = self.params = {
            "calibrationHeading" : int(0),
            "calibrationTimes" : int(3),
            "calibrationDistance" : int(30)
            }
        
        self.params.update(kwargs)
        self.check()

class Focus(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "focus"
        self.default = self.params = {
            "focusX" : 0.25,
            "focusY" : 0.25,
            "focusRegionWidth" : 0.5,
            "focusRegionHeight" : 0.5,
            "isPointFocus" : int(0),
            "isInfiniteFocus" : int(0),
            "payloadPositionIndex" : int(0)
            }
        
        self.params.update(kwargs)
        self.check()

class Hover(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "hover"
        self.default = self.params = {"hoverTime" : 0}
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, time):
        return cls(
            action_group = action_group,
            hoverTime = float(time),
        )

class OrientedShoot(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "orientedShoot"
        self.params = self.default = {
            "payloadPositionIndex" : 0,
            "payloadLensIndex" : "zoom",
            "useGlobalPayloadLensIndex" : 0,
            "focusX" : 0.25,
            "focusY" : 0.25,
            "focusRegionWidth" : 0.5,
            "focusRegionHeight" : 0.5,
            "focalLength" : 240,
            "gimbalPitchRotateAngle" : 0,
            "gimbalRollRotateAngle" : 0,
            "gimbalYawRotateAngle" : 272,
            "aircraftHeading" : 272,
            "accurateFrameValid" : 0,
            "targetAngle" : 0,
            "actionUUID" : "068d76e9-0f15-45f6-86a0-33c45aef63ec",
            "imageWidth" : 0,
            "imageHeight" : 0,
            "AFPos" : 0,
            "gimbalPort" : 0,
            "orientedCameraType" : 81,
            "orientedFilePath" : "",
            "orientedFileSize" : 0,
            "orientedFileSuffix" : "",
            "orientedPhotoMode" : "normalPhoto",
        }
        
        self.params.update(kwargs)
        self.check()

    @classmethod
    def new(cls, action_group, yaw, pitch, zoom):
        return cls(
            action_group = action_group,
            gimbalPitchRotateAngle = pitch,
            aircraftHeading = yaw,
            gimbalYawRotateAngle = yaw,
            focalLength = zoom
        )

class Photo(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "takePhoto"
        self.default = {
            "payloadPositionIndex" : 0,
            "useGlobalPayloadLensIndex" : 0
        }
        
        self.params = {
            "payloadPositionIndex" : 0,
            "useGlobalPayloadLensIndex" : 0
            }
        self.params.update(kwargs)
        self.check()

class Pitch(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "gimbalRotate"
        self.default = self.params = {
            "gimbalHeadingYawBase" : str("aircraft"),
            "gimbalRotateMode" : "absoluteAngle",
            "gimbalPitchRotateEnable" : int(1),
            "gimbalPitchRotateAngle" : 0.0,
            "gimbalRollRotateEnable" : int(0),
            "gimbalRollRotateAngle" : int(0),
            "gimbalYawRotateEnable" : int(0),
            "gimbalYawRotateAngle" : int(0),
            "gimbalRotateTimeEnable" : int(0),
            "gimbalRotateTime" : int(0),
            "payloadPositionIndex" : int(0)
            }
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, angle):
        return cls(
            action_group = action_group,
            gimbalPitchRotateEnable = int(1),
            gimbalPitchRotateAngle = angle
        )

class RecordPointCloud(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "recordPointCloud"
        self.default = self.params = {
            "recordPointCloudOperate" : "startRecord",
            "payloadPositionIndex" : int(0)
            }
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, action = "startRecord"):
        return cls(
            action_group = action_group,
            recordPointCloudOperate = action,
        )

class StartContinuousShoot(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "startContinuousShooting"
        self.default = self.params = {
            "payloadPositionIndex" : int(0),
            "useGlobalPayloadLensIndex" : int(0),
            "payloadLensIndex" : str("visable,narrow_band")
            }
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, payloadLensIndex):
        return cls(
            action_group = action_group,
            payloadLensIndex = payloadLensIndex
        )

class StopContinuousShoot(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "stopContinuousShooting"
        self.default = self.params = {
            "payloadPositionIndex" : int(0),
            "payloadLensIndex" : str("visable,narrow_band")
            }
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, payloadLensIndex):
        return cls(
            action_group = action_group,
            payloadLensIndex = payloadLensIndex
        )

class StartTimeLapse(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "startTimeLapse"
        self.default = self.params = {
            "payloadPositionIndex" : int(0),
            "useGlobalPayloadLensIndex" : int(0),
            "payloadLensIndex" : str("visable,narrow_band"),
            "minShootInterval" : float(1.0)
            }
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, payloadLensIndex):
        return cls(
            action_group = action_group,
            payloadLensIndex = payloadLensIndex
        )

class StopTimeLapse(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "stopTimeLapse"
        self.default = self.params = {
            "payloadPositionIndex" : int(0),
            "payloadLensIndex" : str("visable,narrow_band")
            }
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group, payloadLensIndex):
        return cls(
            action_group = action_group,
            payloadLensIndex = payloadLensIndex
        )

class Yaw(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "rotateYaw"
        self.default = self.params = {
            "aircraftHeading" : 0,
            "aircraftPathMode" : "clockwise"
        }
        
        theta = kwargs["aircraftHeading"]

        theta = -180 + (theta % 360)

        theta = round(theta)
        kwargs["aircraftHeading"] = theta
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new(cls, action_group,angle):
        return cls(
            action_group = action_group,
            aircraftHeading = angle
            )

class Zoom(Action):
    def __init__(self, action_group, **kwargs):
        super().__init__(action_group)
        self.name = "zoom"
        self.default = self.params = {
            "focalLength" : 0,
            "isUseFocalFactor" : 1,
            "focalFactor" : 0,
            "payloadPositionIndex": 0
            } if "focalFactor" in kwargs.keys() else {
                "focalLength" : 0,
                "isUseFocalFactor" : 0,
                "payloadPositionIndex" : 0
                }
        
        self.params.update(kwargs)
        self.check()
    
    @classmethod
    def new_mm(cls, action_group, mm):
        return cls(
            action_group = action_group,
            focalLength = mm
            )
    
    def new_factor(cls, action_group, factor):
        return cls(
            action_group = action_group,
            focalFactor = factor
            )