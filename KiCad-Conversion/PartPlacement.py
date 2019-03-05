class PartPlacement():
    """PartPlacement contains all coordinate and physical info for a given component."""
    
    def __init__(self, 
        component_ID,
        feeder_ID = 0,
        speed = 0,
        height = 0,
        rotation = 0,
        designator = None,
        head = 1,
        x = 0.0,
        y = 0.0,
        place_component = True,
        check_vacuum = True,
        use_vision = True,

        centroid_correction_x = 0,
        centroid_correction_y = 0,

        footprint = None,
        value = None,
        comment = None
        ):

        self.component_ID = component_ID
        self.feeder_ID = feeder_ID
        self.speed = speed
        self.height = height
        self.rotation = rotation
        self.designator = designator
        self.head = head
        self.x = x
        self.y = y
        self.place_component = place_component
        self.check_vacuum = check_vacuum
        self.use_vision = use_vision
        self.centroid_correction_x = centroid_correction_x
        self.centroid_correction_y = centroid_correction_y

        self.footprint = footprint
        self.value = value
        self.comment = comment

    # Print the name in a format that is easy to read in CharmHigh program
    def component_name(self):
        out = "{}".format(self.value)
        # if self.footprint:
        #     out += "-{}".format(self.footprint)
        return out

