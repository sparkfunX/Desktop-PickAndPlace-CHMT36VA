class ICTray():
    """Contains info for a IC Tray or cut tape on the PCB Area.
    Is linked to a Feeder via the feeder_IC.
    """
    def __init__(self,
        feeder_ID=None,
        first_IC_center_X=0,
        first_IC_center_Y=0,
        last_IC_center_X=0,
        last_IC_center_Y=0,
        number_X=0,
        number_Y=0,
        start_IC=0
        ):

        self.feeder_ID=feeder_ID
        self.first_IC_center_X=first_IC_center_X
        self.first_IC_center_Y=first_IC_center_Y
        self.last_IC_center_X=last_IC_center_X
        self.last_IC_center_Y=last_IC_center_Y
        self.number_X=number_X
        self.number_Y=number_Y
        self.start_IC=start_IC