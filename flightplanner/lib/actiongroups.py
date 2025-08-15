from lib.actions import Action, Hover, Pitch, Photo,\
    AircraftCalibration, \
    StartTimeLapse, StopTimeLapse, \
        StartContinuousShoot, StopContinuousShoot, \
            RecordPointCloud
from config import Config

config = Config()

#==============================================================================
# Functions
def compile_action_group(
        action_group_id, action_id_start_index,
        mode, action_group
        ):
    
    with open(
        config.action_group_template, "r"
        ) as action_group_template:
        action_group_text = action_group_template.read()
        if action_group.action_trigger == None:
            trigger_param = ""
        else:
            trigger_param = "\n" + 12 * " " + "<wpml:actionTriggerParam>" + \
                f"{action_group.action_trigger_param}" + \
                    "</wpml:actionTriggerParam>"

        return action_group_text.format(
            ACTION_GROUP_ID = action_group_id,
            START_INDEX = action_group.action_start_wp.index,
            END_INDEX = action_group.action_end_wp.index,
            MODE = mode,
            ACTIONTRIGGER = action_group.action_trigger,
            ACTIONTRIGGERPARAM = trigger_param,
            ACTIONS = "\n".join([
                a.compile_xml(
                    action_id = action_id_start_index + i
                    ) for i, a in enumerate(action_group.actions)
                ])
        )

#==============================================================================
# Classes
#------------------------------------------------------------------------------
## Action main class
class ActionGroup():
    def __init__(
            self,
            waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        self.waypoint = waypoint
        self._action_start_wp = action_start_wp
        self._action_end_wp = action_end_wp
        self.action_trigger = "reachPoint"
        self.action_trigger_param = None
        self.actions = []
    
    @property
    def action_start_wp(self):
        return self._action_start_wp or self.waypoint
    
    @property
    def action_end_wp(self):
        return self._action_end_wp or self.action_start_wp

    @property
    def instance_idx(self):
        return self.__class__.instances.index(self)
    
    def __repr__(self):
        return f"ActionGroup: {self.actions}"
    
    def end_action_group(self, action_end_wp):
        self._action_end_wp = action_end_wp
    
    def add_action(self, action, **params):
        if not issubclass(action, Action):
            raise TypeError(
                f"Expected an Action subclass, got {type(action)}."
                )
        self.actions.append(action(self, **params))
    
    def stop_action(self, action_class, index = None):
        if index is None:
            for target in action_class.instances:
                if target._action_end_wp is None and hasattr(
                    self.waypoint, "index"
                    ):
                    target.end_action_group(self.waypoint)
        elif index < len(action_class.instances):
            target = action_class.instances[index]
            if target._action_end_wp is None and hasattr(
                self.waypoint, "index"
                ):
                target.end_action_group(self.waypoint)
    
    def link_to(self, action_classes):
        for action_class in action_classes:
            self.stop_action(action_class)

#------------------------------------------------------------------------------
## Specific action group classes
class AircraftCalibrationGroup(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            AircraftCalibration(self)
        ]

class PrepareTimelapseNadirMSMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "betweenAdjacentPoints"
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -90,
                gimbalRotateTime = 10
                ),
            StartTimeLapse.new(self, "visible,narrow_band")
        ]

class StartNadirMSMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None, action_trigger_param = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "multipleDistance"
        self.action_trigger_param = action_trigger_param
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -90,
                gimbalRotateTime = 10
                ),
            StartContinuousShoot.new(self, "visible,narrow_band")
        ]

class StopNadirMSMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            StopContinuousShoot.new(self, "visible,narrow_band")
            ]
        self.link_to([StartNadirMSMapping])

class PrepareObliqueMSMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(
            waypoint,
            action_start_wp = action_start_wp or waypoint,
            action_end_wp = action_end_wp or waypoint
            )
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -45,
                gimbalRotateTime = 10
                ),
            Hover.new(self, 0.5)
        ]
        self.link_to([StartNadirMSMapping])

class StartObliqueMSMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None, action_trigger_param = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "multipleDistance"
        self.action_trigger_param = action_trigger_param
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -45,
                gimbalRotateTime = 10
                ),
            StartContinuousShoot.new(self, "visible,narrow_band")
        ]
        self.link_to([StartNadirMSMapping])

class StopObliqueMSMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            StopContinuousShoot.new(self, "visible,narrow_band")
        ]
        self.link_to([StartObliqueMSMapping])

class StartRecordPointCloud(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None, imu_calibration = False,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            RecordPointCloud.new(self, "startRecord")
            ]
    def add_calibration(self):
        self.actions.insert(0, AircraftCalibration(self))

class StartLiDARMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None, action_trigger_param = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "multipleDistance"
        self.action_trigger_param = action_trigger_param
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -90,
                gimbalRotateTime = 10
                ),
            Photo(self)
        ]

class StopRecordPointCloud(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            RecordPointCloud.new(self, "stopRecord")
        ]
    def add_calibration(self):
        self.actions.insert(0, AircraftCalibration(self))

class PrepareObliqueLiDARMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(
            waypoint,
            action_start_wp = action_start_wp or waypoint,
            action_end_wp = action_end_wp or waypoint
            )
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -45,
                gimbalRotateTime = 10
                ),
            Hover.new(self, 0.5)
        ]
        self.link_to([StartLiDARMapping])

class StartObliqueLiDARMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None, action_trigger_param = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "multipleDistance"
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -45,
                gimbalRotateTime = 10
                ),
            Photo(self)
        ]
        self.link_to([StartNadirMSMapping])

class StopObliqueLiDARMapping(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            Pitch(
                self,
                gimbalPitchRotateAngle = -45,
                gimbalRotateTime = 10
                )
        ]
        self.link_to([StartObliqueLiDARMapping])