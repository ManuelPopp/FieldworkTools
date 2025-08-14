#==============================================================================
# Imports
from lib.waypoints import Waypoint

#==============================================================================
# Classes
#------------------------------------------------------------------------------
## Waypoint group main class
class WaypointGroup():
    def __init__(self, n_waypoints, wp_type = None):
        self.n_waypoints = n_waypoints
        self.wp_type = wp_type
    
    @property
    def n_actions(self):
        return sum([w.n_actions for w in self.waypoints])
    
    @property
    def waypoints(self):
        return self.create_waypoint_group()
    
    def create_waypoint(self, coordinates, altitude, actions):
        return Waypoint(coordinates, altitude, actions)
    
    def create_waypoint_group(self):
        print(
            "This is a generic parent class. Rules for creating waypoints " +
            "are not defined."
            )
    
    def to_xml(
            self, start_id, start_action_group_id, action_start_index,
            sensor
            ):
        xml_strings = []
        
        for i, w in enumerate(self.waypoints):
            xml_strings.append(
                w.to_xml(
                    index = start_id + i,
                    action_group_id = start_action_group_id,
                    action_start_index = action_start_index,
                    sensor = sensor
                    )
                )
            
            if w.has_actiongroup:
                start_action_group_id += 1
            
            action_start_index += len(w.actions)
        
        return "".join([xml[0] for xml in xml_strings]), "".join(
            [xml[1] for xml in xml_strings]
            )

#------------------------------------------------------------------------------
## Specific waypoint group classes
### Calibrate IMU
class IMUCalibration(WaypointGroup):
    def __init__(self, waypoint_0, waypoint_1, n_steps, step_length_m):
        self.wp_type = "fly"
        self.waypoint_group_type = "calibrate_imu"
        self.n_steps = n_steps
        self.step_length_m = step_length_m
        self.waypoint_0 = waypoint_0
        self.waypoint_1 = waypoint_1
    
    def create_waypoint_group(self):
        intermediate_coords, intermediate_velocities, \
            intermediate_altitudes = add_slowdowns(
                mission_coords = [
                    self.waypoint_0.coordinates, self.waypoint_1.coordinates
                    ],
                mission_speeds = [
                    self.waypoint_0.velocity, self.waypoint_1.velocity
                    ],
                mission_altitudes = [
                    self.waypoint_0.altitude, self.waypoint_1.altitude
                    ],
                n_steps = self.n_steps,
                segment_lengths = self.step_length_m
                )
        
        wpt_group = [
            Waypoint(
                coordinates = c, altitude = a, velocity = v,
                wp_turning_mode = "toPointAndPassWithContinuityCurvature"
                ) for c, a, v in zip(
                    intermediate_coords, intermediate_altitudes,
                    intermediate_velocities[1:] + [self.waypoint_1.velocity]
                    )
                ]
        
        self.waypoint_0.set_speed(intermediate_velocities[0])
        self.n_waypoints = len(wpt_group)
        
        return wpt_group