from PyQt4.QtCore import QPyNullVariant

from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsSnapper, QgsProject, QgsTolerance
from qgis.gui import QgsMessageBar
from ..network import Junction, Pipe
from ..geo_utils.points_along_line import PointsAlongLineGenerator
from ..parameters import Parameters
from collections import OrderedDict
from ..geo_utils import raster_utils
import math


class NodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def create_new_junction(junctions_vlay, node, eid, elev, demand, depth, pattern):

        nodes_caps = junctions_vlay.dataProvider().capabilities()
        if nodes_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            junctions_vlay.beginEditCommand("Add node")
            new_junct_feat = QgsFeature(junctions_vlay.pendingFields())
            new_junct_feat.setAttribute(Junction.field_name_eid, eid)
            new_junct_feat.setAttribute(Junction.field_name_elevation, elev)
            new_junct_feat.setAttribute(Junction.field_name_demand, demand)
            new_junct_feat.setAttribute(Junction.field_name_depth, depth)
            new_junct_feat.setAttribute(Junction.field_name_pattern, pattern)
            new_junct_feat.setGeometry(QgsGeometry.fromPoint(node))
            junctions_vlay.addFeatures([new_junct_feat])
            junctions_vlay.endEditCommand()


class LinkHandler:
    def __init__(self):
        pass

    @staticmethod
    def create_new_pipe(pipes_vlay, eid, demand, diameter, loss, roughness, status, nodes):

        pipes_caps = pipes_vlay.dataProvider().capabilities()
        if pipes_caps and QgsVectorDataProvider.AddFeatures:

            pipe_geom = QgsGeometry.fromPolyline(nodes)

            # Calculate 3D length
            length_3d = LinkHandler.calc_3d_length(pipe_geom)

            pipes_vlay.beginEditCommand("Add new pipes")
            new_pipe_ft = QgsFeature(pipes_vlay.pendingFields())
            new_pipe_ft.setAttribute(Pipe.field_name_eid, eid)
            new_pipe_ft.setAttribute(Pipe.field_name_demand, demand)
            new_pipe_ft.setAttribute(Pipe.field_name_diameter, diameter)
            new_pipe_ft.setAttribute(Pipe.field_name_length, length_3d)
            new_pipe_ft.setAttribute(Pipe.field_name_loss, loss)
            new_pipe_ft.setAttribute(Pipe.field_name_roughness, roughness)
            new_pipe_ft.setAttribute(Pipe.field_name_status, status)
            new_pipe_ft.setGeometry(pipe_geom)

            pipes_vlay.addFeatures([new_pipe_ft])

            pipes_vlay.endEditCommand()

    @staticmethod
    def calc_3d_length(pipe_geom):

        # Check whether start and end node exist
        (start_node_ft, end_node_ft) = NetworkUtils.get_start_end_nodes(pipe_geom)

        distance_elev_od = OrderedDict()

        # Start node
        start_add = 0
        if start_node_ft is not None:
            start_node_elev = start_node_ft.attribute(Junction.field_name_elevation)
            if start_node_elev is None or type(start_node_elev) is QPyNullVariant:
                start_node_elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, start_node_ft.geometry().asPoint(), 0)
            start_node_depth = start_node_ft.attribute(Junction.field_name_depth)
            if start_node_depth is None or type(start_node_depth) is QPyNullVariant:
                start_node_depth = 0
            start_add = 1

        # End node
        end_remove = 0
        if end_node_ft is not None:
            end_node_elev = end_node_ft.attribute(Junction.field_name_elevation)
            if end_node_elev is None or type(end_node_elev) is QPyNullVariant:
                end_node_elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, end_node_ft.geometry().asPoint(), 0)
            end_node_depth = end_node_ft.attribute(Junction.field_name_depth)
            if end_node_depth is None or type(end_node_depth) is QPyNullVariant:
                end_node_depth = 0
            end_remove = 1

        point_gen = PointsAlongLineGenerator(pipe_geom)
        dists_and_points = point_gen.get_points_coords(100, False)  # TODO: Softcode

        # TODO: calc depth for intermediate points

        if start_node_ft is not None:
            distance_elev_od[0] = start_node_elev - start_node_depth

        for p in range(start_add, len(dists_and_points) - end_remove):
            distance_elev_od[dists_and_points.keys()[p]] = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, dists_and_points.values()[p].asPoint(), 1)

        if end_node_ft is not None:
            distance_elev_od[pipe_geom.length()] = end_node_elev - end_node_depth

        # Calculate 3D length
        length_3d = 0
        for p in range(1, len(distance_elev_od)):
            run = distance_elev_od.keys()[p] - distance_elev_od.keys()[p-1]
            rise = distance_elev_od.values()[p] - distance_elev_od.values()[p-1]

            length_3d += math.sqrt(run**2 + rise**2)

        return length_3d


class NetworkUtils:
    def __init__(self):
        pass

    @staticmethod
    def get_start_end_nodes(link_geom):
        link_vertices = link_geom.asPolyline()

        start_node_ft = None
        end_node_ft = None

        # Search among nodes
        nodes_vlay = Parameters.junctions_vlay # TODO: add other point layers
        nodes_feats = nodes_vlay.getFeatures()
        if nodes_feats is None == 0:
            return [None, None]

        for node_feat in nodes_feats:
            node_geom = node_feat.geometry()
            node_vertex = node_geom.asPoint()
            if node_geom.distance(QgsGeometry.fromPoint(link_vertices[0])) == 0:  # TODO: add tolerance
                start_node_ft = node_feat
            if node_geom.distance(QgsGeometry.fromPoint(link_vertices[len(link_vertices) - 1])):  # TODO: Add tolerance
                end_node_ft = node_feat

        return (start_node_ft, end_node_ft)

        # Search among reservoirs
        # TODO

        # Search among sources
        # TODO

    @staticmethod
    def find_next_id(vlay, prefix):
        features = vlay.getFeatures()
        max_eid = -1
        for feat in features:
            eid = feat.attribute(Junction.field_name_eid)
            eid_val = int(eid[len(prefix):len(eid)])
            max_eid = max(max_eid, eid_val)

        max_eid += 1
        max_eid = max(max_eid, 1)
        return prefix + str(max_eid)

    @staticmethod
    def set_up_snap_layer(vlayer, tolerance=None, snapping_type=QgsSnapper.SnapToVertex):

        snap_layer = QgsSnapper.SnapLayer()
        snap_layer.mLayer = vlayer

        if tolerance is None or tolerance < 0:
            (a, b, c, d, tolerance, f) = QgsProject.instance().snapSettingsForLayer(vlayer.id())
            snap_layer.mTolerance = tolerance
        else:
            snap_layer.mTolerance = tolerance

        snap_layer.mUnitType = QgsTolerance.MapUnits
        snap_layer.mSnapTo = snapping_type
        return snap_layer

    @staticmethod
    def set_up_snapper(snap_layers, map_canvas):
        snapper = QgsSnapper(map_canvas.mapSettings())
        snapper.setSnapLayers(snap_layers)
        snapper.setSnapMode(QgsSnapper.SnapWithOneResult)
        return snapper
