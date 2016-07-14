import os
from PyQt4.QtCore import QVariant
from qgis.core import QgsVectorLayer, QgsField, QgsCoordinateReferenceSystem, QgsFields, QgsVectorFileWriter, QGis
from network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from network import Tables
from exceptions import ShpExistsExcpetion


class ShapefileDS:

    def __init__(self):
        pass

    @staticmethod
    def create_shapefiles(shp_folder, crs=None):

        junctions_shp_path = os.path.join(shp_folder, Tables.junctions_table_name + '.shp')
        if not os.path.isfile(junctions_shp_path):
            ShapefileDS.create_junctions_shp(junctions_shp_path, crs)
        else:
            junctions_exist = True

        reservoirs_shp_path = os.path.join(shp_folder, Tables.reservoirs_table_name + '.shp')
        if not os.path.isfile(reservoirs_shp_path):
            ShapefileDS.create_reservoirs_shp(reservoirs_shp_path, crs)
        else:
            reservoiors_exist = True

        tanks_shp_path = os.path.join(shp_folder, Tables.tanks_table_name + '.shp')
        if not os.path.isfile(tanks_shp_path):
            ShapefileDS.create_tanks_shp(tanks_shp_path, crs)
        else:
            tanks_exist = True

        pipes_shp_path = os.path.join(shp_folder, Tables.pipes_table_name + '.shp')
        if not os.path.isfile(pipes_shp_path):
            ShapefileDS.create_pipes_shp(pipes_shp_path, crs)
        else:
            pipes_exist = True

        pumps_shp_path = os.path.join(shp_folder, Tables.pumps_table_name + '.shp')
        if not os.path.isfile(pumps_shp_path):
            ShapefileDS.create_pumps_shp(pumps_shp_path, crs)
        else:
            pumps_exist = True

        valves_shp_path = os.path.join(shp_folder, Tables.valves_table_name + '.shp')
        if not os.path.isfile(valves_shp_path):
            ShapefileDS.create_valves_shp(valves_shp_path, crs)
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
        fields.append(QgsField(Junction.field_name_depth, QVariant.Double))
        fields.append(QgsField(Junction.field_name_elevation, QVariant.Double))
        fields.append(QgsField(Junction.field_name_pattern, QVariant.Int))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBPoint, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_reservoirs_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Reservoir.field_name_eid, QVariant.String)))
        # TODO: complete fields

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBPoint, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_tanks_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Tank.field_name_eid, QVariant.String)))
        # TODO: Complete fields

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
        fields.append(QgsField(QgsField(Pipe.field_name_roughness, QVariant.Int)))
        fields.append(QgsField(QgsField(Pipe.field_name_status, QVariant.String)))
        fields.append(QgsField(QgsField(Pipe.field_name_minor_loss, QVariant.Int)))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBLineString, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_pumps_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Pump.field_name_eid, QVariant.String)))
        fields.append(QgsField(QgsField(Pump.field_name_curve, QVariant.Int)))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBLineString, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())

    @staticmethod
    def create_valves_shp(shp_file_path, crs=None):

        fields = QgsFields()
        fields.append(QgsField(QgsField(Valve.field_name_eid, QVariant.String)))

        writer = QgsVectorFileWriter(shp_file_path, "CP1250", fields, QGis.WKBLineString, crs, "ESRI Shapefile")
        if writer.hasError() != QgsVectorFileWriter.NoError:
            raise Exception(writer.errorMessage())


class PostGISDS:

    def __init__(self):
        pass