class Times:

    section_name = 'TIMES'

    unit_sec = 0
    unit_min = 1
    unit_hr = 2
    unit_day = 3
    unit_text = {0: 'Second', 1: 'Minute', 2: 'Hour', 3: 'Day'}

    stats_avg = 0
    stats_min = 1
    stats_max = 2
    stats_range = 3
    stats_none = 4
    stats_text = {0: 'Averaged', 1: 'Minimum', 2: 'Maximum', 3: 'Range', 4: 'None'}

    def __init__(self):
        self.units = Times.unit_hr
        self.duration = 1
        self.hydraulic_timestamp = Hour(1, 0)
        self.quality_timestamp = Hour(0, 5)
        self.rule_timestamp = Hour(1, 0)
        self.pattern_timestamp = Hour(1, 0)
        self.pattern_start = Hour(0, 0)
        self.report_timestamp = Hour(1, 0)
        self.report_start = Hour(0, 0)
        self.start_clocktime = Hour(0, 0)
        self.statistics = Times.stats_avg


class Hour:

    def __init__(self, hours, mins):
        self.hours = hours
        self.mins = mins

    def get_as_text(self):
        return str(self.hours).zfill(2) + ':' + str(self.mins).zfill(2)