import math
from collections import OrderedDict

from PyQt4.QtCore import QPyNullVariant
from qgis.core import QgsFeature, QgsGeometry, QgsVectorDataProvider, QgsSnapper, QgsProject, QgsTolerance, QgsPoint,\
    QgsVectorLayerEditUtils, QgsFeatureRequest, QgsLineStringV2, QgsPointV2, QgsWKBTypes

from network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from ..tools.parameters import Parameters
from ..geo_utils import raster_utils
from ..geo_utils.points_along_line import PointsAlongLineGenerator, PointsAlongLineUtils


class NodeHandler:

    def __init__(self):
        pass

    @staticmethod
    def create_new_junction(params, point, eid, elev, demand, depth, pattern_id):

        junctions_caps = params.junctions_vlay.dataProvider().capabilities()
        if junctions_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            params.junctions_vlay.beginEditCommand("Add junction")

            try:
                new_junct_feat = QgsFeature(params.junctions_vlay.pendingFields())
                new_junct_feat.setAttribute(Junction.field_name_eid, eid)
                new_junct_feat.setAttribute(Junction.field_name_elev, elev)
                new_junct_feat.setAttribute(Junction.field_name_demand, demand)
                new_junct_feat.setAttribute(Junction.field_name_delta_z, depth)
                new_junct_feat.setAttribute(Junction.field_name_pattern, pattern_id)

                new_junct_feat.setGeometry(QgsGeometry.fromPoint(point))

                params.junctions_vlay.addFeatures([new_junct_feat])

            except Exception as e:
                params.junctions_vlay.destroyEditCommand()
                raise e

            params.junctions_vlay.endEditCommand()

            return new_junct_feat

    @staticmethod
    def create_new_reservoir(params, point, eid, elev, elev_corr, head):

        reservoirs_caps = params.reservoirs_vlay.dataProvider().capabilities()
        if reservoirs_caps and QgsVectorDataProvider.AddFeatures:

            # New stand-alone node
            params.reservoirs_vlay.beginEditCommand("Add reservoir")
            new_reservoir_feat = None

            try:
                new_reservoir_feat = QgsFeature(params.reservoirs_vlay.pendingFields())
                new_reservoir_feat.setAttribute(Reservoir.field_name_eid, eid)
                new_reservoir_feat.setAttribute(Reservoir.field_name_elev, elev)
                new_reservoir_feat.setAttribute(Reservoir.field_name_delta_z, elev_corr)
                # new_reservoir_feat.setAttribute(Reservoir.field_name_head, head)

                new_reservoir_feat.setGeometry(QgsGeometry.fromPoint(point))

                params.reservoirs_vlay.addFeatures([new_reservoir_feat])

            except Exception as e:
                params.reservoirs_vlay.destroyEditCommand()
                raise e

                params.reservoirs_vlay.endEditCommand()

            return new_reservoir_feat

    @staticmethod
    def create_new_tank(params, point, eid, tank_curve_id, diameter, elev, elev_corr, level_init, level_min, level_max, vol_min):
        tanks_caps = params.tanks_vlay.dataProvider().capabilities()
        if tanks_caps and QgsVectorDataProvider.AddFeatures:

            params.tanks_vlay.beginEditCommand("Add junction")

            try:
                new_tank_feat = QgsFeature(params.tanks_vlay.pendingFields())

                new_tank_feat.setAttribute(Tank.field_name_eid, eid)
                new_tank_feat.setAttribute(Tank.field_name_curve, tank_curve_id)
                new_tank_feat.setAttribute(Tank.field_name_diameter, diameter)
                new_tank_feat.setAttribute(Tank.field_name_elev, elev)
                new_tank_feat.setAttribute(Tank.field_name_delta_z, elev_corr)
                new_tank_feat.setAttribute(Tank.field_name_level_init, level_init)
                new_tank_feat.setAttribute(Tank.field_name_level_min, level_min)
                new_tank_feat.setAttribute(Tank.field_name_level_max, level_max)
                new_tank_feat.setAttribute(Tank.field_name_vol_min, vol_min)

                new_tank_feat.setGeometry(QgsGeometry.fromPoint(point))

                params.tanks_vlay.addFeatures([new_tank_feat])

            except Exception as e:
                params.tanks_vlay.destroyEditCommand()
                raise e

                params.tanks_vlay.endEditCommand()

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

                field_index = layer.dataProvider().fieldNameIndex(Junction.field_name_elev)
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
    def delete_node(params, layer, node_ft, del_ad_nodes=True):

        # The node is a junction
        if layer == params.junctions_vlay:

            # # The node is a simple node (not part of a pump or valve)
            # adj_links_fts = NetworkUtils.find_adjacent_links(parameters, node_ft.geometry())
            #
            # # Only pipes adjacent to node: it's a simple junction
            # if not adj_links_fts['pumps'] and not adj_links_fts['valves']:

                # Delete node
                NodeHandler._delete_feature(layer, node_ft)

                # Delete adjacent pipes
                if del_ad_nodes:
                    adj_pipes = NetworkUtils.find_adjacent_links(params, node_ft.geometry())
                    for adj_pipe in adj_pipes['pipes']:
                        LinkHandler.delete_link(params, params.pipes_vlay, adj_pipe)

        # The node is a reservoir or a tank
        elif layer == params.reservoirs_vlay or layer == params.tanks_vlay:

            adj_pipes = NetworkUtils.find_adjacent_links(params, node_ft.geometry())['pipes']

            NodeHandler._delete_feature(layer, node_ft)

            if del_ad_nodes:
                for adj_pipe in adj_pipes:
                    LinkHandler.delete_link(params.pipes_vlay, adj_pipe)


