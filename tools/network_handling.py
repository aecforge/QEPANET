from PyQt4.QtCore import QPyNullVariant

from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider
from ..network import Node, Pipe
from ..geo_utils.points_along_line import PointsAlongLineGenerator
from ..parameters import Parameters
from collections import OrderedDict
from ..geo_utils import raster_utils
import math


class NodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def create_new_node(nodes_vlay, node, eid, elev):

        nodes_caps = nodes_vlay.dataProvider().capabilities()
        if nodes_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            nodes_vlay.beginEditCommand("Add node")
            new_node_ft = QgsFeature(nodes_vlay.pendingFields())
            new_node_ft.setAttribute(Node.field_name_eid, eid)
            new_node_ft.setAttribute(Node.field_name_elevation, elev)
            new_node_ft.setGeometry(QgsGeometry.fromPoint(node))
            nodes_vlay.addFeatures([new_node_ft])
            nodes_vlay.endEditCommand()


class LinkHandler:

    @staticmethod
    def create_new_pipe(pipes_vlay, eid, demand, diameter, loss, roughness, status, nodes, dem_rlayer):

        pipes_caps = pipes_vlay.dataProvider().capabilities()
        if pipes_caps and QgsVectorDataProvider.AddFeatures:

            pipe_geom = QgsGeometry.fromPolyline(nodes)

            # Calculate 3D length
            length_3d = LinkHandler.calc_3d_length(pipe_geom)

            # Get end_node and start_node

            # pipes_vlay.beginEditCommand("Add new pipes")
            # new_pipe_ft_1 = QgsFeature(pipes_vlay.pendingFields())
            # new_pipe_ft_1.setAttribute(Pipe.field_name_eid, eid)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_demand, demand)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_diameter, diameter)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_end_node, end_node)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_length, length)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_loss, loss)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_roughness, roughness)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_start_node, start_node)
            # new_pipe_ft_1.setAttribute(Pipe.field_name_status, status)
            # new_pipe_ft_1.setGeometry(ls_geom)
            # pipes_vlay.endEditCommand()

    @staticmethod
    def calc_3d_length(pipe_geom):

        # Check whether start and end node exist
        (start_node_ft, end_node_ft) = NetworkUtils.get_start_end_nodes(pipe_geom)

        distance_elev_od = OrderedDict()

        start_add = 0
        if start_node_ft is not None:
            start_node_elev = start_node_ft.attribute(Node.field_name_elevation)
            if type(start_node_elev) is QPyNullVariant:
                start_node_elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, start_node_ft.geometry().asPoint(), 0)
            start_node_depth = start_node_ft.attribute(Node.field_name_depth)
            if type(start_node_depth) is QPyNullVariant:
                start_node_depth = 0
            start_add = 1

        end_remove = 0
        if end_node_ft is not None:
            end_node_elev = end_node_ft.attribute(Node.field_name_elevation)
            if type(end_node_elev) is QPyNullVariant:
                end_node_elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, end_node_ft.geometry().asPoint(), 0)
            end_node_depth = end_node_ft.attribute(Node.field_name_depth)
            if type(end_node_depth) is QPyNullVariant:
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
        nodes_vlay = Parameters.nodes_vlay # TODO: add other point layers
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