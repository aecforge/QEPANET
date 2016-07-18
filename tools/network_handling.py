import math
from collections import OrderedDict

from PyQt4.QtCore import QPyNullVariant
from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsSnapper, QgsProject, QgsTolerance, QgsPoint,\
    QgsVectorLayerEditUtils

from network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from parameters import Parameters
from ..geo_utils import raster_utils
from ..geo_utils.points_along_line import PointsAlongLineGenerator, PointsAlongLineUtils


class NodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def create_new_junction(point, eid, elev, demand, depth, pattern_id):

        junctions_caps = Parameters.junctions_vlay.dataProvider().capabilities()
        if junctions_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            Parameters.junctions_vlay.beginEditCommand("Add junction")
            new_junct_feat = None

            try:
                new_junct_feat = QgsFeature(Parameters.junctions_vlay.pendingFields())
                new_junct_feat.setAttribute(Junction.field_name_eid, eid)
                new_junct_feat.setAttribute(Junction.field_name_elevation, elev)
                new_junct_feat.setAttribute(Junction.field_name_demand, demand)
                new_junct_feat.setAttribute(Junction.field_name_depth, depth)
                new_junct_feat.setAttribute(Junction.field_name_pattern, pattern_id)

                new_junct_feat.setGeometry(QgsGeometry.fromPoint(point))

                Parameters.junctions_vlay.addFeatures([new_junct_feat])

            except Exception:
                Parameters.junctions_vlay.destroyEditCommand()

            Parameters.junctions_vlay.endEditCommand()

            return new_junct_feat

    @staticmethod
    def create_new_reservoir(point, eid, elev, elev_corr, pressure):

        reservoirs_caps = Parameters.reservoirs_vlay.dataProvider().capabilities()
        if reservoirs_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            Parameters.reservoirs_vlay.beginEditCommand("Add reservoir")
            new_reservoir_feat = None

            try:
                new_reservoir_feat = QgsFeature(Parameters.reservoirs_vlay.pendingFields())
                new_reservoir_feat.setAttribute(Reservoir.field_name_eid, eid)
                new_reservoir_feat.setAttribute(Reservoir.field_name_elevation, elev)
                new_reservoir_feat.setAttribute(Reservoir.field_name_elevation_corr, elev_corr)
                new_reservoir_feat.setAttribute(Reservoir.field_name_pressure, pressure)

                new_reservoir_feat.setGeometry(QgsGeometry.fromPoint(point))

                Parameters.reservoirs_vlay.addFeatures([new_reservoir_feat])

            except Exception:
                Parameters.reservoirs_vlay.destroyEditCommand()

            Parameters.reservoirs_vlay.endEditCommand()

            return new_reservoir_feat

    @staticmethod
    def create_new_tank(point, eid, curve, diameter, elev, elev_corr, level_init, level_min, level_max, vol_min):
        tanks_caps = Parameters.tanks_vlay.dataProvider().capabilities()
        if tanks_caps and QgsVectorDataProvider.AddFeatures:

            Parameters.tanks_vlay.beginEditCommand("Add junction")
            new_tank_feat = None

            try:
                new_tank_feat = QgsFeature(Parameters.tanks_vlay.pendingFields())

                new_tank_feat.setAttribute(Tank.field_name_eid, eid)
                new_tank_feat.setAttribute(Tank.field_name_curve, curve.id)
                new_tank_feat.setAttribute(Tank.field_name_diameter, diameter)
                new_tank_feat.setAttribute(Tank.field_name_elevation, elev)
                new_tank_feat.setAttribute(Tank.field_name_elevation_corr, elev_corr)
                new_tank_feat.setAttribute(Tank.field_name_level_init, level_init)
                new_tank_feat.setAttribute(Tank.field_name_level_min, level_min)
                new_tank_feat.setAttribute(Tank.field_name_level_max, level_max)
                new_tank_feat.setAttribute(Tank.field_name_vol_min, vol_min)

                new_tank_feat.setGeometry(QgsGeometry.fromPoint(point))

                Parameters.tanks_vlay.addFeatures([new_tank_feat])

            except Exception:
                Parameters.tanks_vlay.destroyEditCommand()

            Parameters.tanks_vlay.endEditCommand()

            return new_tank_feat

    @staticmethod
    def move_junction(node_ft, new_pos_pt):
        caps = Parameters.junctions_vlay.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.ChangeGeometries:

            Parameters.reservoirs_vlay.beginEditCommand('Move junction')

            try:
                edit_utils = QgsVectorLayerEditUtils(Parameters.junctions_vlay)
                edit_utils.moveVertex(
                    new_pos_pt.x(),
                    new_pos_pt.y(),
                    node_ft.id(),
                    0)

            except Exception:
                Parameters.junctions_vlay.destroyEditCommand()

            Parameters.junctions_vlay.endEditCommand()

