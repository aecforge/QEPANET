import math
from collections import OrderedDict

from PyQt4.QtCore import QPyNullVariant
from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsSnapper, QgsProject, QgsTolerance, QgsPoint,\
    QgsVectorLayerEditUtils, QgsFeatureRequest

from network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from ..tools.parameters import Parameters
from ..geo_utils import raster_utils
from ..geo_utils.points_along_line import PointsAlongLineGenerator, PointsAlongLineUtils


class NodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def create_new_junction(parameters, point, eid, elev, demand, depth, pattern_id):

        junctions_caps = parameters.junctions_vlay.dataProvider().capabilities()
        if junctions_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            parameters.junctions_vlay.beginEditCommand("Add junction")
            new_junct_feat = None

            try:
                new_junct_feat = QgsFeature(parameters.junctions_vlay.pendingFields())
                new_junct_feat.setAttribute(Junction.field_name_eid, eid)
                new_junct_feat.setAttribute(Junction.field_name_elevation, elev)
                new_junct_feat.setAttribute(Junction.field_name_demand, demand)
                new_junct_feat.setAttribute(Junction.field_name_elev_corr, depth)
                new_junct_feat.setAttribute(Junction.field_name_pattern, pattern_id)

                new_junct_feat.setGeometry(QgsGeometry.fromPoint(point))

                parameters.junctions_vlay.addFeatures([new_junct_feat])

            except Exception as e:
                parameters.junctions_vlay.destroyEditCommand()
                raise e

                parameters.junctions_vlay.endEditCommand()

            return new_junct_feat

    @staticmethod
    def create_new_reservoir(parameters, point, eid, elev, elev_corr, head):

        reservoirs_caps = parameters.reservoirs_vlay.dataProvider().capabilities()
        if reservoirs_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            parameters.reservoirs_vlay.beginEditCommand("Add reservoir")
            new_reservoir_feat = None

            try:
                new_reservoir_feat = QgsFeature(parameters.reservoirs_vlay.pendingFields())
                new_reservoir_feat.setAttribute(Reservoir.field_name_eid, eid)
                new_reservoir_feat.setAttribute(Reservoir.field_name_elevation, elev)
                new_reservoir_feat.setAttribute(Reservoir.field_name_elev_corr, elev_corr)
                new_reservoir_feat.setAttribute(Reservoir.field_name_head, head)

                new_reservoir_feat.setGeometry(QgsGeometry.fromPoint(point))

                parameters.reservoirs_vlay.addFeatures([new_reservoir_feat])

            except Exception as e:
                parameters.reservoirs_vlay.destroyEditCommand()
                raise e

                parameters.reservoirs_vlay.endEditCommand()

            return new_reservoir_feat

    @staticmethod
    def create_new_tank(parameters, point, eid, tank_curve_id, diameter, elev, elev_corr, level_init, level_min, level_max, vol_min):
        tanks_caps = parameters.tanks_vlay.dataProvider().capabilities()
        if tanks_caps and QgsVectorDataProvider.AddFeatures:

            parameters.tanks_vlay.beginEditCommand("Add junction")

            try:
                new_tank_feat = QgsFeature(parameters.tanks_vlay.pendingFields())

                new_tank_feat.setAttribute(Tank.field_name_eid, eid)
                new_tank_feat.setAttribute(Tank.field_name_curve, tank_curve_id)
                new_tank_feat.setAttribute(Tank.field_name_diameter, diameter)
                new_tank_feat.setAttribute(Tank.field_name_elevation, elev)
                new_tank_feat.setAttribute(Tank.field_name_elev_corr, elev_corr)
                new_tank_feat.setAttribute(Tank.field_name_level_init, level_init)
                new_tank_feat.setAttribute(Tank.field_name_level_min, level_min)
                new_tank_feat.setAttribute(Tank.field_name_level_max, level_max)
                new_tank_feat.setAttribute(Tank.field_name_vol_min, vol_min)

                new_tank_feat.setGeometry(QgsGeometry.fromPoint(point))

                parameters.tanks_vlay.addFeatures([new_tank_feat])

            except Exception as e:
                parameters.tanks_vlay.destroyEditCommand()
                raise e

                parameters.tanks_vlay.endEditCommand()

            return new_tank_feat

    @staticmethod
    def move_element(layer, dem_rlay, node_ft, new_pos_pt):
        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.ChangeGeometries:

            layer.beginEditCommand('Move node')

            try:
                edit_utils = QgsVectorLayerEditUtils(layer)
                edit_utils.moveVertex(
                    new_pos_pt.x(),
                    new_pos_pt.y(),
                    node_ft.id(),
                    0)

                # Elevation
                new_elev = raster_utils.read_layer_val_from_coord(dem_rlay, new_pos_pt, 1)
                if new_elev is None:
                    new_elev = 0

                field_index = layer.dataProvider().fieldNameIndex(Junction.field_name_elevation)
                layer.changeAttributeValue(node_ft.id(), field_index, new_elev)

            except Exception as e:
                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

    @staticmethod
    def _delete_feature(layer, feature):
        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.DeleteFeatures:

            layer.beginEditCommand('Delete feature')

            try:
                layer.deleteFeature(feature.id())

            except Exception as e:
                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

    @staticmethod
    def delete_node(parameters, layer, node_ft):

        # The node is a junction
        if layer == parameters.junctions_vlay:

            # # The node is a simple node (not part of a pump or valve)
            # adj_links_fts = NetworkUtils.find_adjacent_links(parameters, node_ft.geometry())
            #
            # # Only pipes adjacent to node: it's a simple junction
            # if not adj_links_fts['pumps'] and not adj_links_fts['valves']:

                # Delete node
                NodeHandler._delete_feature(layer, node_ft)

                # Delete adjacent pipes
                adj_pipes = NetworkUtils.find_adjacent_links(parameters, node_ft.geometry())
                for adj_pipe in adj_pipes['pipes']:
                    LinkHandler.delete_link(parameters, parameters.pipes_vlay, adj_pipe)

            # # The node is part of a pump or valve
            # else:
            #
            #     if adj_links_fts['pumps'] or adj_links_fts['valves']:
            #
            #         if adj_links_fts['pumps']:
            #             adj_links_ft = adj_links_fts['pumps'][0]
            #         elif adj_links_fts['valves']:
            #             adj_links_ft = adj_links_fts['valves'][0]
            #         else:
            #             return
            #
            #         adjadj_links = NetworkUtils.find_links_adjacent_to_link(parameters, layer, adj_links_ft, False, True, True)
            #         adj_nodes = NetworkUtils.find_start_end_nodes(parameters, adj_links_ft.geometry(), False, True, True)
            #
            #         # Stitch...
            #         midpoint = NetworkUtils.find_midpoint(adj_nodes[0].geometry().asPoint(), adj_nodes[1].geometry().asPoint())
            #
            #         LinkHandler.stitch_pipes(
            #             parameters,
            #             adjadj_links['pipes'][0],
            #             adj_nodes[0].geometry().asPoint(),
            #             adjadj_links['pipes'][1],
            #             adj_nodes[1].geometry().asPoint(),
            #             midpoint)

        # The node is a reservoir or a tank
        elif layer == parameters.reservoirs_vlay or layer == parameters.tanks_vlay:

            adj_pipes = NetworkUtils.find_adjacent_links(parameters, node_ft.geometry())['pipes']

            NodeHandler._delete_feature(layer, node_ft)

            for adj_pipe in adj_pipes:
                LinkHandler.delete_link(parameters.pipes_vlay, adj_pipe)


