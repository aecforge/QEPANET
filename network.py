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
    field_name_elevation = 'elevation'
    field_name_pattern = 'pattern'

    def __init__(self, eid):
        self.eid = eid
        self.demand = 0
        self.depth = 0
        self.elevation = -1
        self.pattern = None


class Pipe:

    field_name_eid = 'id'
    field_name_demand = 'demand'
    field_name_diameter = 'diameter'
    field_name_end_node = 'end_node'
    field_name_length = 'length'
    field_name_loss = 'minor_loss'
    field_name_roughness = 'roughness'
    field_name_start_node = 'start_node'
    field_name_status = 'status'

    def __init__(self, eid):
        self.eid = eid

        self.demand = 0
        self.diameter = -1
        self.end_node = -1
        self.length = 0
        self.loss = 0
        self.roughness = -1
        self.start_node = -1
        self.status = 'on'
