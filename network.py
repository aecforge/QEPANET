class Tables:
    def __init__(self):
        self.pipes_table_name = 'pipes'
        self.nodes_table_name = 'nodes'
        self.reservoirs_table_name = 'reservoirs'
        self.sources_table_name = 'sources'
        self.pumps_table_name = 'pumps'
        self.valves_table_name = 'valves'


class Node:
    def __init__(self, eid):
        self.eid = eid
        self.demand = 0
        self.depth = 0
        self.elevation = -1
        self.pattern = None

        self.eid_field_name = 'id'
        self.demand_field_name = 'demand'
        self.depth_field_name = 'depth'
        self.elevation_field_name = 'elevation'
        self.patter_field_name = 'pattern'


class Pipe:
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

        self.demand_field_name = 'demand'
        self.diameter_field_name = 'diameter'
        self.end_node_field_name = 'end_node'
        self.length_field_name = 'length'
        self.loss_field_name = 'loss'
        self.roughness_field_name = 'roughness'
        self.start_node_field_name = 'start_node'
        self.status_field_name = 'status'
