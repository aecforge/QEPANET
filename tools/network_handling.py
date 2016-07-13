import math
from collections import OrderedDict

from PyQt4.QtCore import QPyNullVariant
from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsSnapper, QgsProject, QgsTolerance, QgsPoint

from network import Junction, Pipe, Pump
from ..geo_utils import raster_utils
from ..geo_utils.points_along_line import PointsAlongLineGenerator, PointsAlongLineUtils
from ..parameters import Parameters


class NodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def create_new_junction(junctions_vlay, point, eid, elev, demand, depth, pattern):

        nodes_caps = junctions_vlay.dataProvider().capabilities()
        if nodes_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            junctions_vlay.beginEditCommand("Add junction")

            new_junct_feat = QgsFeature(junctions_vlay.pendingFields())
            new_junct_feat.setAttribute(Junction.field_name_eid, eid)
            new_junct_feat.setAttribute(Junction.field_name_elevation, elev)
            new_junct_feat.setAttribute(Junction.field_name_demand, demand)
            new_junct_feat.setAttribute(Junction.field_name_depth, depth)
            new_junct_feat.setAttribute(Junction.field_name_pattern, pattern)

            new_junct_feat.setGeometry(QgsGeometry.fromPoint(point))

            junctions_vlay.addFeatures([new_junct_feat])

            junctions_vlay.endEditCommand()

            return new_junct_feat


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

            return new_pipe_ft

    @staticmethod
    def create_new_pump(pipe_ft, pumps_vlay, nodes_vlay, closest_junction_ft, position, pump_curve):

        # Find start and end nodes positions
        # Get vertex along line next to snapped point
        a, b, next_vertex = pipe_ft.geometry().closestSegmentWithContext(position)

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(position))
        dist_before = dist - 0.5 # TODO: softcode based on projection units
        if dist_before <= 0:
            dist_before = 1
        dist_after = dist + 0.5 # TODO: softcode based on projection units
        if dist_after > pipe_ft.geometry().length():
            dist_after = pipe_ft.geometry().length() - 1

        if dist_before >= dist_after:
            raise Exception('The pipe is too short for a pump to be placed on it.')

        node_before = pipe_ft.geometry().interpolate(dist_before).asPoint()
        node_after = pipe_ft.geometry().interpolate(dist_after).asPoint()

        # Create two new nodes
        junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J')  # TODO: softcode

        pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()
        junctions_caps = Parameters.junctions_vlay.dataProvider().capabilities()
        pumps_caps = Parameters.pumps_vlay.dataProvider().capabilities()

        if junctions_caps:
            j_demand = closest_junction_ft.attribute(Junction.field_name_demand)
            depth = closest_junction_ft.attribute(Junction.field_name_depth)
            pattern = closest_junction_ft.attribute(Junction.field_name_pattern)

            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, node_before, 1)
            NodeHandler.create_new_junction(Parameters.junctions_vlay, node_before, junction_eid, elev, j_demand, depth, pattern)

            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, node_after, 1)
            NodeHandler.create_new_junction(Parameters.junctions_vlay, node_after, junction_eid, elev, j_demand, depth, pattern)

        # Split the pipe and create gap
        if pipes_caps:
            gap = 1 # TODO: softcode pump length
            LinkHandler.split_pipe(pipe_ft, position, gap)

        # Create the new link (the pipe)
        if pumps_caps:

            pump_eid = NetworkUtils.find_next_id(Parameters.pumps_vlay, 'P')  # TODO: softcode
            pump_geom = QgsGeometry.fromPolyline([node_before, node_after])

            pumps_vlay.beginEditCommand("Add new pump")

            new_pump_ft = QgsFeature(pumps_vlay.pendingFields())
            new_pump_ft.setAttribute(Pump.field_name_eid, pump_eid)
            new_pump_ft.setAttribute(Pump.field_name_curve, pump_curve)

            new_pump_ft.setGeometry(pump_geom)

            pumps_vlay.addFeatures([new_pump_ft])

            pumps_vlay.endEditCommand()

            return new_pump_ft

    @staticmethod
    def split_pipe(pipe_ft, split_point, gap=0):

        # Get vertex along line next to snapped point
        a, b, next_vertex = pipe_ft.geometry().closestSegmentWithContext(split_point)

        # Split only if vertex is not at line ends
        demand = pipe_ft.attribute(Pipe.field_name_demand)
        p_diameter = pipe_ft.attribute(Pipe.field_name_diameter)
        loss = pipe_ft.attribute(Pipe.field_name_loss)
        roughness = pipe_ft.attribute(Pipe.field_name_roughness)
        status = pipe_ft.attribute(Pipe.field_name_status)

        # Create two new linestrings
        pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(split_point))
        dist_before = dist - 0.5 * gap
        if dist_before <= 0:
            dist_before = gap
        dist_after = dist + 0.5  * gap
        if dist_after > pipe_ft.geometry().length():
            dist_after = pipe_ft.geometry().length() - gap

        if dist_before >= dist_after:
            raise Exception('Exception caught in splitting pipe.'
                            'Pipe is too short.')

        node_before = pipe_ft.geometry().interpolate(dist_before)
        node_after = pipe_ft.geometry().interpolate(dist_after)

        if pipes_caps:

            Parameters.junctions_vlay.beginEditCommand("Add new node")
            nodes = pipe_ft.geometry().asPolyline()

            # First new polyline
            pl1_pts = []
            for n in range(next_vertex):
                pl1_pts.append(QgsPoint(nodes[n].x(), nodes[n].y()))

            pl1_pts.append(node_before.asPoint())

            pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'P')  # TODO: softcode
            pipe_ft_1 = LinkHandler.create_new_pipe(Parameters.pipes_vlay, pipe_eid, demand, p_diameter, loss, roughness, status, pl1_pts)

            # Second new polyline
            pl2_pts = []
            pl2_pts.append(node_after.asPoint())
            for n in range(len(nodes) - next_vertex):
                pl2_pts.append(QgsPoint(nodes[n + next_vertex].x(), nodes[n + next_vertex].y()))

            pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'P')  # TODO: softcode
            pipe_ft_2 = LinkHandler.create_new_pipe(Parameters.pipes_vlay, pipe_eid, demand, p_diameter, loss, roughness, status, pl2_pts)

            # Delete old pipe
            Parameters.pipes_vlay.deleteFeature(pipe_ft.id())

            Parameters.pipes_vlay.endEditCommand()

            return [pipe_ft_1, pipe_ft_2]

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
                if start_node_elev is None:
                    start_node_elev = 0

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
                if end_node_elev is None:
                    end_node_elev = 0
            end_node_depth = end_node_ft.attribute(Junction.field_name_depth)
            if end_node_depth is None or type(end_node_depth) is QPyNullVariant:
                end_node_depth = 0
            end_remove = 1

        point_gen = PointsAlongLineGenerator(pipe_geom)
        dists_and_points = point_gen.get_points_coords(100, False)  # TODO: Softcode the interval between points

        if start_node_ft is not None:
            distance_elev_od[0] = start_node_elev - start_node_depth

        for p in range(start_add, len(dists_and_points) - end_remove):
            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, dists_and_points.values()[p].asPoint(), 1)
            if elev is None:
                elev = 0
            distance_elev_od[dists_and_points.keys()[p]] = elev

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

    @staticmethod
    def find_start_end_nodes(link_geom):
        junctions_fts = Parameters.junctions_vlay.getFeatures()

        cands = []
        for junction_ft in junctions_fts:
            if link_geom.boundingBox().contains(junction_ft.geometry().asPoint()):
                cands.append(junction_ft)

        intersecting = []
        if cands:
            for junction_ft in cands:
                if junction_ft.geometry().distance(QgsGeometry.fromPoint(link_geom.asPolyline()[0])) < Parameters.tolerance:
                    intersecting.append(junction_ft)
                if junction_ft.geometry().distance(QgsGeometry.fromPoint(link_geom.asPolyline()[len(link_geom.asPolyline()) - 1])) < Parameters.tolerance:
                    intersecting.append(junction_ft)

        return intersecting

