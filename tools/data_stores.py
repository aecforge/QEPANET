import os

from PyQt4.QtCore import QVariant
from qgis.core import *

from exceptions import ShpExistsExcpetion
from ..model.network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from ..model.network import Tables


class MemoryDS:

    def __init__(self):
        pass

    @staticmethod
    def create_empty_memory_layers():
        MemoryDS.create_junctions_lay()
        MemoryDS.create_reservoirs_lay()
        MemoryDS.create_tanks_lay()
        MemoryDS.create_pipes_lay()
        MemoryDS.create_pumps_lay()
        MemoryDS.create_valves_lay()

    @staticmethod
    def create_junctions_lay(geoms, ids, demands, elevs, elev_corrs, patterns, crs=None):

        junctions_lay = QgsVectorLayer('Point', 'Junctions', 'memory')
        junctions_lay.setCrs(crs)
        junctions_lay_dp = junctions_lay.dataProvider()
        junctions_lay_dp.addAttributes(Junction.fields)

        for n in range(len(geoms)):
            node_ft = QgsFeature()
            node_ft.setGeometry(geoms[n])
            junction_id = ids[n] if ids is not None else None
            demand = demands[n] if demands is not None else None
            elev = elevs[n] if elevs is not None else None
            elev_corr = elev_corrs[n] if elev_corrs is not None else None
            pattern = patterns[n] if patterns is not None else None
            # emitter = emitters[n] if emitters is not None else None

            node_ft.setAttribute(Junction.field_name_eid, junction_id)
            node_ft.setAttribute(Junction.field_name_demand, demand)
            node_ft.setAttribute(Junction.field_name_elev, elev)
            node_ft.setAttribute(Junction.field_name_elev_corr, elev_corr)
            node_ft.setAttribute(Junction.field_name_pattern, pattern)

            junctions_lay.addFeature(node_ft)

        return junctions_lay

    @staticmethod
    def create_reservoirs_lay(geoms, ids, elevs, elevs_corr, crs=None):

        reservoirs_lay = QgsVectorLayer('Point', 'Reservoirs', 'memory')
        reservoirs_lay.setCrs(crs)
        reservoirs_lay_dp = reservoirs_lay.dataProvider()
        reservoirs_lay_dp.addAttributes(Reservoir.fields)

        for n in range(len(geoms)):
            reservoir_ft = QgsFeature()
            reservoir_ft.setGeometry(geoms[n])

            reservoir_id = ids[n] if ids is not None else None
            elev = elevs[n] if elevs is not None else None
            elev_corr = elevs_corr[n] if elevs_corr is not None else None

            reservoir_ft.setAttribute(Reservoir.field_name_eid, reservoir_id)
            reservoir_ft.setAttribute(Reservoir.field_name_elev, elev)
            reservoir_ft.setAttribute(Reservoir.field_name_elev_corr, elev_corr)
            reservoirs_lay.addFeature(reservoir_ft)

        return reservoirs_lay

    @staticmethod
    def create_tanks_lay(geoms, ids, curves, diameters, elevs, elevs_corr, levels_init, levels_max, levels_min, vols_min, crs=None):

        tanks_lay = QgsVectorLayer('Point', 'Tanks', 'memory')
        tanks_lay.setCrs(crs)
        tanks_lay_dp = tanks_lay.dataProvider()
        tanks_lay_dp.addAttributes(Reservoir.fields)

        for n in range(len(geoms)):
            reservoir_ft = QgsFeature()
            reservoir_ft.setGeometry(geoms[n])

            tank_id = ids[n] if ids is not None else None
            curve = curves[n] if curves is not None else None
            diameter = diameters[n] if diameters is not None else None
            elev = elevs[n] if elevs is not None else None
            elev_corr = elevs_corr[n] if elevs_corr is not None else None
            level_init = levels_init[n] if levels_init is not None else None
            level_max = levels_max[n] if levels_max is not None else None
            level_min = levels_min[n] if levels_min is not None else None
            vol_min = vols_min[n] if vols_min is not None else None

            reservoir_ft.setAttribute(Tank.field_name_eid, tank_id)
            reservoir_ft.setAttribute(Tank.field_name_curve, curve)
            reservoir_ft.setAttribute(Tank.field_name_diameter, diameter)
            reservoir_ft.setAttribute(Tank.field_name_elev, elev)
            reservoir_ft.setAttribute(Tank.field_name_elev_corr, elev_corr)
            reservoir_ft.setAttribute(Tank.field_name_level_init, level_init)
            reservoir_ft.setAttribute(Tank.field_name_level_max, level_max)
            reservoir_ft.setAttribute(Tank.field_name_level_min, level_min)
            reservoir_ft.setAttribute(Tank.field_name_vol_min, vol_min)
            tanks_lay.addFeature(reservoir_ft)

        return tanks_lay

    @staticmethod
    def create_pipes_lay(geoms, ids, demands, diameters, lengths, roughnesses, statuses, minor_losses, crs=None):

        pipes_lay = QgsVectorLayer('LineString', 'Pipes', 'memory')
        pipes_lay.setCrs(crs)
        pipes_lay_dp = pipes_lay.dataProvider()
        pipes_lay_dp.addAttributes(Pipe.fields)

        for n in range(len(geoms)):
            pipe_ft = QgsFeature()
            pipe_ft.setGeometry(geoms[n])
            
            pipe_id = ids[n] if ids is not None else None
            demand = demands[n] if demands is not None else None
            diameter = diameters[n] if diameters is not None else None
            length = lengths[n] if lengths is not None else None
            roughness = roughnesses[n] if roughnesses is not None else None
            status = statuses[n] if statuses is not None else None
            minor_loss = minor_losses[n] if minor_losses is not None else None

            pipe_ft.setAttribute(Pipe.field_name_eid, pipe_id)
            pipe_ft.setAttribute(Pipe.field_name_diameter, diameter)
            pipe_ft.setAttribute(Pipe.field_name_length, length)
            pipe_ft.setAttribute(Pipe.field_name_roughness, roughness)
            pipe_ft.setAttribute(Pipe.field_name_status, status)
            pipe_ft.setAttribute(Pipe.field_name_minor_loss, minor_loss)
            pipes_lay.addFeature(pipe_ft)

        return pipes_lay

    @staticmethod
    def create_pumps_lay(geoms, ids, head_curve_ids, powers, speeds, patterns, crs=None):
        
        pumps_lay = QgsVectorLayer('LineString', 'Pumps', 'memory')
        pumps_lay.setCrs(crs)
        pumps_lay_dp = pumps_lay.dataProvider()
        pumps_lay_dp.addAttributes(Pump.fields)
        
        for n in range(len(geoms)):
            pump_ft = QgsFeature()
            pump_ft.setGeometry(geoms[n])

            pump_id = ids[n] if ids is not None else None
            head_curve_id = head_curve_ids[n] if head_curve_ids is not None else None
            power = powers[n] if powers is not None else None
            speed = speeds[n] if speeds is not None else None
            pattern = patterns[n] if patterns is not None else None

            pump_ft.setAttributes(Pump.field_name_eid, pump_id)
            pump_ft.setAttributes(Pump.field_name_head, head_curve_id)
            pump_ft.setAttributes(Pump.field_name_power, power)
            pump_ft.setAttributes(Pump.field_name_speed, speed)
            pump_ft.setAttributes(Pump.field_name_pattern, pattern)
            pumps_lay.addFeature(pump_ft)

        return pumps_lay

    @staticmethod
    def create_valves_lay(geoms, ids, diameters, minor_losses, settings, types, crs=None):
        
        valves_lay = QgsVectorLayer('LineString', 'Valves', 'memory')
        valves_lay.setCrs(crs)
        valves_lay_dp = valves_lay.dataProvider()
        valves_lay_dp.addAttributes(Valve.fields)
    
        for n in range(len(geoms)):
            valve_ft = QgsFeature()
            valve_ft.setGeometry(geoms[n])
    
            valve_id = ids[n] if ids is not None else None
            diameter = diameters[n] if diameters is not None else None
            minor_loss = minor_losses[n] if minor_losses is not None else None
            setting = settings[n] if settings is not None else None
            type = types[n] if types is not None else None
    
            valve_ft.setAttribute(Valve.field_name_eid, valve_id)
            valve_ft.setAttribute(Valve.field_name_diameter, diameter)
            valve_ft.setAttribute(Valve.field_name_minor_loss, minor_loss)
            valve_ft.setAttribute(Valve.field_name_setting, setting)
            valve_ft.setAttribute(Valve.field_name_type, type)
            valves_lay.addFeature(valve_ft)
    
        return valves_lay


