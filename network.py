class Tables:
    def __init__(self):
        self.pipes_table_name = 'pipes'
        self.nodes_table_name = 'nodes'
        self.reservoirs_table_name = 'reservoirs'
        self.sources_table_name = 'sources'
        self.pumps_table_name = 'pumps'
        self.valves_table_name = 'valves'


class Node:

    eid_field_name = 'id'
    demand_field_name = 'demand'
    depth_field_name = 'depth'
    elevation_field_name = 'elevation'
    patter_field_name = 'pattern'

    def __init__(self, eid):
        self.eid = eid
        self.demand = 0
        self.depth = 0
        self.elevation = -1
        self.pattern = None


class Pipe:

    demand_field_name = 'demand'
    diameter_field_name = 'diameter'
    end_node_field_name = 'end_node'
    length_field_name = 'length'
    loss_field_name = 'loss'
    roughness_field_name = 'roughness'
    start_node_field_name = 'start_node'
    status_field_name = 'status'

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
