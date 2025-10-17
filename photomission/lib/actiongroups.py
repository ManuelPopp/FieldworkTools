from lib.actions import Action, Hover, Pitch, Photo, Zoom
from config import Config

config = Config()

#==============================================================================
# Functions
def compile_action_group(
        action_group_id, action_id_start_index,
        action_group, mode = "parallel"
        ):
    
    with open(
        config.action_group_template, "r"
        ) as action_group_template:
        action_group_text = action_group_template.read()

        return action_group_text.format(
            ACTION_GROUP_ID = action_group_id,
            START_INDEX = action_group.action_start_wp.index,
            END_INDEX = action_group.action_end_wp.index \
                if action_group.action_duration is None \
                    else action_group.action_start_wp.index + \
                        action_group.action_duration,
            MODE = mode,
            ACTIONTRIGGER = action_group.action_trigger,
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
        self.action_duration = None
    
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
class PreparePhotoActionGroup(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.action_duration = None
        self.actions = [
            Pitch.new(self, angle = -90.0)
        ]

class PreparePhotoZoom(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "betweenAdjacentPoints"
        self.action_duration = 1
        self.actions = [
            Zoom.new_factor(action_group = self, factor = 2.5)
        ]

class PhotoActionGroup(ActionGroup):
    instances = []
    def __init__(
            self, waypoint = None,
            action_start_wp = None, action_end_wp = None
            ):
        super().__init__(waypoint, action_start_wp, action_end_wp)
        self.__class__.instances.append(self)
        self.action_trigger = "reachPoint"
        self.actions = [
            Photo(self),
            Hover.new(action_group = self, time = 1)
        ]
        #self.link_to([PreparePhotoActionGroup])