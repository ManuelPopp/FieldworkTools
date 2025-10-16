#==============================================================================
# Imports
import copy
from lib.actiongroups import PhotoActionGroup
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
class Photogroup(WaypointGroup):
    def __init__(self, waypoint, num_photos = 1):
        self.wp_type = "photo"
        self.waypoint_group_type = "photogroup"
        self.waypoint = waypoint
        self.n = num_photos
    
    def create_waypoint_group(self):
        #self.waypoint.pitch = -90.0                        # look straight down
        wpt_group = [self.waypoint]
        for _ in range(self.n):
            wpt_i = copy.deepcopy(self.waypoint)
            wpt_i.wp_type = "photo"
            wpt_i.add_action_group(PhotoActionGroup)
            wpt_i.pitch = -90.0
            wpt_group.append(wpt_i)
        
        wpt_group.append(copy.deepcopy(self.waypoint))
        self.n_waypoints = len(wpt_group)
        
        return wpt_group