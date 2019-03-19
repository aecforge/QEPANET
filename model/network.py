from collections import OrderedDict
from qgis.core import QgsField
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


class Node:

    field_name_eid = 'id'
    field_name_var = 'variable'

    fields = [QgsField(field_name_eid,  QVariant.String),
              QgsField(field_name_var, QVariant.String)]

    def __init__(self, eid):
        self.eid = eid


class Junction:
    section_name = 'JUNCTIONS'
    section_header = 'ID               	Elev      	Demand    	Pattern'
    field_name_eid = 'id'
    field_name_demand = 'demand'
    field_name_elev = 'elev_dem'
    field_name_delta_z = 'delta_z'
    field_name_pattern = 'pattern'
    field_name_emitter_coeff = 'emit_coeff'
    field_name_description = 'description'
    field_name_tag = 'tag'

    prefix = 'J'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_elev, QVariant.Double),
              QgsField(field_name_delta_z, QVariant.Double),
              QgsField(field_name_pattern, QVariant.String),
              QgsField(field_name_demand, QVariant.Double),
              QgsField(field_name_emitter_coeff, QVariant.Double),
              QgsField(field_name_description, QVariant.String),
              QgsField(field_name_tag, QVariant.String)]

    def __init__(self, eid):
        self.eid = eid
        self.demand = 0
        self.elevation = -1
        self.deltaz = 0
        self.pattern = None
        self.emitter_coeff = 0
        self.description = ''
        self.tag = ''

class QJunction:
    section_name = 'QEPANET-JUNCTIONS'
    section_header = 'ID               	DeltaZ'
    field_name_eid = 'id'
    field_name_delta_z = 'delta_z'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_delta_z, QVariant.Double)]


class Reservoir:
    section_name = 'RESERVOIRS'
    section_header = 'ID               	Head      	Pattern'
    field_name_eid = 'id'
    field_name_elev = 'elev_dem'
    field_name_delta_z = 'delta_z'
    field_name_pressure_head = 'press_head'
    field_name_pattern = 'pattern'
    field_name_description = 'description'
    field_name_tag = 'tag'

    prefix = 'R'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_elev, QVariant.Double),
              QgsField(field_name_delta_z, QVariant.Double),
              QgsField(field_name_pressure_head, QVariant.Double),
              QgsField(field_name_pattern, QVariant.String),
              QgsField(field_name_description, QVariant.String),
              QgsField(field_name_tag, QVariant.String)]

    def __init__(self, eid):
        self.eid = eid
        self.elevation = -1
        self.elevation_corr = 0
        self.field_name_pressure_head = 0
        self.pattern = None
        self.description = ''
        self.tag = ''


class Status:
    section_name = 'STATUS'

    def __init__(self):
        pass


class Tank:
    section_name = 'TANKS'
    section_header = 'ID                	Elevation 	InitLevel 	MinLevel  	MaxLevel  	Diameter  	MinVol    	VolCurve'
    field_name_eid = 'id'
    field_name_curve = 'curve'
    field_name_diameter = 'diameter'
    field_name_elev = 'elev_dem'
    field_name_delta_z = 'delta_z'
    field_name_level_init = 'init_level'
    field_name_level_max = 'max_level'
    field_name_level_min = 'min_level'
    field_name_vol_min = 'min_vol'
    field_name_description = 'description'
    field_name_tag = 'tag'

    prefix = 'T'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_elev, QVariant.Double),
              QgsField(field_name_delta_z, QVariant.Double),
              QgsField(field_name_level_init, QVariant.Double),
              QgsField(field_name_level_min, QVariant.Double),
              QgsField(field_name_level_max, QVariant.Double),
              QgsField(field_name_diameter, QVariant.Double),
              QgsField(field_name_vol_min, QVariant.Double),
              QgsField(field_name_curve, QVariant.String),
              QgsField(field_name_description, QVariant.String),
              QgsField(field_name_tag, QVariant.String)]

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
        self.description = ''
        self.tag = ''


class Link:
    field_name_eid = 'id'
    field_name_var = 'variable'

    fields = [QgsField(field_name_eid),
              QgsField(field_name_var, QVariant.String)]

    def __init__(self, eid):
        self.eid = eid


