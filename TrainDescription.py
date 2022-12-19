class TrainDescription:
    area = None
    description = None
    current_berth = None
    last_report = None
    active = None
    cancelled = None
    berth_history = None

    def __init__(self, area, description, berth, report_time, from_berth=None):
        # TODO: implement type checks
        self.area = area
        self.description = description
        self.current_berth = berth
        self.last_report = report_time
        self.active = True
        self.cancelled = False
        self.berth_history = []

        if from_berth is not None:
            self.berth_history.append(from_berth)
        self.berth_history.append(berth)

    def change_berth(self, new_berth, report_time):
        self.current_berth = new_berth
        self.last_report = report_time
        self.berth_history.append(new_berth)

    def __repr__(self):
        return f'TrainDescription(area={self.area}, current_berth={self.current_berth}, berth_history={self.berth_history})'
