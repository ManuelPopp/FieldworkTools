from warnings import warn
from lib.geo import get_utm_crs, round_coords, coordinates_to_utm
from lib.actions import Action
from lib.actiongroups import (
    ActionGroup, compile_action_group
)
from lib.utils import get_heading_angle

class Waypoint():
    def __init__(
            self, coordinates, altitude, velocity,
            turn_mode = "toPointAndStopWithContinuityCurvature",
            heading_mode = "smoothTransition",
            heading_angle = None, heading_angle_enable = True,
            turn_damping_dist = None, use_straight = True,
            wp_type = "fly", utm_crs = None, actions = None,
            mission = None
            ):
        self.coordinates = round_coords(coordinates)
        self._utm_crs = utm_crs
        self.altitude = altitude if altitude is None else round(altitude, 1)
        self.velocity = velocity if velocity is None else round(velocity, 1)
        self.turn_mode = turn_mode
        self.heading_mode = heading_mode
        self.turn_damping_dist = 0 if turn_damping_dist is None else \
            turn_damping_dist
        self._heading_angle = heading_angle
        self.heading_angle_enable = heading_angle_enable
        self.use_straight = use_straight
        self.wp_type = wp_type
        self.actions = [] if actions is None else actions
        self.mission = mission
        self.altitude_adjusted = False
    
    @property
    def index(self):
        if hasattr(self, "_index") and self._index is not None:
            return self._index
        if hasattr(self.mission, "waypoints"):
            return self.mission.waypoints.index(self)
        return None
    
    @property
    def heading_angle(self):
        if self._heading_angle is None:
            try:
                idx = self.index
                num_waypoints = len(self.mission.waypoints)
                if idx == num_waypoints - 1:
                    return 0
                wp1 = self.mission.waypoints[idx + 1]
                return get_heading_angle(self, wp1)
            except Exception as e:
                warn(f"Could not determine heading angle: {e}")
        return self._heading_angle
    
    @property
    def utm_crs(self):
        if self._utm_crs is None:
            if self.mission is None:
                self._utm_crs = get_utm_crs(self.coordinates)
            else:
                self._utm_crs = self.mission.local_crs
        return self._utm_crs
    
    @property
    def coordinates_utm(self):
        return coordinates_to_utm(
            self.coordinates[0], self.coordinates[1]
            ) if self.utm_crs is None else coordinates_to_utm(
                self.coordinates[0], self.coordinates[1],
                utm_crs = self.utm_crs
            )
    
    @property
    def has_actiongroup(self):
        return len(self.actions) > 0
    
    @property
    def num_action_groups(self):
        return len(self.actions)
    
    @property
    def num_actions(self):
        return sum([len(ag.actions) for ag in self.actions])

    def __repr__(self):
        tpl = "Waypoint\n{c}, alt: {a} m, v: {v} m/s\nactions: {act}\n"
        return tpl.format(
            c = self.coordinates,
            a = self.altitude,
            v = self.velocity,
            act = self.actions
        )
    
    def compile_actions(
            self, action_start_index
            ):
        action_xmls = []
        for group_index, action_group in enumerate(self.actions):
            action_xml_i = compile_action_group(
                action_group_id = group_index + 1, # action group IDs start at 1
                action_id_start_index = action_start_index,
                action_group = action_group,
                mode = "parallel"
            )
            action_xmls.append(action_xml_i)
        
        return "\n".join(action_xmls)
    
    def _add_action(self, action):
        if not isinstance(action, Action):
            raise TypeError(
                f"Expected an Action subclass, got {type(action)}."
                )
        self.actions[-1].add_action(action)
    
    def _add_actions(self, actions):
        for action in actions:
            if not isinstance(action, Action):
                raise TypeError(
                    f"Expected an Action subclass, got {type(action)}."
                    )
            self.actions[-1].add_actions(action)

    def add_action_group(self, action_group, **kwargs):
        if not issubclass(action_group, ActionGroup):
            t = type(action_group)
            raise TypeError(
                f"Expected an ActionGroup subclass, got {t}"
            )
        self.actions.append(action_group(waypoint = self, **kwargs))
    
    def set_altitude(self, altitude):
        self.altitude = round(altitude, 1)
    
    def set_speed(self, speed):
        self.velocity = speed
    
    def set_turning_mode(self, wp_turning_mode):
        self.wp_turning_mode = wp_turning_mode
    
    def set_damping_dist(self, turn_damping_dist):
        self.turn_damping_dist = turn_damping_dist
    
    def set_heading_angle(self, heading_angle):
        self._heading_angle = heading_angle
    
    def enable_heading_angle(self, *args):
        if len(args) == 1:
            self.heading_angle_enable = int(args[0])
        elif len(args) == 0:
            self.heading_angle_enable = 1
        else:
            raise ValueError(f"Invalid number of arguments: {len(args)}.")
    
    def disable_heading_angle(self):
        self.heading_angle_enable = 0
   
    def to_xml(
            self,
            template_file, index = None
            ):
        with open(template_file, "r") as placemark_template:
            placemark_text = placemark_template.read()
            new_placemark = placemark_text.format(
                LONGITUDE = self.coordinates[0],
                LATITUDE = self.coordinates[1],
                INDEX = self.index if index is None else index,
                EXECALTITUDE = self.altitude,
                WPSPEED = self.velocity,
                HEADINGMODE = self.heading_mode,
                HEADINGANGLE = self.heading_angle,
                TURNMODE = self.turn_mode,
                TURN_DAMPING_DISTANCE = self.turn_damping_dist,
                USE_STRAIGHT_LINES = int(self.use_straight),
                HEADING_ANGLE_ENABLE = int(self.heading_angle_enable),
                ACTIONS = self.compile_actions(self.action_start_index),
                GIMBALPITCH = self.pitch if hasattr(self, "pitch") else 0
            )
        
        return new_placemark