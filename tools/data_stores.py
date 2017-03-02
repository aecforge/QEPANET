import os

from PyQt4.QtCore import QVariant
from qgis.core import *

from exceptions import ShpExistsExcpetion
from ..model.network import *
from ..model.network import Tables


class MemoryDS:

    def __init__(self):
        pass

    # @staticmethod
    # def create_empty_memory_layers(crs):
    #
    #     junctions_lay = MemoryDS.create_junctions_lay(crs=crs)
    #     reservoirs_lay = MemoryDS.create_reservoirs_lay(crs=crs)
    #     tanks_lay = MemoryDS.create_tanks_lay(crs=crs)
    #     pipes_lay = MemoryDS.create_pipes_lay(crs=crs)
    #     pumps_lay = MemoryDS.create_pumps_lay(crs=crs)
    #     valves_lay = MemoryDS.create_valves_lay(crs=crs)
    #
    #     return {Junction.section_name: junctions_lay,
    #             Reservoir.section_name: reservoirs_lay,
    #             Tank.section_name: tanks_lay,
    #             Pipe.section_name: pipes_lay,
    #             Pump.section_name: pumps_lay,
    #             Valve.section_name: valves_lay}

    @staticmethod
    def create_junctions_lay(geoms=None, ids=None, demands=None, elevs=None, elev_corrs=None, patterns=None, crs=None):

        url = 'Point'
        if crs is not None:
            url += '?crs=' + crs.authid()

        junctions_lay = QgsVectorLayer(url, 'Junctions', 'memory')
        junctions_lay_dp = junctions_lay.dataProvider()
        junctions_lay_dp.addAttributes(Junction.fields)
        junctions_lay.updateFields()

        if geoms is not None:
            for n in range(len(geoms)):
                junctions_ft = QgsFeature()
                junctions_ft.setGeometry(geoms[n])
                junction_id = ids[n] if ids is not None else None
                demand = demands[n] if demands is not None else None
                elev = elevs[n] if elevs is not None else None
                elev_corr = elev_corrs[n] if elev_corrs is not None else None
                pattern = patterns[n] if patterns is not None else None
                # emitter = emitters[n] if emitters is not None else None

                junctions_ft.setAttribute(Junction.field_name_eid, junction_id)
                junctions_ft.setAttribute(Junction.field_name_elev, elev)
                junctions_ft.setAttribute(Junction.field_name_delta_z, elev_corr)
                junctions_ft.setAttribute(Junction.field_name_pattern, pattern)

                junctions_lay.addFeature(junctions_ft)

        return junctions_lay

    @staticmethod
    def create_reservoirs_lay(geoms=None, ids=None, elevs=None, elevs_corr=None, crs=None):

        url = 'Point'
        if crs is not None:
            url += '?crs=' + crs.authid()

        reservoirs_lay = QgsVectorLayer(url, 'Reservoirs', 'memory')
        reservoirs_lay_dp = reservoirs_lay.dataProvider()
        reservoirs_lay_dp.addAttributes(Reservoir.fields)
        reservoirs_lay.updateFields()

        if geoms is not None:
            for n in range(len(geoms)):
                reservoir_ft = QgsFeature()
                reservoir_ft.setGeometry(geoms[n])

                reservoir_id = ids[n] if ids is not None else None
                elev = elevs[n] if elevs is not None else None
                elev_corr = elevs_corr[n] if elevs_corr is not None else None

                reservoir_ft.setAttribute(Reservoir.field_name_eid, reservoir_id)
                reservoir_ft.setAttribute(Reservoir.field_name_elev, elev)
                reservoir_ft.setAttribute(Reservoir.field_name_delta_z, elev_corr)
                reservoirs_lay.addFeature(reservoir_ft)

        return reservoirs_lay

    @staticmethod
    def create_tanks_lay(geoms=None, ids=None, curves=None, diameters=None, elevs=None, elevs_corr=None,
                         levels_init=None, levels_max=None, levels_min=None, vols_min=None, crs=None):

        url = 'Point'
        if crs is not None:
            url += '?crs=' + crs.authid()

        tanks_lay = QgsVectorLayer(url, 'Tanks', 'memory')
        tanks_lay_dp = tanks_lay.dataProvider()
        tanks_lay_dp.addAttributes(Tank.fields)
        tanks_lay.updateFields()

        if geoms is not None:
            for n in range(len(geoms)):
                tanks_ft = QgsFeature()
                tanks_ft.setGeometry(geoms[n])

                tank_id = ids[n] if ids is not None else None
                curve = curves[n] if curves is not None else None
                diameter = diameters[n] if diameters is not None else None
                elev = elevs[n] if elevs is not None else None
                elev_corr = elevs_corr[n] if elevs_corr is not None else None
                level_init = levels_init[n] if levels_init is not None else None
                level_max = levels_max[n] if levels_max is not None else None
                level_min = levels_min[n] if levels_min is not None else None
                vol_min = vols_min[n] if vols_min is not None else None

                tanks_ft.setAttribute(Tank.field_name_eid, tank_id)
                tanks_ft.setAttribute(Tank.field_name_curve, curve)
                tanks_ft.setAttribute(Tank.field_name_diameter, diameter)
                tanks_ft.setAttribute(Tank.field_name_elev, elev)
                tanks_ft.setAttribute(Tank.field_name_delta_z, elev_corr)
                tanks_ft.setAttribute(Tank.field_name_level_init, level_init)
                tanks_ft.setAttribute(Tank.field_name_level_max, level_max)
                tanks_ft.setAttribute(Tank.field_name_level_min, level_min)
                tanks_ft.setAttribute(Tank.field_name_vol_min, vol_min)
                tanks_lay.addFeature(tanks_ft)

        return tanks_lay

    @staticmethod
    def create_pipes_lay(geoms=None, ids=None, demands=None, diameters=None, lengths=None, roughnesses=None,
                         statuses=None, minor_losses=None, crs=None):

        url = 'LineString'
        if crs is not None:
            url += '?crs=' + crs.authid()

        pipes_lay = QgsVectorLayer(url, 'Pipes', 'memory')
        pipes_lay_dp = pipes_lay.dataProvider()
        pipes_lay_dp.addAttributes(Pipe.fields)
        pipes_lay.updateFields()

        if geoms is not None:
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
    def create_pumps_lay(geoms=None, ids=None, head_curve_ids=None, powers=None, speeds=None, patterns=None, crs=None):

        url = 'LineString'
        if crs is not None:
            url += '?crs=' + crs.authid()

        pumps_lay = QgsVectorLayer(url, 'Pumps', 'memory')
        pumps_lay_dp = pumps_lay.dataProvider()
        pumps_lay_dp.addAttributes(Pump.fields)
        pumps_lay.updateFields()

        if geoms is not None:
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
    def create_valves_lay(geoms=None, ids=None, diameters=None, minor_losses=None, settings=None, types=None, crs=None):

        url = 'LineString'
        if crs is not None:
            url += '?crs=' + crs.authid()
        valves_lay = QgsVectorLayer(url, 'Valves', 'memory')
        valves_lay_dp = valves_lay.dataProvider()
        valves_lay_dp.addAttributes(Valve.fields)
        valves_lay.updateFields()

        if geoms is not None:
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

    @staticmethod
    def create_nodes_lay(params, field_name_var=u'variable', lay_name=u'Nodes', crs=None):

        url = 'Point'
        if crs is not None:
            url += '?crs=' + crs.authid()
        nodes_lay = QgsVectorLayer(url, lay_name, u'memory')
        nodes_lay_dp = nodes_lay.dataProvider()
        nodes_lay_dp.addAttributes([
            QgsField(Node.field_name_eid,  QVariant.String),
            QgsField(field_name_var, QVariant.Double)])
        nodes_lay.updateFields()

        new_fts = []
        for feat in params.junctions_vlay.getFeatures():
            new_ft = QgsFeature(nodes_lay.pendingFields())
            new_ft.setGeometry(feat.geometry())
            new_ft.setAttribute(Node.field_name_eid, feat.attribute(Junction.field_name_eid))
            new_fts.append(new_ft)

        for feat in params.reservoirs_vlay.getFeatures():
            new_ft = QgsFeature(nodes_lay.pendingFields())
            new_ft.setGeometry(feat.geometry())
            new_ft.setAttribute(Node.field_name_eid, feat.attribute(Reservoir.field_name_eid))
            new_fts.append(new_ft)

        for feat in params.tanks_vlay.getFeatures():
            new_ft = QgsFeature(nodes_lay.pendingFields())
            new_ft.setGeometry(feat.geometry())
            new_ft.setAttribute(Node.field_name_eid, feat.attribute(Tank.field_name_eid))
            new_fts.append(new_ft)

        nodes_lay_dp.addFeatures(new_fts)

        return nodes_lay

    @staticmethod
    def create_links_lay(params, field_name_var=u'variable', lay_name=u'Nodes', crs=None):

        url = 'LineString'
        if crs is not None:
            url += '?crs=' + crs.authid()
        links_lay = QgsVectorLayer(url, lay_name, u'memory')
        links_lay_dp = links_lay.dataProvider()
        links_lay_dp.addAttributes([
            QgsField(Node.field_name_eid,  QVariant.String),
            QgsField(field_name_var, QVariant.String)])
        links_lay.updateFields()

        new_fts = []
        for feat in params.pipes_vlay.getFeatures():
            new_ft = QgsFeature(links_lay.pendingFields())
            new_ft.setGeometry(feat.geometry())
            new_ft.setAttribute(Link.field_name_eid, feat.attribute(Pipe.field_name_eid))
            new_fts.append(new_ft)

        for feat in params.pumps_vlay.getFeatures():
            new_ft = QgsFeature(links_lay.pendingFields())
            new_ft.setGeometry(feat.geometry())
            new_ft.setAttribute(Link.field_name_eid, feat.attribute(Pump.field_name_eid))
            new_fts.append(new_ft)

        for feat in params.valves_vlay.getFeatures():
            new_ft = QgsFeature(links_lay.pendingFields())
            new_ft.setGeometry(feat.geometry())
            new_ft.setAttribute(Link.field_name_eid, feat.attribute(Valve.field_name_eid))
            new_fts.append(new_ft)

        links_lay_dp.addFeatures(new_fts)

        return links_lay


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
        fields.append(QgsField(Junction.field_name_delta_z, QVariant.Double))
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
        fields.append(QgsField(Reservoir.field_name_delta_z, QVariant.Double))
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
        fields.append(QgsField(Tank.field_name_delta_z, QVariant.Double))
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
        # fields.append(QgsField(QgsField(Pipe.field_name_demand, QVariant.Double)))
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