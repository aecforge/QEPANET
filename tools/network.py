from collections import OrderedDict

class Tables:

    pipes_table_name = 'pipes'
    junctions_table_name = 'junctions'
    reservoirs_table_name = 'reservoirs'
    tanks_table_name = 'tanks'
    pumps_table_name = 'pumps'
    valves_table_name = 'valves'

    def __init__(self):
        pass


class Junction:

    field_name_eid = 'id'
    field_name_demand = 'demand'
    field_name_depth = 'depth'
    field_name_elevation = 'elev'
    field_name_pattern = 'pattern'

    def __init__(self, eid):
        self.eid = eid
        self.demand = 0
        self.depth = 0
        self.elevation = -1
        self.pattern = None


class Reservoir:

    field_name_eid = 'id'
    field_name_elevation = 'elev'
    field_name_elevation_corr = 'elev_corr'
    field_name_pressure = 'pressure'

    def __init__(self, eid):
        self.eid = eid
        self.elevation = -1
        self.elevation_corr = 0
        self.pressure = 0


class Tank:
    field_name_eid = 'id'
    field_name_curve = 'curve'
    field_name_diameter = 'diameter'
    field_name_elevation = 'elev'
    field_name_elevation_corr = 'elev_corr'
    field_name_level_init = 'init_level'
    field_name_level_max = 'max_level'
    field_name_level_min = 'min_level'
    field_name_vol_min = 'min_vol'

    def __init__(self, eid):
        self.eid = eid
        self.curve = -1
        self.diameter = 0
        self.elevation = -1
        self.elevation_corr = 0
        self.level_init = 0
        self.level_max = 0
        self.level_min = 0
        self.vol_min = 0

class Pipe:

    field_name_eid = 'id'
    field_name_demand = 'demand'
    field_name_diameter = 'diameter'
    field_name_end_node = 'end_node'
    field_name_length = 'length'
    field_name_minor_loss = 'minor_loss'
    field_name_roughness = 'roughness'
    field_name_start_node = 'start_node'
    field_name_status = 'status'

    def __init__(self, eid):
        self.eid = eid

        self.demand = 0
        self.diameter = -1
        self.end_node = -1
        self.length = 0
        self.minor_loss = 0
        self.roughness = -1
        self.start_node = -1
        self.status = 'on'


class Pump:

    field_name_eid = 'id'
    field_name_curve = 'curve'

    def __init__(self, eid):
        self.eid = eid

        self.curve = -1


class Valve:
    field_name_eid = 'id'
    field_name_diameter = 'diameter'
    field_name_minor_loss = 'minor_loss'
    field_name_setting = 'setting'
    field_name_type = 'type'

    type_prv = 'PRV'
    type_psv = 'PSV'
    type_pbv = 'PBV'
    type_fcv = 'FCV'
    type_tcv = 'TCV'
    type_gpv = 'GPV'

    types = OrderedDict()
    types['PRV'] = 'PRV (pressure reducing)'
    types['PSV'] = 'PSV (pressure sustaining)'
    types['PBV'] = 'PBV (pressure breaker)'
    types['FCV'] = 'FCV (flow control)'
    types['TCV'] = 'TCV (throttle control)'
    types['GPV'] = 'GPV (general purpose)'

    def __init__(self, eid):
        self.eid = eid


class Pattern:

    def __init__(self, name, id):
        self.id = id
        self.name = name
        self.values = []

    def add_value(self, val):
        self.values.append(val)


class Curve:

    def __init__(self, name, id):
        self.id = id
        self.name = name
        self.xs = []
        self.ys = []

    def add_xy(self, x, y):
        self.xs.append(x)
        self.ys.append(y)