class LinkHandler:
    def __init__(self):
        pass

    @staticmethod
    def create_new_pipe(params, eid, diameter, loss, roughness, status, material, nodes, densify_vertices):

        pipes_caps = params.pipes_vlay.dataProvider().capabilities()
        if pipes_caps and QgsVectorDataProvider.AddFeatures:

            pipe_geom = QgsGeometry.fromPolyline(nodes)

            # Densify vertices
            dists_and_points = {}
            if densify_vertices and params.vertex_dist > 0:
                points_gen = PointsAlongLineGenerator(pipe_geom)
                dists_and_points = points_gen.get_points_coords(params.vertex_dist, False)

                # Add original vertices
                for v in range(1, len(pipe_geom.asPolyline()) - 1):
                    dist = PointsAlongLineUtils.distance(pipe_geom, QgsGeometry.fromPoint(pipe_geom.asPolyline()[v]), params.tolerance)
                    dists_and_points[dist] = pipe_geom.asPolyline()[v]

            else:
                for v in range(len(pipe_geom.asPolyline())):
                    dist = PointsAlongLineUtils.distance(pipe_geom, QgsGeometry.fromPoint(pipe_geom.asPolyline()[v]),
                                                         params.tolerance)
                    dists_and_points[dist] = pipe_geom.asPolyline()[v]

            dists_and_points = OrderedDict(sorted(dists_and_points.items()))
            pipe_geom_2 = QgsGeometry.fromPolyline(dists_and_points.values())

            line_coords = []
            for vertex in pipe_geom_2.asPolyline():
                z = raster_utils.read_layer_val_from_coord(params.dem_rlay, vertex)
                if z is None:
                    z = 0
                line_coords.append(QgsPointV2(QgsWKBTypes.PointZ, vertex.x(), vertex.y(), z))

            linestring = QgsLineStringV2()
            linestring.setPoints(line_coords)
            geom_3d = QgsGeometry(linestring)

            # Calculate 3D length
            if params.dem_rlay is not None:
                length_3d = LinkHandler.calc_3d_length(params, pipe_geom_2)
            else:
                length_3d = pipe_geom_2.length()

                params.pipes_vlay.beginEditCommand("Add new pipes")
            new_pipe_ft = None

            try:
                new_pipe_ft = QgsFeature(params.pipes_vlay.pendingFields())
                new_pipe_ft.setAttribute(Pipe.field_name_eid, eid)
                # new_pipe_ft.setAttribute(Pipe.field_name_demand, demand)
                new_pipe_ft.setAttribute(Pipe.field_name_diameter, diameter)
                new_pipe_ft.setAttribute(Pipe.field_name_length, length_3d)
                new_pipe_ft.setAttribute(Pipe.field_name_minor_loss, loss)
                new_pipe_ft.setAttribute(Pipe.field_name_roughness, roughness)
                new_pipe_ft.setAttribute(Pipe.field_name_status, status)
                new_pipe_ft.setAttribute(Pipe.field_name_material, material)

                new_pipe_ft.setGeometry(geom_3d)

                # Bug: newly created feature is selected (why?). Register previously created features
                sel_feats = params.pipes_vlay.selectedFeatures()

                params.pipes_vlay.addFeatures([new_pipe_ft])

                # Restore previously selected feature
                sel_feats_ids = []
                for sel_feat in sel_feats:
                    sel_feats_ids.append(sel_feat.id())
                params.pipes_vlay.setSelectedFeatures(sel_feats_ids)

            except Exception as e:
                params.pipes_vlay.destroyEditCommand()
                raise e

            params.pipes_vlay.endEditCommand()
            return new_pipe_ft

    @staticmethod
    def create_new_pumpvalve(params, data_dock, pipe_ft, closest_junction_ft, position, layer, attributes):

        # Find start and end nodes positions
        # Get vertex along line next to snapped point
        a, b, next_vertex = pipe_ft.geometry().closestSegmentWithContext(position)

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(position), params.tolerance)

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

        pipes_caps = params.pipes_vlay.dataProvider().capabilities()
        junctions_caps = params.junctions_vlay.dataProvider().capabilities()
        caps = layer.dataProvider().capabilities()

        if junctions_caps:
            if closest_junction_ft is not None:
                # j_demand = closest_junction_ft.attribute(Junction.field_name_demand)
                depth = closest_junction_ft.attribute(Junction.field_name_delta_z)
                pattern_id = closest_junction_ft.attribute(Junction.field_name_pattern)
            else:
                # j_demand = float(data_dock.txt_junction_demand.text())
                depth = float(data_dock.txt_junction_depth.text())
                pattern = data_dock.cbo_junction_pattern.itemData(data_dock.cbo_junction_pattern.currentIndex())
                if pattern is not None:
                    pattern_id = pattern.id
                else:
                    pattern_id = None

            junction_eid = NetworkUtils.find_next_id(params.junctions_vlay, Junction.prefix)  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(params.dem_rlay, node_before, 1)
            NodeHandler.create_new_junction(params, node_before, junction_eid, elev, 0, depth, pattern_id)

            junction_eid = NetworkUtils.find_next_id(params.junctions_vlay, Junction.prefix)  # TODO: softcode
            elev = raster_utils.read_layer_val_from_coord(params.dem_rlay, node_after, 1)
            NodeHandler.create_new_junction(params, node_after, junction_eid, elev, 0, depth, pattern_id)

        # Split the pipe and create gap
        if pipes_caps:
            gap = 1  # TODO: softcode pump length
            LinkHandler.split_pipe(params, pipe_ft, position, gap)

        # Create the new link (the pump or valve)
        if caps:

            prefix = ''
            if layer == params.pumps_vlay:
                prefix = Pump.prefix
            elif layer == params.valves_vlay:
                prefix = Valve.prefix
            eid = NetworkUtils.find_next_id(layer, prefix)  # TODO: softcode

            geom = QgsGeometry.fromPolyline([node_before, node_after])

            layer.beginEditCommand("Add new pump/valve")

            try:
                new_ft = QgsFeature(layer.pendingFields())

                if layer == params.pumps_vlay:
                    new_ft = QgsFeature(params.pumps_vlay.pendingFields())
                    new_ft.setAttribute(Pump.field_name_eid, eid)
                    param = attributes[0]
                    new_ft.setAttribute(Pump.field_name_param, param)
                    head = attributes[1]
                    new_ft.setAttribute(Pump.field_name_head, head)
                    power = attributes[2]
                    new_ft.setAttribute(Pump.field_name_power, power)
                    speed = attributes[3]
                    new_ft.setAttribute(Pump.field_name_speed, speed)

                elif layer == params.valves_vlay:
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
    def split_pipe(params, pipe_ft, split_point, gap=0):

        # Get vertex along line next to snapped point
        pipe_dist, vertex_coords, next_vertex = pipe_ft.geometry().closestSegmentWithContext(split_point)
        a, b, c, d, vertex_dist = pipe_ft.geometry().closestVertex(split_point)

        after_add = 0
        if vertex_dist < params.tolerance:
            # It was clicked on a vertex
            after_add = 1

        # Split only if vertex is not at line ends
        # demand = pipe_ft.attribute(Pipe.field_name_demand)
        p_diameter = pipe_ft.attribute(Pipe.field_name_diameter)
        loss = pipe_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe_ft.attribute(Pipe.field_name_roughness)
        status = pipe_ft.attribute(Pipe.field_name_status)
        material = pipe_ft.attribute(Pipe.field_name_material)

        # Create two new linestrings
        pipes_caps = params.pipes_vlay.dataProvider().capabilities()

        dist = PointsAlongLineUtils.distance(pipe_ft.geometry(), QgsGeometry.fromPoint(split_point), params.tolerance)
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

            params.junctions_vlay.beginEditCommand("Add new node")

            try:
                nodes = pipe_ft.geometry().asPolyline()

                # First new polyline
                pl1_pts = []
                for n in range(next_vertex):
                    pl1_pts.append(QgsPoint(nodes[n].x(), nodes[n].y()))

                pl1_pts.append(node_before.asPoint())

                pipe_eid = NetworkUtils.find_next_id(params.pipes_vlay, Pipe.prefix)
                pipe_ft_1 = LinkHandler.create_new_pipe(
                    params,
                    pipe_eid,
                    p_diameter,
                    loss,
                    roughness,
                    status,
                    material,
                    pl1_pts,
                    False)

                # Second new polyline
                pl2_pts = []
                pl2_pts.append(node_after.asPoint())
                for n in range(len(nodes) - next_vertex - after_add):
                    pl2_pts.append(QgsPoint(nodes[n + next_vertex + after_add].x(), nodes[n + next_vertex + after_add].y()))

                pipe_eid = NetworkUtils.find_next_id(params.pipes_vlay, Pipe.prefix)
                pipe_ft_2 = LinkHandler.create_new_pipe(
                    params,
                    pipe_eid,
                    p_diameter,
                    loss,
                    roughness,
                    status,
                    material,
                    pl2_pts,
                    False)

                # Delete old pipe
                params.pipes_vlay.deleteFeature(pipe_ft.id())

            except Exception as e:
                params.pipes_vlay.destroyEditCommand()
                raise e

            params.pipes_vlay.endEditCommand()

            return [pipe_ft_1, pipe_ft_2]

    @staticmethod
    def move_pipe_vertex(params, pipe_ft, new_pos_pt_v2, vertex_index):
        caps = params.pipes_vlay.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:
            params.pipes_vlay.beginEditCommand("Update pipes geometry")

            try:
                edit_utils = QgsVectorLayerEditUtils(params.pipes_vlay)
                edit_utils.moveVertexV2(new_pos_pt_v2, pipe_ft.id(), vertex_index)

                # Retrieve the feature again, and update attributes
                request = QgsFeatureRequest().setFilterFid(pipe_ft.id())
                feats = list(params.pipes_vlay.getFeatures(request))

                field_index = params.pipes_vlay.dataProvider().fieldNameIndex(Pipe.field_name_length)
                new_3d_length = LinkHandler.calc_3d_length(params, feats[0].geometry())
                params.pipes_vlay.changeAttributeValue(pipe_ft.id(), field_index, new_3d_length)

            except Exception as e:
                params.pipes_vlay.destroyEditCommand()
                raise e

            params.pipes_vlay.endEditCommand()

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
    def delete_link(params, layer, link_ft):

        # The link is a pipe
        if layer == params.pipes_vlay:
            LinkHandler._delete_feature(layer, link_ft)

        # The link is a pump or valve
        elif layer == params.pumps_vlay or layer == params.valves_vlay:

            adj_links_fts = NetworkUtils.find_adjacent_links(params, link_ft.geometry())

            if adj_links_fts['pumps']:
                adj_links_ft = adj_links_fts['pumps'][0]
            elif adj_links_fts['valves']:
                adj_links_ft = adj_links_fts['valves'][0]
            else:
                return

            adjadj_links = NetworkUtils.find_links_adjacent_to_link(params, layer,
                                                                    adj_links_ft,
                                                                    False, True, True)
            adj_nodes = NetworkUtils.find_start_end_nodes(params, adj_links_ft.geometry(),
                                                          False, True, True)

            # Stitch...
            midpoint = NetworkUtils.find_midpoint(adj_nodes[0].geometry().asPoint(),
                                                  adj_nodes[1].geometry().asPoint())

            if len(adjadj_links['pipes']) == 2:
                LinkHandler.stitch_pipes(
                    params,
                    adjadj_links['pipes'][0],
                    adj_nodes[0].geometry().asPoint(),
                    adjadj_links['pipes'][1],
                    adj_nodes[1].geometry().asPoint(),
                    midpoint)

            # Delete old links and pipes
            LinkHandler._delete_feature(layer, adj_links_ft)

            for adjadj_link in adjadj_links['pipes']:
                LinkHandler._delete_feature(params.pipes_vlay, adjadj_link)
            NodeHandler._delete_feature(params.junctions_vlay, adj_nodes[0])
            NodeHandler._delete_feature(params.junctions_vlay, adj_nodes[1])

    @staticmethod
    def delete_vertex(params, layer, pipe_ft, vertex_index):
        caps = layer.dataProvider().capabilities()

        if caps & QgsVectorDataProvider.ChangeGeometries:
            layer.beginEditCommand("Update pipe geometry")

            try:
                edit_utils = QgsVectorLayerEditUtils(params.pipes_vlay)
                edit_utils.deleteVertexV2(pipe_ft.id(), vertex_index)

                # Retrieve the feature again, and update attributes
                request = QgsFeatureRequest().setFilterFid(pipe_ft.id())
                feats = list(params.pipes_vlay.getFeatures(request))

                field_index = params.pipes_vlay.dataProvider().fieldNameIndex(Pipe.field_name_length)
                new_3d_length = LinkHandler.calc_3d_length(params, feats[0].geometry())
                params.pipes_vlay.changeAttributeValue(pipe_ft.id(), field_index, new_3d_length)

            except Exception as e:
                params.pipes_vlay.destroyEditCommand()
                raise e

            params.pipes_vlay.endEditCommand()

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

        eid = NetworkUtils.find_next_id(parameters.pipes_vlay, Pipe.prefix)

        # TODO: let the user set the attributes
        # demand = pipe1_ft.attribute(Pipe.field_name_demand)
        diameter = pipe1_ft.attribute(Pipe.field_name_diameter)
        loss = pipe1_ft.attribute(Pipe.field_name_minor_loss)
        roughness = pipe1_ft.attribute(Pipe.field_name_roughness)
        status = pipe1_ft.attribute(Pipe.field_name_status)
        material = pipe1_ft.attribute(Pipe.field_name_material)

        LinkHandler.create_new_pipe(parameters, eid, diameter, loss, roughness, status, material, new_geom_pts, False)

    @staticmethod
    def calc_3d_length(parameters, pipe_geom):

        # Check whether start and end node exist
        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(parameters, pipe_geom)

        distance_elev_od = OrderedDict()

        # Start node
        start_add = 0
        if start_node_ft is not None:
            start_node_elev = start_node_ft.attribute(Junction.field_name_elev)
            if start_node_elev is None or type(start_node_elev) is QPyNullVariant:
                start_node_elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, start_node_ft.geometry().asPoint(), 0)
                if start_node_elev is None:
                    start_node_elev = 0

            start_node_depth = start_node_ft.attribute(Junction.field_name_delta_z)
            if start_node_depth is None or type(start_node_depth) is QPyNullVariant:
                start_node_depth = 0
            start_add = 1

        # End node
        end_remove = 0
        if end_node_ft is not None:
            end_node_elev = end_node_ft.attribute(Junction.field_name_elev)
            if end_node_elev is None or type(end_node_elev) is QPyNullVariant:
                end_node_elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, end_node_ft.geometry().asPoint(), 0)
                if end_node_elev is None:
                    end_node_elev = 0
            end_node_depth = end_node_ft.attribute(Junction.field_name_delta_z)
            if end_node_depth is None or type(end_node_depth) is QPyNullVariant:
                end_node_depth = 0
            end_remove = 1

        # point_gen = PointsAlongLineGenerator(pipe_geom)
        # dists_and_points = point_gen.get_points_coords(vertex_dist, False)

        if start_node_ft is not None:
            distance_elev_od[0] = start_node_elev - start_node_depth

        vertices = pipe_geom.asPolyline()

        distances = [0]
        for p in range(1, len(vertices)):
            distances.append(distances[p-1] + QgsGeometry.fromPoint(vertices[p]).distance(QgsGeometry.fromPoint(vertices[p-1])))

        for p in range(start_add, len(vertices) - end_remove):
            elev = raster_utils.read_layer_val_from_coord(parameters.dem_rlay, vertices[p], 1)
            if elev is None:
                elev = 0
            distance_elev_od[distances[p]] = elev

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
        for node_ft in all_feats:
            if link_geom.buffer(parameters.tolerance, 5).boundingBox().contains(node_ft.geometry().asPoint()):
                cands.append(node_ft)

        if cands:
            for node_ft in cands:
                if node_ft.geometry().distance(QgsGeometry.fromPoint(link_geom.asPolyline()[0])) < parameters.tolerance:
                    intersecting_fts[0] = node_ft
                if node_ft.geometry().distance(QgsGeometry.fromPoint(link_geom.asPolyline()[-1])) < parameters.tolerance:
                    intersecting_fts[1] = node_ft

        return intersecting_fts

    @staticmethod
    def find_node_layer(params, node_geom):

        for feat in params.reservoirs_vlay.getFeatures():
            if NetworkUtils.points_overlap(node_geom, feat.geometry(), params.tolerance):
                return params.reservoirs_vlay

        for feat in params.tanks_vlay.getFeatures():
            if NetworkUtils.points_overlap(node_geom, feat.geometry(), params.tolerance):
                return params.tanks_vlay

        for feat in params.junctions_vlay.getFeatures():
            if NetworkUtils.points_overlap(node_geom, feat.geometry(), params.tolerance):
                return params.junctions_vlay

    @staticmethod
    def find_adjacent_links(params, node_geom):

        adjacent_links_d = {'pumps': [], 'valves': []}

        # Search among pipes
        adjacent_pipes_fts = []
        for pipe_ft in params.pipes_vlay.getFeatures():
            pipe_geom = pipe_ft.geometry()
            nodes = pipe_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0]), params.tolerance) or\
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1]), params.tolerance):
                adjacent_pipes_fts.append(pipe_ft)

        adjacent_links_d['pipes'] = adjacent_pipes_fts

        if len(adjacent_pipes_fts) > 2:
            # It's a pure junction, cannot be a pump or valve
            return adjacent_links_d

        # Search among pumps
        adjacent_pumps_fts = []
        for pump_ft in params.pumps_vlay.getFeatures():
            pump_geom = pump_ft.geometry()
            nodes = pump_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0]), params.tolerance) or \
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1]), params.tolerance):
                adjacent_pumps_fts.append(pump_ft)

        adjacent_links_d['pumps'] = adjacent_pumps_fts

        # Search among valves
        adjacent_valves_fts = []
        for valve_ft in params.valves_vlay.getFeatures():
            valve_geom = valve_ft.geometry()
            nodes = valve_geom.asPolyline()
            if NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[0]), params.tolerance) or \
                    NetworkUtils.points_overlap(node_geom, QgsGeometry.fromPoint(nodes[len(nodes) - 1]), params.tolerance):
                adjacent_valves_fts.append(valve_ft)

        adjacent_links_d['valves'] = adjacent_valves_fts

        return adjacent_links_d

    @staticmethod
    def find_next_id(vlay, prefix):

        features = vlay.getFeatures()
        max_eid = -1
        for feat in features:
            eid = feat.attribute(Junction.field_name_eid)

            # Check whether there's an eid using the prefix-number format
            format_used = False
            if eid.startswith(prefix):
                number = eid[len(prefix):len(eid)]
                try:
                    int(number)
                    format_used = True
                except ValueError:
                    pass

            if format_used:
                eid_val = int(eid[len(prefix):len(eid)])
            else:
                eid_val = 0
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
    def find_pumps_valves_junctions(params):
        """Find junctions adjacent to pumps and valves"""

        adj_points = []

        pump_fts = params.pumps_vlay.getFeatures()
        for pump_ft in pump_fts:
            (start, end) = NetworkUtils.find_start_end_nodes(pump_ft.geometry(), False, True, True)
            if start is not None:
                adj_points.append(start.geometry().asPoint())
            if end is not None:
                adj_points.append(end.geometry().asPoint())

        valve_fts = params.valves_vlay.getFeatures()
        for valve_ft in valve_fts:
            (start, end) = NetworkUtils.find_start_end_nodes(valve_ft.geometry(), False, True, True)
            if start is not None:
                adj_points.append(start.geometry().asPoint())
            if end is not None:
                adj_points.append(end.geometry().asPoint())

        return adj_points

    @staticmethod
    def find_links_adjacent_to_link(
            parameters,
            link_vlay,
            link_ft,
            exclude_pipes=False,
            exclude_pumps=False,
            exclude_valves=False):
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
    def look_for_adjacent_links(params, link_ft, link_vlay, search_vlay):

        link_pts = link_ft.geometry().asPolyline()

        adj_links = []
        for ft in search_vlay.getFeatures():
            pts = ft.geometry().asPolyline()
            if NetworkUtils.points_overlap(pts[0], link_pts[0], params.tolerance) or \
                    NetworkUtils.points_overlap(pts[0], link_pts[-1], params.tolerance) or \
                    NetworkUtils.points_overlap(pts[-1], link_pts[0], params.tolerance) or \
                    NetworkUtils.points_overlap(pts[-1], link_pts[-1], params.tolerance):

                # Check that the feature found is not the same as the input
                if not (link_vlay.id() == search_vlay.id() and link_ft.id() != ft.id()):
                    adj_links.append(ft)

        return adj_links

    @staticmethod
    def find_overlapping_nodes(params, point):

        overlap_juncts = []
        overlap_reservs = []
        overlap_tanks = []

        for junct_feat in params.junctions_vlay.getFeatures():
            if NetworkUtils.points_overlap(junct_feat.geometry(), point, params.tolerance):
                overlap_juncts.append(junct_feat)
                break

        for reserv_feat in params.reservoirs_vlay.getFeatures():
            if NetworkUtils.points_overlap(reserv_feat.geometry(), point, params.tolerance):
                overlap_reservs.append(reserv_feat)
                break

        for tank_feat in params.tanks_vlay.getFeatures():
            if NetworkUtils.points_overlap(tank_feat.geometry(), point, params.tolerance):
                overlap_tanks.append(tank_feat)
                break

        return {'junctions': overlap_juncts, 'reservoirs': overlap_reservs, 'tanks': overlap_tanks }

    @staticmethod
    def find_midpoint(point1, point2):

        mid_x = (point1.x() + point2.x()) / 2
        mid_y = (point1.y() + point2.y()) / 2

        return QgsPoint(mid_x, mid_y)