class ShapefileDS:

    def __init__(self):
        pass

    @staticmethod
    def create_shapefiles(shp_folder, crs=None):

        junctions_shp_path = os.path.join(shp_folder, Tables.junctions_table_name + '.shp')
        if not os.path.isfile(junctions_shp_path):
            ShapefileDS.create_junctions_shp(junctions_shp_path, crs)
            junctions_exist = False
        else:
            junctions_exist = True

        reservoirs_shp_path = os.path.join(shp_folder, Tables.reservoirs_table_name + '.shp')
        if not os.path.isfile(reservoirs_shp_path):
            ShapefileDS.create_reservoirs_shp(reservoirs_shp_path, crs)
            reservoiors_exist = False
        else:
            reservoiors_exist = True

        tanks_shp_path = os.path.join(shp_folder, Tables.tanks_table_name + '.shp')
        if not os.path.isfile(tanks_shp_path):
            ShapefileDS.create_tanks_shp(tanks_shp_path, crs)
            tanks_exist = False
        else:
            tanks_exist = True

        pipes_shp_path = os.path.join(shp_folder, Tables.pipes_table_name + '.shp')
        if not os.path.isfile(pipes_shp_path):
            ShapefileDS.create_pipes_shp(pipes_shp_path, crs)
            pipes_exist = False
        else:
            pipes_exist = True

        pumps_shp_path = os.path.join(shp_folder, Tables.pumps_table_name + '.shp')
        if not os.path.isfile(pumps_shp_path):
            ShapefileDS.create_pumps_shp(pumps_shp_path, crs)
            pumps_exist = False
        else:
            pumps_exist = True

        valves_shp_path = os.path.join(shp_folder, Tables.valves_table_name + '.shp')
        if not os.path.isfile(valves_shp_path):
            ShapefileDS.create_valves_shp(valves_shp_path, crs)
            valves_exist = False
        else:
            valves_exist = True

        if junctions_exist or reservoiors_exist or tanks_exist or pipes_exist or pumps_exist or valves_exist:
            message = 'The following Shapefile(s) existed already: '
            if junctions_exist:
                message += ' junctions;'
            if reservoiors_exist:
                message += ' reservoirs;'
            if tanks_exist:
                message += ' tanks;'
            if pipes_exist:
                message += ' pipes;'
            if pumps_exist:
                message += ' pumps;'
            if valves_exist:
                message += ' valves;'
            raise ShpExistsExcpetion(message)

    @staticmethod
    def create_junctions_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Junction.field_name_eid, QVariant.String)))
        fields.append(QgsField(QgsField(Junction.field_name_demand, QVariant.Double)))
        fields.append(QgsField(Junction.field_name_elev, QVariant.Double))
        fields.append(QgsField(Junction.field_name_elev_corr, QVariant.Double))
        fields.append(QgsField(Junction.field_name_pattern, QVariant.String))
        fields.append(QgsField(Junction.field_name_emitter_coeff, QVariant.Double))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBPoint, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_reservoirs_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(Reservoir.field_name_eid, QVariant.String))
        fields.append(QgsField(Reservoir.field_name_elev, QVariant.Double))
        fields.append(QgsField(Reservoir.field_name_elev_corr, QVariant.Double))
        # fields.append(QgsField(Reservoir.field_name_head, QVariant.Double))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBPoint, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_tanks_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(Tank.field_name_eid, QVariant.String))
        fields.append(QgsField(Tank.field_name_curve, QVariant.Int))
        fields.append(QgsField(Tank.field_name_diameter, QVariant.Double))
        fields.append(QgsField(Tank.field_name_elev, QVariant.Double))
        fields.append(QgsField(Tank.field_name_elev_corr, QVariant.Double))
        fields.append(QgsField(Tank.field_name_level_init, QVariant.Double))
        fields.append(QgsField(Tank.field_name_level_max, QVariant.Double))
        fields.append(QgsField(Tank.field_name_level_min, QVariant.Double))
        fields.append(QgsField(Tank.field_name_vol_min, QVariant.Double))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBPoint, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_pipes_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Pipe.field_name_eid, QVariant.String)))
        fields.append(QgsField(QgsField(Pipe.field_name_demand, QVariant.Double)))
        fields.append(QgsField(QgsField(Pipe.field_name_diameter, QVariant.Double)))
        fields.append(QgsField(QgsField(Pipe.field_name_length, QVariant.Double)))
        fields.append(QgsField(QgsField(Pipe.field_name_roughness, QVariant.Double)))
        fields.append(QgsField(QgsField(Pipe.field_name_status, QVariant.String)))
        fields.append(QgsField(QgsField(Pipe.field_name_minor_loss, QVariant.Double)))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBLineString, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_pumps_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Pump.field_name_eid, QVariant.String)))
        # fields.append(QgsField(QgsField(Pump.field_name_from_node, QVariant.String)))
        # fields.append(QgsField(QgsField(Pump.field_name_to_node, QVariant.String)))
        fields.append(QgsField(QgsField(Pump.field_name_param, QVariant.String)))
        fields.append(QgsField(QgsField(Pump.field_name_value, QVariant.String)))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBLineString, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_valves_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Valve.field_name_eid, QVariant.String)))
        fields.append(QgsField(QgsField(Valve.field_name_diameter, QVariant.Double)))
        fields.append(QgsField(QgsField(Valve.field_name_minor_loss, QVariant.Double)))
        fields.append(QgsField(QgsField(Valve.field_name_setting, QVariant.Double)))
        fields.append(QgsField(QgsField(Valve.field_name_type, QVariant.String)))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBLineString, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())


class PostGISDS:

    def __init__(self):
        pass