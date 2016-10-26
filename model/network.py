from collections import OrderedDict
from qgis.core import *
from PyQt4.QtCore import QVariant


class Tables:

    pipes_table_name = 'pipes'
    junctions_table_name = 'junctions'
    reservoirs_table_name = 'reservoirs'
    tanks_table_name = 'tanks'
    pumps_table_name = 'pumps'
    valves_table_name = 'valves'

    def __init__(self):
        pass


class Title:
    section_name = 'TITLE'

    def __init__(self, title):
        self.title = title


class Junction:
    section_name = 'JUNCTIONS'
    section_header = 'ID               	Elev      	Demand    	Pattern'
    field_name_eid = 'id'
    field_name_demand = 'demand'
    field_name_elev = 'elev'
    field_name_elev_corr = 'elev_corr'
    field_name_pattern = 'pattern'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_elev, QVariant.Double),
              QgsField(field_name_elev_corr, QVariant.Double),
              QgsField(field_name_pattern, QVariant.String),
              QgsField(field_name_demand, QVariant.Double)]

    def __init__(self, eid):
        self.eid = eid
        self.demand = 0
        self.elevation = -1
        self.elev_corr = 0
        self.pattern = None
        self.emitter_coeff = 0


class Reservoir:
    section_name = 'RESERVOIRS'
    section_header = 'ID               	Head      	Pattern'
    field_name_eid = 'id'
    field_name_elev = 'elev'
    field_name_elev_corr = 'elev_corr'
    field_name_pattern = 'pattern'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_elev, QVariant.Double),
              QgsField(field_name_elev_corr, QVariant.Double)]

    def __init__(self, eid):
        self.eid = eid
        self.elevation = -1
        self.elevation_corr = 0
        self.head = 0
        self.pattern = 0


class Tank:
    section_name = 'TANKS'
    section_header = 'ID                	Elevation 	InitLevel 	MinLevel  	MaxLevel  	Diameter  	MinVol    	VolCurve'
    field_name_eid = 'id'
    field_name_curve = 'curve'
    field_name_diameter = 'diameter'
    field_name_elev = 'elev'
    field_name_elev_corr = 'elev_corr'
    field_name_level_init = 'init_level'
    field_name_level_max = 'max_level'
    field_name_level_min = 'min_level'
    field_name_vol_min = 'min_vol'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_elev, QVariant.Double),
              QgsField(field_name_elev_corr, QVariant.Double),
              QgsField(field_name_level_init, QVariant.Double),
              QgsField(field_name_level_min, QVariant.Double),
              QgsField(field_name_level_max, QVariant.Double),
              QgsField(field_name_diameter, QVariant.Double),
              QgsField(field_name_vol_min, QVariant.Double),
              QgsField(field_name_curve, QVariant.Double)]

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
    section_name = 'PIPES'
    section_header = 'ID                	Node1              	Node2              	Length             	Diameter           	Roughness          	MinorLoss          	Status'
    field_name_eid = 'id'
    field_name_diameter = 'diameter'
    field_name_length = 'length'
    field_name_minor_loss = 'minor_loss'
    field_name_roughness = 'roughness'
    field_name_status = 'status'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_length, QVariant.Double),
              QgsField(field_name_diameter, QVariant.Double),
              QgsField(field_name_status, QVariant.String),
              QgsField(field_name_roughness, QVariant.Double),
              QgsField(field_name_minor_loss, QVariant.Double)]

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
    section_name = 'PUMPS'
    section_header = 'ID              	Node1           	Node2           	Parameters'
    field_name_eid = 'id'
    field_name_power = 'power'
    field_name_head = 'head'
    field_name_pattern = 'pattern'
    field_name_speed = 'speed'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_head, QVariant.String),
              QgsField(field_name_power, QVariant.String),
              QgsField(field_name_speed, QVariant.String),
              QgsField(field_name_pattern, QVariant.String)]

    parameters_power = 'POWER'
    parameters_head = 'HEAD'

    def __init__(self, eid):
        self.eid = eid
        self.params = Pump.parameters_power
        self.value = 0


class Valve:
    section_name = 'VALVES'
    section_header = 'ID              	Node1           	Node2           	Diameter   	Type      	Setting   	MinorLoss'
    field_name_eid = 'id'
    field_name_diameter = 'diameter'
    field_name_minor_loss = 'minor_loss'
    field_name_setting = 'setting'
    field_name_type = 'type'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_diameter, QVariant.Double),
              QgsField(field_name_type, QVariant.String),
              QgsField(field_name_setting, QVariant.Double),
              QgsField(field_name_minor_loss, QVariant.Double)]

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


class Coordinate:
    section_name = 'COORDINATES'
    section_header = 'Node            	X-Coord         	Y-Coord'

    def __init__(self):
        pass


class Vertex:
    section_name = 'VERTICES'
    section_header = 'Link            	X-Coord         	Y-Coord'

    def __init__(self):
        pass


class Emitter:
    section_name = 'EMITTERS'

    def __init__(self):
        pass
