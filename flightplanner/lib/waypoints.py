class Waypoint():
    def __init__(
            self, coordinates, altitude, velocity,
            wp_turning_mode = "toPointAndPassWithContinuityCurvature",
            heading_angle = None, heading_angle_enable = False,
            turn_damping_dist = None, use_straight = True,
            wp_type = "fly"
            ):
        self.coordinates = lib.geo.round_coords(coordinates)
        self.altitude = altitude if altitude is None else round(altitude, 1)
        self.velocity = velocity if velocity is None else round(velocity, 1)
        self.wp_turning_mode = wp_turning_mode
        self.turn_damping_dist = 0 if turn_damping_dist is None else \
            turn_damping_dist
        self.heading_angle = 0 if heading_angle is None else heading_angle
        self.heading_angle_enable = heading_angle_enable
        self.use_straight = use_straight
        self.wp_type = wp_type
        self.actions = []
    
    @property
    def has_actiongroup(self):
        return len(self.actions) > 0
    
    @property
    def n_actions(self):
        return len(self.actions)

    def __repr__(self):
        return f"{self.coordinates} a: {self.altitude}m, v: {self.velocity}m/s"
    
    def compile_actions(
            self, action_group_id, action_start_index,
            action_start_wp, uav_type = "enterprise",
            template = False
            ):
        if len(self.actions) > 0:
            action_xml = lib.actions.create_action_group(
                action_group_id = action_group_id,
                action_id_start_index = action_start_index,
                action_start_wp = action_start_wp,
                actions = self.actions,
                template = False,
                mode = "sequence" if uav_type == "enterprise" else "parallel"
            )
        else:
            action_xml = ""
        
        return action_xml
    
    def add_action(self, action):
        self.actions.append(action)
    
    def add_actions(self, actions):
        self.actions.extend(actions)
    
    def set_altitude(self, altitude):
        self.altitude = round(altitude, 1)
    
    def set_speed(self, speed):
        self.velocity = speed
    
    def set_turning_mode(self, wp_turning_mode):
        self.wp_turning_mode = wp_turning_mode
    
    def set_damping_dist(self, turn_damping_dist):
        self.turn_damping_dist = turn_damping_dist
    
    def set_heading_angle(self, heading_angle):
        self.heading_angle = heading_angle
    
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
            self, index, action_group_id, action_id_start_index,
            template_File
            ):
        with open(template_File, "r") as placemark_template:
            placemark_text = placemark_template.read()
            new_placemark = placemark_text.format(
                lng = self.coordinates[0],
                lat = self.coordinates[1],
                index = index,
                waypoint_height = self.altitude,
                SPEED = self.velocity,
                WAYPOINT_HEADING_MODE = self.wp_turning_mode,
                HEADING_ANGLE = 0 if self.wp_turning_mode == "followWayline" \
                    else self.heading_angle,
                WAYPOINT_TURN_MODE = self.wp_turning_mode,
                TURN_DAMPING_DISTANCE = self.turn_damping_dist,
                USE_STRAIGHT_LINES = int(self.use_straight),
                HEADING_ANGLE_ENABLE = int(self.heading_angle_enable),
                action = self.compile_actions(
                    action_group_id, action_id_start_index,
                    action_start_wp = index, uav_type = uav_type
                    )
            )
        
        if uav_type == "enterprise":
            template_file = "templates/template_placemark_enterprise.xml"
            
            with open(template_file, "r") as placemark_template:
                placemark_text = placemark_template.read()
                new_placemark_template = placemark_text.format(
                    lng = self.coordinates[0],
                    lat = self.coordinates[1],
                    index = index,
                    waypoint_height = self.altitude,
                    SPEED = self.velocity,
                    WAYPOINT_HEADING_MODE = self.wp_turning_mode,
                    HEADING_ANGLE = 0 if self.wp_turning_mode == \
                        "followWayline" else self.heading_angle,
                    WAYPOINT_TURN_MODE = self.wp_turning_mode,
                    TURN_DAMPING_DISTANCE = self.turn_damping_dist,
                    USE_STRAIGHT_LINES = int(self.use_straight),
                    HEADING_ANGLE_ENABLE = int(self.heading_angle_enable),
                    action = self.compile_actions(
                        action_group_id, action_id_start_index,
                        action_start_wp = index, uav_type = uav_type,
                        template = True
                        )
                )
                
                return new_placemark, new_placemark_template
        else:
            return new_placemark