class LinkHandler:
    def __init__(self):
        pass

    @staticmethod
    def create_new_pipe(eid, demand, diameter, loss, roughness, status, nodes):

        pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()
        if pipes_caps and QgsVectorDataProvider.AddFeatures:

            pipe_geom = QgsGeometry.fromPolyline(nodes)

            # Calculate 3D length
            if Parameters.dem_rlay is not None:
                length_3d = LinkHandler.calc_3d_length(pipe_geom)
            else:
                length_3d = pipe_geom.length()

            Parameters.pipes_vlay.beginEditCommand("Add new pipes")
            new_pipe_ft = None

            try:
                new_pipe_ft = QgsFeature(Parameters.pipes_vlay.pendingFields())
                new_pipe_ft.setAttribute(Pipe.field_name_eid, eid)
                new_pipe_ft.setAttribute(Pipe.field_name_demand, demand)
                new_pipe_ft.setAttribute(Pipe.field_name_diameter, diameter)
                new_pipe_ft.setAttribute(Pipe.field_name_length, length_3d)
                new_pipe_ft.setAttribute(Pipe.field_name_minor_loss, loss)
                new_pipe_ft.setAttribute(Pipe.field_name_roughness, roughness)
                new_pipe_ft.setAttribute(Pipe.field_name_status, status)

                new_pipe_ft.setGeometry(pipe_geom)

                Parameters.pipes_vlay.addFeatures([new_pipe_ft])

            except Exception:
                Parameters.pipes_vlay.destroyEditCommand()

            Parameters.pipes_vlay.endEditCommand()

            return new_pipe_ft

    @staticmethod
    def create_new_pump(pipe_ft, closest_junction_ft, position, pump_curve):

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

        pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()
        junctions_caps = Parameters.junctions_vlay.dataProvider().capabilities()
        pumps_caps = Parameters.pumps_vlay.dataProvider().capabilities()

        if junctions_caps:
            j_demand = closest_junction_ft.attribute(Junction.field_name_demand)
            depth = closest_junction_ft.attribute(Junction.field_name_depth)
            pattern_id = closest_junction_ft.attribute(Junction.field_name_pattern)

            junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J')  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, node_before, 1)
            NodeHandler.create_new_junction(node_before, junction_eid, elev, j_demand, depth, pattern_id)

            junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J')  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, node_after, 1)
            NodeHandler.create_new_junction(node_after, junction_eid, elev, j_demand, depth, pattern_id)

        # Split the pipe and create gap
        if pipes_caps:
            gap = 1 # TODO: softcode pump length
            LinkHandler.split_pipe(pipe_ft, position, gap)

        # Create the new link (the pipe)
        if pumps_caps:

            pump_eid = NetworkUtils.find_next_id(Parameters.pumps_vlay, 'P')  # TODO: softcode
            pump_geom = QgsGeometry.fromPolyline([node_before, node_after])

            Parameters.pumps_vlay.beginEditCommand("Add new pump")

            new_pump_ft = None
            try:
                new_pump_ft = QgsFeature(Parameters.pumps_vlay.pendingFields())
                new_pump_ft.setAttribute(Pump.field_name_eid, pump_eid)
                new_pump_ft.setAttribute(Pump.field_name_curve, pump_curve.id)

                new_pump_ft.setGeometry(pump_geom)

                Parameters.pumps_vlay.addFeatures([new_pump_ft])

            except Exception:
                Parameters.pumps_vlay.destroyEditCommand()

            Parameters.pumps_vlay.endEditCommand()

            return new_pump_ft

    @staticmethod
    def create_new_valve(valve_ft, closest_junction_ft, position, diameter, minor_loss, setting, type):

        # Find start and end nodes positions
        # Get vertex along line next to snapped point
        a, b, next_vertex = valve_ft.geometry().closestSegmentWithContext(position)

        dist = PointsAlongLineUtils.distance(valve_ft.geometry(), QgsGeometry.fromPoint(position))
        dist_before = dist - 0.5 # TODO: softcode based on projection units
        if dist_before <= 0:
            dist_before = 1
        dist_after = dist + 0.5 # TODO: softcode based on projection units
        if dist_after > valve_ft.geometry().length():
            dist_after = valve_ft.geometry().length() - 1

        if dist_before >= dist_after:
            raise Exception('The pipe is too short for a valve to be placed on it.')

        node_before = valve_ft.geometry().interpolate(dist_before).asPoint()
        node_after = valve_ft.geometry().interpolate(dist_after).asPoint()

        pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()
        junctions_caps = Parameters.junctions_vlay.dataProvider().capabilities()
        valves_caps = Parameters.valves_vlay.dataProvider().capabilities()

        if junctions_caps:
            j_demand = closest_junction_ft.attribute(Junction.field_name_demand)
            depth = closest_junction_ft.attribute(Junction.field_name_depth)
            pattern_id = closest_junction_ft.attribute(Junction.field_name_pattern)

            junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J')  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, node_before, 1)
            NodeHandler.create_new_junction(node_before, junction_eid, elev, j_demand, depth, pattern_id)

            junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J')  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, node_after, 1)
            NodeHandler.create_new_junction(node_after, junction_eid, elev, j_demand, depth, pattern_id)

        # Split the pipe and create gap
        if pipes_caps:
            gap = 1 # TODO: softcode pump length
            LinkHandler.split_pipe(valve_ft, position, gap)

        # Create the new link (the pipe)
        if valves_caps:

            valve_eid = NetworkUtils.find_next_id(Parameters.valves_vlay, 'V')  # TODO: softcode
            valve_geom = QgsGeometry.fromPolyline([node_before, node_after])

            Parameters.valves_vlay.beginEditCommand("Add new valve")

            new_valve_ft = None
            try:
                new_valve_ft = QgsFeature(Parameters.valves_vlay.pendingFields())
                new_valve_ft.setAttribute(Valve.field_name_eid, valve_eid)
                new_valve_ft.setAttribute(Valve.field_name_diameter, diameter)
                new_valve_ft.setAttribute(Valve.field_name_minor_loss, minor_loss)
                new_valve_ft.setAttribute(Valve.field_name_setting, setting)
                new_valve_ft.setAttribute(Valve.field_name_type, type)

                new_valve_ft.setGeometry(valve_geom)

                Parameters.valves_vlay.addFeatures([new_valve_ft])

            except Exception:
                Parameters.valves_vlay.destroyEditCommand()

            Parameters.valves_vlay.endEditCommand()

            return new_valve_ft

    @staticmethod
    def split_pipe(pipe_ft, split_point, gap=0):

        # Get vertex along line next to snapped point
        a, b, next_vertex = pipe_ft.geometry().closestSegmentWithContext(split_point)

        # Split only if vertex is not at line ends
        demand = pipe_ft.attribute(Pipe.field_name_demand)
        p_diameter = pipe_ft.attribute(Pipe.field_name_diameter)
        loss = pipe_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe_ft.attribute(Pipe.field_name_roughness)
        status = pipe_ft.attribute(Pipe.field_name_status)

        # Create two new linestrings
        pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(split_point))
        dist_before = dist - 0.5 * gap
        if dist_before <= 0:
            dist_before = gap
        dist_after = dist + 0.5 * gap
        if dist_after > pipe_ft.geometry().length():
            dist_after = pipe_ft.geometry().length() - gap

        if dist_before > dist_after:
            raise Exception('Exception caught in splitting pipe.'
                            'Pipe is too short.')

        node_before = pipe_ft.geometry().interpolate(dist_before)
        node_after = pipe_ft.geometry().interpolate(dist_after)

        if pipes_caps:

            Parameters.junctions_vlay.beginEditCommand("Add new node")

            pipe_ft_1 = None
            pipe_ft_2 = None
            try:
                nodes = pipe_ft.geometry().asPolyline()

                # First new polyline
                pl1_pts = []
                for n in range(next_vertex):
                    pl1_pts.append(QgsPoint(nodes[n].x(), nodes[n].y()))

                pl1_pts.append(node_before.asPoint())

                pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'P')  # TODO: softcode
                pipe_ft_1 = LinkHandler.create_new_pipe(
                    pipe_eid,
                    demand,
                    p_diameter,
                    loss,
                    roughness,
                    status,
                    pl1_pts)

                # Second new polyline
                pl2_pts = []
                pl2_pts.append(node_after.asPoint())
                for n in range(len(nodes) - next_vertex):
                    pl2_pts.append(QgsPoint(nodes[n + next_vertex].x(), nodes[n + next_vertex].y()))

                pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'P')  # TODO: softcode
                pipe_ft_2 = LinkHandler.create_new_pipe(
                    pipe_eid,
                    demand,
                    p_diameter,
                    loss,
                    roughness,
                    status,
                    pl2_pts)

                # Delete old pipe
                Parameters.pipes_vlay.deleteFeature(pipe_ft.id())

            except Exception:
                Parameters.pipes_vlay.destroyEditCommand()

            Parameters.pipes_vlay.endEditCommand()

            return [pipe_ft_1, pipe_ft_2]

    @staticmethod
    def move_pipe_vertex(pipe_ft, new_pos_pt, vertex_index):
        caps = Parameters.pipes_vlay.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.ChangeGeometries:
            Parameters.pipes_vlay.beginEditCommand("Update pipes geometry")

            try:
                edit_utils = QgsVectorLayerEditUtils(Parameters.pipes_vlay)
                edit_utils.moveVertex(
                    new_pos_pt.x(),
                    new_pos_pt.y(),
                    pipe_ft.id(),
                    vertex_index)
            except Exception:
                Parameters.pipes_vlay.destroyEditCommand()

            Parameters.pipes_vlay.endEditCommand()

    @staticmethod
    def calc_3d_length(pipe_geom):

        # Check whether start and end node exist
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(pipe_geom)

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
    def find_start_end_nodes(link_geom):
        link_vertices = link_geom.asPolyline()

        start_node_ft = None
        end_node_ft = None

        # Search among nodes
        junction_feats = Parameters.junctions_vlay.getFeatures()
        reservoir_feats = Parameters.reservoirs_vlay.getFeatures()
        tanks_feats = Parameters.tanks_vlay.getFeatures()

        all_feats = list(junction_feats) + list(reservoir_feats) + list(tanks_feats)

        for node_feat in all_feats:
            node_geom = node_feat.geometry()
            if node_geom.distance(QgsGeometry.fromPoint(link_vertices[0])) < Parameters.tolerance:
                start_node_ft = node_feat
            if node_geom.distance(QgsGeometry.fromPoint(link_vertices[len(link_vertices) - 1])) < Parameters.tolerance:
                end_node_ft = node_feat

        return start_node_ft, end_node_ft

    @staticmethod
    def find_start_end_junctions(link_geom):
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

    @staticmethod
    def find_adjacent_pipes(node_geom):

        # Search among pumps
        adjacent_pumps_fts = []
        for pipe_ft in Parameters.pipes_vlay.getFeatures():
            pipe_geom = pipe_ft.geometry()
            nodes = pipe_geom.asPolyline()
            # print 'nodes', node_geom.exportToWkt(), nodes[0].wellKnownText(), nodes[len(nodes) - 1].wellKnownText()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0])) or\
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1])):
                adjacent_pumps_fts.append(pipe_ft)

        return adjacent_pumps_fts

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
    def points_overlap(point_geom1, point_geom2):
        if point_geom1.distance(point_geom2) < Parameters.tolerance:
            return TabError
        else:
            return False