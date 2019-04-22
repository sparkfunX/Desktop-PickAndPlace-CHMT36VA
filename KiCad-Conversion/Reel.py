class Reel():
    """Contains all the info for a given feeder or reel of components"""
    
    def __init__(self,
        feeder_ID = None,
        device_name = None,
        stack_x_offset = None,
        stack_y_offset = None,
        height = 0,
        speed = 0,
        component_size_x = 0,
        component_size_y = 0,
        head = 1,
        angle_compensation = 0,
        feed_spacing = None,
        place_component = True,
        check_vacuum = True,
        use_vision = True,
        relative_tape_angle = 0,
        aliases = None,

        footprint = None,
        value = None,
        comment = None
        ):

        self.feeder_ID = feeder_ID
        self.device_name = device_name
        self.stack_x_offset = stack_x_offset
        self.stack_y_offset = stack_y_offset
        self.height = height
        self.speed = speed
        self.component_size_x = component_size_x
        self.component_size_y = component_size_y
        self.head = head
        self.angle_compensation = angle_compensation
        self.feed_spacing = feed_spacing
        self.place_component = place_component
        self.check_vacuum = check_vacuum
        self.use_vision = use_vision
        self.relative_tape_angle = relative_tape_angle
        self.aliases = aliases

        self.footprint = footprint
        self.value = value
        self.comment = comment

    def __repr__(self):
        return "<Reel {0}>".format(self.reel_number)

    def add_default_feeder(self):
        self.append(Reel(feeder_ID=0, device_name=""))