class Pipe:
    section_name = 'PIPES'
    section_header = 'ID                	Node1              	Node2              	Length             	Diameter           	Roughness          	MinorLoss          	Status'
    field_name_eid = 'id'
    field_name_diameter = 'diameter'
    field_name_length = 'length'
    field_name_minor_loss = 'minor_loss'
    field_name_roughness = 'roughness'
    field_name_status = 'status'
    field_name_material = 'material'
    field_name_description = 'description'
    field_name_tag = 'tag'

    prefix = 'L'  # L to distinguish it from Pumps

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_length, QVariant.Double),
              QgsField(field_name_diameter, QVariant.Double),
              QgsField(field_name_status, QVariant.String),
              QgsField(field_name_roughness, QVariant.Double),
              QgsField(field_name_minor_loss, QVariant.Double),
              QgsField(field_name_material, QVariant.String),
              QgsField(field_name_description, QVariant.String),
              QgsField(field_name_tag, QVariant.String)]

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
        self.material = 'none'
        self.description = ''
        self.tag = ''


class Pump:
    section_name = 'PUMPS'
    section_header = 'ID              	Node1           	Node2           	Parameters'
    field_name_eid = 'id'
    field_name_param = 'param'
    field_name_head = 'head'
    field_name_power = 'power'
    field_name_speed = 'speed'
    field_name_speed_pattern = 'speed_patt'
    field_name_status = 'status'
    field_name_description = 'description'
    field_name_tag = 'tag'

    prefix = 'P'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_param, QVariant.String),
              QgsField(field_name_head, QVariant.String),
              QgsField(field_name_power, QVariant.Double),
              QgsField(field_name_speed, QVariant.Double),
              QgsField(field_name_speed_pattern, QVariant.String),
              QgsField(field_name_status, QVariant.String),
              QgsField(field_name_description, QVariant.String),
              QgsField(field_name_tag, QVariant.String)]

    parameters_power = 'POWER'
    parameters_head = 'HEAD'

    status_closed = 'CLOSED'
    status_open = 'OPEN'

    def __init__(self, eid):
        self.eid = eid
        self.params = Pump.parameters_power
        self.value = 0
        self.description = ''
        self.tag = ''

class Valve:
    section_name = 'VALVES'
    section_header = 'ID              	Node1           	Node2           	Diameter   	Type      	Setting   	MinorLoss'
    field_name_eid = 'id'
    field_name_diameter = 'diameter'
    field_name_minor_loss = 'minor_loss'
    field_name_setting = 'setting'
    field_name_type = 'type'
    field_name_status = 'status'
    field_name_description = 'description'
    field_name_tag = 'tag'

    prefix = 'V'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_diameter, QVariant.Double),
              QgsField(field_name_type, QVariant.String),
              QgsField(field_name_setting, QVariant.String),
              QgsField(field_name_minor_loss, QVariant.Double),
              QgsField(field_name_status, QVariant.String),
              QgsField(field_name_description, QVariant.String),
              QgsField(field_name_tag, QVariant.String)]

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

    status_none = 'NONE'
    status_open = 'OPEN'
    status_closed = 'CLOSED'

    def __init__(self, eid):
        self.eid = eid
        self.description = ''
        self.tag = ''

class QReservoir:
    section_name = 'QEPANET-RESERVOIRS'
    section_header = 'ID               	DeltaZ             PressureHead'
    field_name_eid = 'id'
    field_name_delta_z = 'delta_z'
    field_name_pressure_head = 'press_head'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_delta_z, QVariant.Double),
              QgsField(field_name_pressure_head, QVariant.Double)]


class QTank:
    section_name = 'QEPANET-TANKS'
    section_header = 'ID               	DeltaZ'
    field_name_eid = 'id'
    field_name_delta_z = 'delta_z'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_delta_z, QVariant.Double)]


class QPipe:
    section_name = 'QEPANET-PIPES'
    section_header = 'ID               	Material'
    field_name_eid = 'id'
    field_name_material = 'material'

    fields = [QgsField(field_name_eid, QVariant.String),
              QgsField(field_name_material, QVariant.String)]


class QVertices:
    section_name = 'QEPANET-VERTICES'
    section_header = ';Link            	Z-Coord'


class QOptions:
    section_name = 'QOPTIONS'


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
    section_header = 'Junction        	Coefficient'

    def __init__(self):
        pass


class Tag:
    section_name = 'TAGS'
    element_type_node = 'NODE'
    element_type_link = 'LINK'

    def __init__(self, element_type, element_id, tag):
        self.element_type = element_type
        self.element_id = element_id
        self.tag = tag

class Demand:
    section_name = 'DEMANDS'

    def __init__(self):
        pass

class Control:
    section_name = 'CONTROLS'

    def __init__(self):
        pass

class Label:
    section_name = 'LABELS'

    def __init__(self):
        pass


class Source:
    section_name = 'SOURCE'

    def __init__(self):
        pass


class Reaction:
    section_name = 'REACTION'

    def __init__(self):
        pass


class Mixing:
    section_name = 'MIXING'

    def __init__(self):
        pass


class Backdrop:
    section_name = 'BACKDROP'

    def __init__(self):
        pass