class LinkHandler:
    def __init__(self):
        pass

    @staticmethod
    def create_new_pipe(parameters, eid, demand, diameter, loss, roughness, status, nodes):

        pipes_caps = parameters.pipes_vlay.dataProvider().capabilities()
        if pipes_caps and QgsVectorDataProvider.AddFeatures:

            pipe_geom = QgsGeometry.fromPolyline(nodes)

            # Calculate 3D length
            if parameters.dem_rlay is not None:
                length_3d = LinkHandler.calc_3d_length(parameters, pipe_geom)
            else:
                length_3d = pipe_geom.length()

                parameters.pipes_vlay.beginEditCommand("Add new pipes")
            new_pipe_ft = None

            try:
                new_pipe_ft = QgsFeature(parameters.pipes_vlay.pendingFields())
                new_pipe_ft.setAttribute(Pipe.field_name_eid, eid)
                new_pipe_ft.setAttribute(Pipe.field_name_demand, demand)
                new_pipe_ft.setAttribute(Pipe.field_name_diameter, diameter)
                new_pipe_ft.setAttribute(Pipe.field_name_length, length_3d)
                new_pipe_ft.setAttribute(Pipe.field_name_minor_loss, loss)
                new_pipe_ft.setAttribute(Pipe.field_name_roughness, roughness)
                new_pipe_ft.setAttribute(Pipe.field_name_status, status)

                new_pipe_ft.setGeometry(pipe_geom)

                parameters.pipes_vlay.addFeatures([new_pipe_ft])

            except Exception as e:
                parameters.pipes_vlay.destroyEditCommand()
                raise e

            parameters.pipes_vlay.endEditCommand()
            return new_pipe_ft

    @staticmethod
    def create_new_pumpvalve(parameters, data_dock, pipe_ft, closest_junction_ft, position, layer, attributes):

        # Find start and end nodes positions
        # Get vertex along line next to snapped point
        a, b, next_vertex = pipe_ft.geometry().closestSegmentWithContext(position)

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(position), parameters.tolerance)
        dist_before = dist - 0.5  # TODO: softcode based on projection units
        if dist_before <= 0:
            dist_before = 1
        dist_after = dist + 0.5  # TODO: softcode based on projection units
        if dist_after > pipe_ft.geometry().length():
            dist_after = pipe_ft.geometry().length() - 1

        if dist_before >= dist_after:
            raise Exception('The pipe is too short for a pump or valve to be placed on it.')

        node_before = pipe_ft.geometry().interpolate(dist_before).asPoint()
        node_after = pipe_ft.geometry().interpolate(dist_after).asPoint()

        pipes_caps = parameters.pipes_vlay.dataProvider().capabilities()
        junctions_caps = parameters.junctions_vlay.dataProvider().capabilities()
        caps = layer.dataProvider().capabilities()

        if junctions_caps:
            if closest_junction_ft is not None:
                j_demand = closest_junction_ft.attribute(Junction.field_name_demand)
                depth = closest_junction_ft.attribute(Junction.field_name_elev_corr)
                pattern_id = closest_junction_ft.attribute(Junction.field_name_pattern)
            else:
                j_demand = float(data_dock.txt_junction_demand.text())
                depth = float(data_dock.txt_junction_depth.text())
                pattern_id = data_dock.cbo_junction_pattern.itemData(data_dock.cbo_junction_pattern.currentIndex()).id

            junction_eid = NetworkUtils.find_next_id(parameters.junctions_vlay, 'J')  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, node_before, 1)
            NodeHandler.create_new_junction(parameters, node_before, junction_eid, elev, j_demand, depth, pattern_id)

            junction_eid = NetworkUtils.find_next_id(parameters.junctions_vlay, 'J')  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, node_after, 1)
            NodeHandler.create_new_junction(parameters, node_after, junction_eid, elev, j_demand, depth, pattern_id)

        # Split the pipe and create gap
        if pipes_caps:
            gap = 1  # TODO: softcode pump length
            LinkHandler.split_pipe(parameters, pipe_ft, position, gap)

        # Create the new link (the pump or valve)
        if caps:

            prefix = ''
            if layer == parameters.pumps_vlay:
                prefix = 'P'  # TODO: softcode
            elif layer == parameters.valves_vlay:
                prefix = 'V'  # TODO: softcode
            eid = NetworkUtils.find_next_id(layer, prefix)  # TODO: softcode

            geom = QgsGeometry.fromPolyline([node_before, node_after])

            layer.beginEditCommand("Add new pump/valve")

            try:
                new_ft = QgsFeature(layer.pendingFields())

                if layer == parameters.pumps_vlay:
                    new_ft = QgsFeature(parameters.pumps_vlay.pendingFields())
                    new_ft.setAttribute(Pump.field_name_eid, eid)
                    new_ft.setAttribute(Pump.field_name_param, attributes[0])
                    new_ft.setAttribute(Pump.field_name_value, attributes[1])

                elif layer == parameters.valves_vlay:
                    new_ft.setAttribute(Valve.field_name_eid, eid)
                    new_ft.setAttribute(Valve.field_name_diameter, attributes[0])
                    new_ft.setAttribute(Valve.field_name_minor_loss, attributes[1])
                    new_ft.setAttribute(Valve.field_name_setting, attributes[2])
                    new_ft.setAttribute(Valve.field_name_type, attributes[3])

                new_ft.setGeometry(geom)

                layer.addFeatures([new_ft])

            except Exception as e:
                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

            return new_ft

    @staticmethod
    def split_pipe(parameters, pipe_ft, split_point, gap=0):

        # Get vertex along line next to snapped point
        a, b, next_vertex = pipe_ft.geometry().closestSegmentWithContext(split_point)

        # Split only if vertex is not at line ends
        demand = pipe_ft.attribute(Pipe.field_name_demand)
        p_diameter = pipe_ft.attribute(Pipe.field_name_diameter)
        loss = pipe_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe_ft.attribute(Pipe.field_name_roughness)
        status = pipe_ft.attribute(Pipe.field_name_status)

        # Create two new linestrings
        pipes_caps = parameters.pipes_vlay.dataProvider().capabilities()

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(split_point), parameters.tolerance)
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

            parameters.junctions_vlay.beginEditCommand("Add new node")

            pipe_ft_1 = None
            pipe_ft_2 = None
            try:
                nodes = pipe_ft.geometry().asPolyline()

                # First new polyline
                pl1_pts = []
                for n in range(next_vertex):
                    pl1_pts.append(QgsPoint(nodes[n].x(), nodes[n].y()))

                pl1_pts.append(node_before.asPoint())

                pipe_eid = NetworkUtils.find_next_id(parameters.pipes_vlay, 'P')  # TODO: softcode
                pipe_ft_1 = LinkHandler.create_new_pipe(
                    parameters,
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

                pipe_eid = NetworkUtils.find_next_id(parameters.pipes_vlay, 'P')  # TODO: softcode
                pipe_ft_2 = LinkHandler.create_new_pipe(
                    parameters,
                    pipe_eid,
                    demand,
                    p_diameter,
                    loss,
                    roughness,
                    status,
                    pl2_pts)

                # Delete old pipe
                parameters.pipes_vlay.deleteFeature(pipe_ft.id())

            except Exception as e:
                parameters.pipes_vlay.destroyEditCommand()
                raise e

            parameters.pipes_vlay.endEditCommand()

            return [pipe_ft_1, pipe_ft_2]

    @staticmethod
    def move_pipe_vertex(parameters, pipe_ft, new_pos_pt, vertex_index):
        caps = parameters.pipes_vlay.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:
            parameters.pipes_vlay.beginEditCommand("Update pipes geometry")

            try:
                edit_utils = QgsVectorLayerEditUtils(parameters.pipes_vlay)
                edit_utils.moveVertex(
                    new_pos_pt.x(),
                    new_pos_pt.y(),
                    pipe_ft.id(),
                    vertex_index)

                # Retrieve the feature again, and update attributes
                request = QgsFeatureRequest().setFilterFid(pipe_ft.id())
                feats = list(parameters.pipes_vlay.getFeatures(request))

                field_index = parameters.pipes_vlay.dataProvider().fieldNameIndex(Pipe.field_name_length)
                new_3d_length = LinkHandler.calc_3d_length(parameters, feats[0].geometry())
                parameters.pipes_vlay.changeAttributeValue(pipe_ft.id(), field_index, new_3d_length)

            except Exception as e:
                parameters.pipes_vlay.destroyEditCommand()
                raise e

            parameters.pipes_vlay.endEditCommand()

    @staticmethod
    def move_pump_valve(vlay, ft, delta_vector):
        caps = vlay.dataProvider().capabilities()
        if caps and QgsVectorDataProvider.ChangeGeometries:
            vlay.beginEditCommand('Update pump/valve')
            try:

                old_ft_pts = ft.geometry().asPolyline()
                edit_utils = QgsVectorLayerEditUtils(vlay)

                edit_utils.moveVertex(
                    (QgsPoint(old_ft_pts[0].x() + delta_vector.x(), old_ft_pts[0].y() + delta_vector.y())).x(),
                    (QgsPoint(old_ft_pts[0].x() + delta_vector.x(), old_ft_pts[0].y() + delta_vector.y())).y(),
                    ft.id(),
                    0)
                # In 2.16
                # edit_utils.moveVertex(
                #     (old_ft_pts[0] + delta_vector).x(),
                #     (old_ft_pts[0] + delta_vector).y(),
                #     ft.id(),
                #     0)

                edit_utils.moveVertex(
                    (QgsPoint(old_ft_pts[1].x() + delta_vector.x(), old_ft_pts[1].y() + delta_vector.y())).x(),
                    (QgsPoint(old_ft_pts[1].x() + delta_vector.x(), old_ft_pts[1].y() + delta_vector.y())).y(),
                    ft.id(),
                    1)
                # In 2.16
                # edit_utils.moveVertex(
                #     (old_ft_pts[1] + delta_vector).x(),
                #     (old_ft_pts[1] + delta_vector).y(),
                #     ft.id(),
                #     1)

            except Exception as e:
                vlay.destroyEditCommand()
                raise e

            vlay.endEditCommand()

    @staticmethod
    def _delete_feature(layer, link_ft):

        caps = layer.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.DeleteFeatures:

            layer.beginEditCommand('Delete feature')

            try:
                layer.deleteFeature(link_ft.id())

            except Exception as e:
                layer.destroyEditCommand()
                raise e

            layer.endEditCommand()

    @staticmethod
    def delete_link(parameters, layer, link_ft):

        # The link is a pipe
        if layer == parameters.pipes_vlay:
            LinkHandler._delete_feature(layer, link_ft)

        # The link is a pump or valve
        elif layer == parameters.pumps_vlay or layer == parameters.valves_vlay:

            adj_links_fts = NetworkUtils.find_adjacent_links(parameters, link_ft.geometry())

            if adj_links_fts['pumps']:
                adj_links_ft = adj_links_fts['pumps'][0]
            elif adj_links_fts['valves']:
                adj_links_ft = adj_links_fts['valves'][0]
            else:
                return

            adjadj_links = NetworkUtils.find_links_adjacent_to_link(parameters, layer,
                                                                    adj_links_ft,
                                                                    False, True, True)
            adj_nodes = NetworkUtils.find_start_end_nodes(parameters, adj_links_ft.geometry(),
                                                          False, True, True)

            # Stitch...
            midpoint = NetworkUtils.find_midpoint(adj_nodes[0].geometry().asPoint(),
                                                  adj_nodes[1].geometry().asPoint())

            if len(adjadj_links['pipes']) == 2:
                LinkHandler.stitch_pipes(
                    parameters,
                    adjadj_links['pipes'][0],
                    adj_nodes[0].geometry().asPoint(),
                    adjadj_links['pipes'][1],
                    adj_nodes[1].geometry().asPoint(),
                    midpoint)

            # Delete old links and pipes
            LinkHandler._delete_feature(layer, adj_links_ft)

            for adjadj_link in adjadj_links['pipes']:
                LinkHandler._delete_feature(parameters.pipes_vlay, adjadj_link)
            NodeHandler._delete_feature(parameters.junctions_vlay, adj_nodes[0])
            NodeHandler._delete_feature(parameters.junctions_vlay, adj_nodes[1])

    @staticmethod
    def delete_vertex(parameters, layer, pipe_ft, vertex_index):
        caps = layer.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:
            layer.beginEditCommand("Update pipe geometry")

            try:
                edit_utils = QgsVectorLayerEditUtils(parameters.pipes_vlay)
                edit_utils.deleteVertexV2(pipe_ft.id(), vertex_index)

                # Retrieve the feature again, and update attributes
                request = QgsFeatureRequest().setFilterFid(pipe_ft.id())
                feats = list(parameters.pipes_vlay.getFeatures(request))

                field_index = parameters.pipes_vlay.dataProvider().fieldNameIndex(Pipe.field_name_length)
                new_3d_length = LinkHandler.calc_3d_length(parameters, feats[0].geometry())
                parameters.pipes_vlay.changeAttributeValue(pipe_ft.id(), field_index, new_3d_length)

            except Exception as e:
                parameters.pipes_vlay.destroyEditCommand()
                raise e

            parameters.pipes_vlay.endEditCommand()

    @staticmethod
    def stitch_pipes(parameters, pipe1_ft, stitch_pt1, pipe2_ft, stitch_pt2, stich_pt_new):

        new_geom_pts = []

        # Add points from first adjacent link
        closest_xv1 = pipe1_ft.geometry().closestVertexWithContext(stitch_pt1)
        if closest_xv1[1] == 0:
            new_geom_pts.extend(pipe1_ft.geometry().asPolyline()[::-1])
        else:
            new_geom_pts.extend(pipe1_ft.geometry().asPolyline())

        del new_geom_pts[-1]

        new_geom_pts.append(stich_pt_new)

        # Add points from second adjacent link
        closest_xv2 = pipe2_ft.geometry().closestVertexWithContext(stitch_pt2)
        if closest_xv2[1] == 0:
            new_geom_pts.extend(pipe2_ft.geometry().asPolyline()[1:])
        else:
            new_geom_pts.extend(pipe2_ft.geometry().asPolyline()[::-1][:-1])

        eid = NetworkUtils.find_next_id(parameters.pipes_vlay, 'P')  # TODO: softcode

        # TODO: let the user set the attributes
        demand = pipe1_ft.attribute(Pipe.field_name_demand)
        diameter = pipe1_ft.attribute(Pipe.field_name_diameter)
        loss = pipe1_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe1_ft.attribute(Pipe.field_name_roughness)
        status = pipe1_ft.attribute(Pipe.field_name_status)

        LinkHandler.create_new_pipe(parameters, eid, demand, diameter, loss, roughness, status, new_geom_pts)

    @staticmethod
    def calc_3d_length(parameters, pipe_geom):

        # Check whether start and end node exist
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(parameters, pipe_geom)

        distance_elev_od = OrderedDict()

        # Start node
        start_add = 0
        if start_node_ft is not None:
            start_node_elev = start_node_ft.attribute(Junction.field_name_elevation)
            if start_node_elev is None or type(start_node_elev) is QPyNullVariant:
                start_node_elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, start_node_ft.geometry().asPoint(), 0)
                if start_node_elev is None:
                    start_node_elev = 0

            start_node_depth = start_node_ft.attribute(Junction.field_name_elev_corr)
            if start_node_depth is None or type(start_node_depth) is QPyNullVariant:
                start_node_depth = 0
            start_add = 1

        # End node
        end_remove = 0
        if end_node_ft is not None:
            end_node_elev = end_node_ft.attribute(Junction.field_name_elevation)
            if end_node_elev is None or type(end_node_elev) is QPyNullVariant:
                end_node_elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, end_node_ft.geometry().asPoint(), 0)
                if end_node_elev is None:
                    end_node_elev = 0
            end_node_depth = end_node_ft.attribute(Junction.field_name_elev_corr)
            if end_node_depth is None or type(end_node_depth) is QPyNullVariant:
                end_node_depth = 0
            end_remove = 1

        point_gen = PointsAlongLineGenerator(pipe_geom)
        dists_and_points = point_gen.get_points_coords(100, False)  # TODO: Softcode the interval between points

        if start_node_ft is not None:
            distance_elev_od[0] = start_node_elev - start_node_depth

        for p in range(start_add, len(dists_and_points) - end_remove):
            elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, dists_and_points.values()[p].asPoint(), 1)
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
    def find_start_end_nodes(parameters, link_geom, exclude_junctions=False, exclude_reservoirs=False, exclude_tanks=False):

        all_feats = []
        if not exclude_junctions:
            all_feats.extend(list(parameters.junctions_vlay.getFeatures()))
        if not exclude_reservoirs:
            all_feats.extend(list(parameters.reservoirs_vlay.getFeatures()))
        if not exclude_tanks:
            all_feats.extend(list(parameters.tanks_vlay.getFeatures()))

        intersecting_fts = [None, None]
        if not all_feats:
            return intersecting_fts

        cands = []
        for junction_ft in all_feats:
            if link_geom.buffer(parameters.tolerance, 5).boundingBox().contains(junction_ft.geometry().asPoint()):
                cands.append(junction_ft)

        if cands:
            for junction_ft in cands:
                if junction_ft.geometry().distance(QgsGeometry.fromPoint(link_geom.asPolyline()[0])) < parameters.tolerance:
                    intersecting_fts[0] = junction_ft
                if junction_ft.geometry().distance(QgsGeometry.fromPoint(link_geom.asPolyline()[-1])) < parameters.tolerance:
                    intersecting_fts[1] = junction_ft

        return intersecting_fts

    @staticmethod
    def find_adjacent_links(parameters, node_geom):

        adjacent_links_d = {'pumps': [], 'valves': []}

        # Search among pipes
        adjacent_pipes_fts = []
        for pipe_ft in parameters.pipes_vlay.getFeatures():
            pipe_geom = pipe_ft.geometry()
            nodes = pipe_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0]), parameters.tolerance) or\
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1]), parameters.tolerance):
                adjacent_pipes_fts.append(pipe_ft)

        adjacent_links_d['pipes'] = adjacent_pipes_fts

        if len(adjacent_pipes_fts) > 2:
            # It's a pure junction, cannot be a pump or valve
            return adjacent_links_d

        # Search among pumps
        adjacent_pumps_fts = []
        for pump_ft in parameters.pumps_vlay.getFeatures():
            pump_geom = pump_ft.geometry()
            nodes = pump_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0]), parameters.tolerance) or \
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1]), parameters.tolerance):
                adjacent_pumps_fts.append(pump_ft)

        adjacent_links_d['pumps'] = adjacent_pumps_fts

        # Search among valves
        adjacent_valves_fts = []
        for valve_ft in parameters.valves_vlay.getFeatures():
            valve_geom = valve_ft.geometry()
            nodes = valve_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0]), parameters.tolerance) or \
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1]), parameters.tolerance):
                adjacent_valves_fts.append(valve_ft)

        adjacent_links_d['valves'] = adjacent_valves_fts

        return adjacent_links_d

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
        snapper.setSnapMode(QgsSnapper.SnapWithResultsForSamePosition)
        return snapper

    @staticmethod
    def points_overlap(point1, point2, tolerance):
        """Checks whether two points overlap. Uses tolerance."""

        if isinstance(point1, QgsPoint):
            point1 = QgsGeometry.fromPoint(point1)

        if isinstance(point2, QgsPoint):
            point2 = QgsGeometry.fromPoint(point2)

        if point1.distance(point2) < tolerance:
            return TabError
        else:
            return False

    @staticmethod
    def find_pumps_valves_junctions(parameters):
        """Find junctions adjacent to pumps and valves"""

        adj_points = []

        pump_fts = parameters.pumps_vlay.getFeatures()
        for pump_ft in pump_fts:
            (start, end) = NetworkUtils.find_start_end_nodes(pump_ft.geometry(), False, True, True)
            if start is not None:
                adj_points.append(start.geometry().asPoint())
            if end is not None:
                adj_points.append(end.geometry().asPoint())

        valve_fts = parameters.valves_vlay.getFeatures()
        for valve_ft in valve_fts:
            (start, end) = NetworkUtils.find_start_end_nodes(valve_ft.geometry(), False, True, True)
            if start is not None:
                adj_points.append(start.geometry().asPoint())
            if end is not None:
                adj_points.append(end.geometry().asPoint())

        return adj_points

    @staticmethod
    def find_links_adjacent_to_link(parameters, link_vlay, link_ft, exclude_pipes=False, exclude_pumps=False, exclude_valves=False):
        """Finds the links adjacent to a given link"""

        adj_links = dict()
        if not exclude_pipes:
            adj_links['pipes'] = NetworkUtils.look_for_adjacent_links(parameters, link_ft, link_vlay, parameters.pipes_vlay)
        if not exclude_pumps:
            adj_links['pumps'] = NetworkUtils.look_for_adjacent_links(parameters, link_ft, link_vlay, parameters.pumps_vlay)
        if not exclude_valves:
            adj_links['valves'] = NetworkUtils.look_for_adjacent_links(parameters, link_ft, link_vlay, parameters.valves_vlay)

        return adj_links

    @staticmethod
    def look_for_adjacent_links(parameters, link_ft, link_vlay, search_vlay):

        link_pts = link_ft.geometry().asPolyline()

        adj_links = []
        for ft in search_vlay.getFeatures():
            pts = ft.geometry().asPolyline()
            if NetworkUtils.points_overlap(pts[0], link_pts[0], parameters.tolerance) or \
                    NetworkUtils.points_overlap(pts[0], link_pts[-1], parameters.tolerance) or \
                    NetworkUtils.points_overlap(pts[-1], link_pts[0], parameters.tolerance) or \
                    NetworkUtils.points_overlap(pts[-1], link_pts[-1], parameters.tolerance):

                # Check that the feature found is not the same as the input
                if not (link_vlay.id() == search_vlay.id() and link_ft.id() != ft.id()):
                    adj_links.append(ft)

        return adj_links

    @staticmethod
    def find_overlapping_nodes(parameters, point):

        overlap_juncts = []
        overlap_reservs = []
        overlap_tanks = []

        for junct_feat in parameters.junctions_vlay.getFeatures():
            if NetworkUtils.points_overlap(junct_feat.geometry(), point, parameters.tolerance):
                overlap_juncts.append(junct_feat)
                break

        for reserv_feat in parameters.reservoirs_vlay.getFeatures():
            if NetworkUtils.points_overlap(reserv_feat.geometry(), point, parameters.tolerance):
                overlap_reservs.append(reserv_feat)
                break

        for tank_feat in parameters.tanks_vlay.getFeatures():
            if NetworkUtils.points_overlap(tank_feat.geometry(), point, parameters.tolerance):
                overlap_tanks.append(tank_feat)
                break

        return {'junctions': overlap_juncts, 'reservoirs': overlap_reservs, 'tanks': overlap_tanks }

    @staticmethod
    def find_midpoint(point1, point2):

        mid_x = (point1.x() + point2.x()) / 2
        mid_y = (point1.y() + point2.y()) / 2

        return QgsPoint(mid_x, mid_y)