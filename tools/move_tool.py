# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QCursor, QColor
from qgis.core import QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsTolerance, QgsSnapper,\
    QgsVector, QgsVertexId, QgsPointV2, QgsPointLocator
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand

from ..model.network_handling import NetworkUtils, NodeHandler, LinkHandler
from parameters import Parameters
from ..geo_utils import raster_utils, vector_utils
from ..rendering import symbology


class MoveTool(QgsMapTool):

    def __init__(self, data_dock, params):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.dock_widget = data_dock
        """:type : DataDock"""
        self.params = params

        self.elev = -1
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.mouse_clicked = False
        self.snapper = None

        self.clicked_pt = None

        self.snap_results = None

        self.selected_node_ft = None
        self.selected_node_ft_lay = None
        self.mouse_pt = None
        self.pump_valve_selected = False
        self.pump_or_valve = None
        self.pump_valve_ft = None
        self.adj_links_fts = None
        self.adj_junctions = None
        self.delta_vec = QgsVector(0, 0)
        self.adj_links_fts_d = {}

        self.rubber_bands_d = {}
        self.rubber_bands_geoms_d = {}

    def canvasPressEvent(self, event):

        if self.snap_results is None:
            self.clicked_pt = None
            return

        if event.button() == Qt.RightButton:
            self.mouse_clicked = False
            self.clicked_pt = None

        if event.button() == Qt.LeftButton:

            self.mouse_clicked = True

            # Check if a node was snapped: it can be just one
            self.selected_node_ft = None
            self.adj_links_fts = None

            if self.snap_results.layer().name() == self.params.junctions_vlay.name() or \
                            self.snap_results.layer().name() == self.params.reservoirs_vlay.name() or \
                            self.snap_results.layer().name() == self.params.tanks_vlay.name():

                node_feat_id = self.snap_results.featureId()
                request = QgsFeatureRequest().setFilterFid(node_feat_id)
                node = list(self.snap_results.layer().getFeatures(request))
                self.selected_node_ft = QgsFeature(node[0])

                self.selected_node_ft_lay = self.snap_results.layer()
                self.adj_links_fts = NetworkUtils.find_adjacent_links(self.params, self.selected_node_ft.geometry())

            # No selected nodes: it's just a vertex
            if self.selected_node_ft is None:

                snapped_ft = vector_utils.get_feats_by_id(self.snap_results.layer(), self.snap_results.featureId())[0]
                snapped_ft_geom = snapped_ft.geometry()


                print self.snap_results.vertexIndex() - 1

                if self.snap_results.vertexIndex() - 1 >= 0 and self.snap_results.vertexIndex() < len( snapped_ft_geom.asPolyline()):
                    vertex_before = snapped_ft_geom.vertexAt(self.snap_results.vertexIndex() - 1)

                vertex_at = snapped_ft_geom.vertexAt(self.snap_results.vertexIndex())

                if self.snap_results.vertexIndex() + 1 >= 0 and self.snap_results.vertexIndex() < len(snapped_ft_geom.asPolyline()):
                    vertex_after = snapped_ft_geom.vertexAt(self.snap_results.vertexIndex() + 1)

                points = []
                points.append(vertex_before)
                points.append(vertex_at)
                points.append(vertex_after)
                
                self.rubber_bands_d[0] = (self.build_rubber_band(points), [1], [vertex_at])

            # It's a node
            else:

                # Adjacent links are neither pumps nor valves: find the two pipes adjacent to the node
                # Or node adjacent to pump or valve and NOT using block logic
                if (not self.adj_links_fts['pumps'] and not self.adj_links_fts['valves']) or not self.params.block_logic:

                    self.pump_valve_selected = False

                    rb_points = []

                    rb_index = 0
                    for adjacent_pipes_ft in self.adj_links_fts['pipes']:
                        closest = adjacent_pipes_ft.geometry().closestVertex(self.selected_node_ft.geometry().asPoint())
                        self.adj_links_fts_d[adjacent_pipes_ft] = (closest[1], self.params.pipes_vlay)
                        if closest[1] == 0:
                            next_vertext_id = closest[1] + 1
                        else:
                            next_vertext_id = closest[1] - 1
                        rb_points.append(adjacent_pipes_ft.geometry().vertexAt(next_vertext_id))

                    for adj_pumps_ft in self.adj_links_fts['pumps']:
                        closest = adj_pumps_ft.geometry().closestVertex(self.selected_node_ft.geometry().asPoint())
                        self.adj_links_fts_d[adj_pumps_ft] = (closest[1], self.params.pumps_vlay)
                        if closest[1] == 0:
                            next_vertext_id = closest[1] + 1
                        else:
                            next_vertext_id = closest[1] - 1
                        rb_points.append(adj_pumps_ft.geometry().vertexAt(next_vertext_id))

                    for adj_valves_ft in self.adj_links_fts['valves']:
                        closest = adj_valves_ft.geometry().closestVertex(self.selected_node_ft.geometry().asPoint())
                        self.adj_links_fts_d[adj_valves_ft] = (closest[1], self.params.valves_vlay)
                        if closest[1] == 0:
                            next_vertext_id = closest[1] + 1
                        else:
                            next_vertext_id = closest[1] - 1
                        rb_points.append(adj_valves_ft.geometry().vertexAt(next_vertext_id))

                    rb_points.insert(1, self.selected_node_ft.geometry().asPoint())
                    self.rubber_bands_d[0] = (self.build_rubber_band(rb_points), [1], [self.selected_node_ft.geometry().asPoint()])

                # Node adjacent to pump or valve and using block logic
                else:

                    self.pump_valve_selected = True

                    # Find the pipes adjacent to the pump/valve
                    if self.adj_links_fts['pumps']:
                        self.pump_valve_ft = self.adj_links_fts['pumps'][0]
                        self.pump_or_valve = 'pump'
                        adj_links = NetworkUtils.find_links_adjacent_to_link(self.params, self.params.pumps_vlay, self.pump_valve_ft, False, True, True)
                    elif self.adj_links_fts['valves']:
                        self.pump_valve_ft = self.adj_links_fts['valves'][0]
                        self.pump_or_valve = 'valve'
                        adj_links = NetworkUtils.find_links_adjacent_to_link(self.params, self.params.valves_vlay, self.pump_valve_ft, False, True, True)
                    else:
                        return

                    pump_valve_pts = self.pump_valve_ft.geometry().asPolyline()

                    self.rubber_bands_d[0] = (self.build_rubber_band(pump_valve_pts), range(len(pump_valve_pts)), pump_valve_pts)

                    rb_index = 1
                    if 'pipes' in adj_links:
                        for adj_link_ft in adj_links['pipes']:
                            self.process_adj(adj_link_ft, self.params.pipes_vlay, rb_index)
                            rb_index += 1
                    if 'pumps' in adj_links:
                        for adj_link_ft in adj_links['pumps']:
                            self.process_adj(adj_link_ft, self.params.pumps_vlay, rb_index)
                            rb_index += 1
                    if 'valves' in adj_links:
                        for adj_link_ft in adj_links['valves']:
                            self.process_adj(adj_link_ft, self.params.valves_vlay, rb_index)
                            rb_index += 1

                    # Find the nodes adjacent to the pump/valve
                    self.adj_junctions = NetworkUtils.find_start_end_nodes_w_layer(self.params, self.pump_valve_ft.geometry())

    def process_adj(self, adj_link_ft, layer, rb_index):

        adj_link_pts = adj_link_ft.geometry().asPolyline()
        pump_valve_pts = self.pump_valve_ft.geometry().asPolyline()

        if NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve_pts[0]), adj_link_pts[0], self.params.tolerance):
            self.adj_links_fts_d[adj_link_ft] = (0, layer)
            rb_pts = [pump_valve_pts[0], adj_link_pts[1]]
            self.rubber_bands_d[rb_index] = (self.build_rubber_band(rb_pts), [0], [pump_valve_pts[0]])

        if NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve_pts[-1]), adj_link_pts[0], self.params.tolerance):
            self.adj_links_fts_d[adj_link_ft] = (0, layer)
            rb_pts = [pump_valve_pts[-1], adj_link_pts[1]]
            self.rubber_bands_d[rb_index] = (self.build_rubber_band(rb_pts), [0], [pump_valve_pts[-1]])

        if NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve_pts[0]), adj_link_pts[-1], self.params.tolerance):
            self.adj_links_fts_d[adj_link_ft] = (len(adj_link_pts)-1, layer)
            rb_pts = [pump_valve_pts[0], adj_link_pts[-2]]
            self.rubber_bands_d[rb_index] = (self.build_rubber_band(rb_pts), [0], [pump_valve_pts[0]])

        if NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve_pts[-1]), adj_link_pts[-1], self.params.tolerance):
            self.adj_links_fts_d[adj_link_ft] = (len(adj_link_pts)-1, layer)
            rb_pts = [pump_valve_pts[-1], adj_link_pts[-2]]
            self.rubber_bands_d[rb_index] = (self.build_rubber_band(rb_pts), [0], [pump_valve_pts[-1]])

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, self.mouse_pt, 1)
        if elev is not None:
            self.elev = elev
            self.dock_widget.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        # Mouse not clicked
        if not self.mouse_clicked:

            match = self.snapper.snapToMap(self.mouse_pt)
            if match.isValid():

                self.snap_results = match
                # snapped_pt = self.snap_results[0].snappedVertex
                snapped_vertex = match.point()

                self.vertex_marker.setCenter(QgsPoint(snapped_vertex.x(), snapped_vertex.y()))
                self.vertex_marker.setColor(QColor(255, 0, 0))
                self.vertex_marker.setIconSize(10)
                self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)  # or ICON_CROSS, ICON_X
                self.vertex_marker.setPenWidth(3)
                self.vertex_marker.show()
            else:
                self.snap_results = None
                self.selected_node_ft = None
                self.vertex_marker.hide()

        # Mouse clicked
        else:

            # Mouse clicked and vertex selected
            # Update rubber band
            if self.snap_results is not None:

                snapped_pt = self.snap_results.point()

                self.delta_vec = QgsVector(self.mouse_pt.x() - snapped_pt.x(),
                                           self.mouse_pt.y() - snapped_pt.y())

                # In 2.16+: self.delta_vec = QgsVector(self.mouse_pt - snapped_pt)

                if self.adj_links_fts is None:

                    # snapped_pt = self.snap_results[0].snappedVertex
                    # self.rubber_bands_d[0][0].movePoint(self.rubber_bands_d[0][1], self.mouse_pt)
                    self.move_rubber_band_pt(self.rubber_bands_d[0])

                else:

                    # It's just a junction
                    if not self.pump_valve_selected:
                        for key, value in self.rubber_bands_d.iteritems():
                            # self.rubber_bands_d[key][0].movePoint(self.rubber_bands_d[key][1], self.mouse_pt)
                            self.move_rubber_band_pt(self.rubber_bands_d[key])

                    # It's a pump/valve
                    else:

                        # Adjacent links are neither pumps nor valves: find the two pipes adjacent to the node
                        # Or node adjacent to pump or valve and NOT using block logic
                        if (not self.adj_links_fts['pumps'] and not self.adj_links_fts['valves']) or not self.params.block_logic:

                            for key, value in self.rubber_bands_d.iteritems():
                                self.move_rubber_band_pt(self.rubber_bands_d[key])
                                # in 2.16: self.rubber_bands_d[key].movePoint(1, snapped_pt + self.delta_vec)
                                # self.rubber_bands_d[key].movePoint(2, QgsPoint(snapped_pt.x() + self.delta_vec.x(), snapped_pt.y() + self.delta_vec.y()))

                        # Node adjacent to pump or valve and using block logic
                        else:
                            for key, value in self.rubber_bands_d.iteritems():
                                self.move_rubber_band_pt(self.rubber_bands_d[key])

    def move_rubber_band_pt(self, rubber_band_v):
        rubber_band = rubber_band_v[0]
        pt_indices = rubber_band_v[1]
        start_pts = rubber_band_v[2]

        for i in range(len(pt_indices)):
            rubber_band.movePoint(pt_indices[i], QgsPoint(start_pts[i].x() + self.delta_vec.x(), start_pts[i].y() + self.delta_vec.y()))

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return
        if event.button() == 1:
            self.mouse_clicked = False

            # Remove rubber band
            for key in self.rubber_bands_d.keys():
                self.iface.mapCanvas().scene().removeItem(self.rubber_bands_d[key][0])
                del self.rubber_bands_d[key]

            if self.snap_results is not None:

                # No adjacent links: it's just a pipe vertex
                if self.adj_links_fts is None:
                    feat = vector_utils.get_feats_by_id(self.snap_results.layer(), self.snap_results.featureId())

                    vertex_id = QgsVertexId(0, 0, self.snap_results.vertexIndex(), QgsVertexId.SegmentVertex)
                    vertex_v2 = feat[0].geometry().geometry().vertexAt(vertex_id)

                    new_pos_pt_v2 = QgsPointV2(self.mouse_pt.x(), self.mouse_pt.y())
                    new_pos_pt_v2.addZValue(vertex_v2.z())

                    LinkHandler.move_link_vertex(self.params, self.params.pipes_vlay, feat[0], new_pos_pt_v2, self.snap_results.vertexIndex())

                # There are adjacent links: it's a node
                else:

                    # Not pump or valve: plain junction
                    if not self.pump_valve_selected:

                        # Update junction geometry
                        NodeHandler.move_element(
                            self.selected_node_ft_lay,
                            self.params.dem_rlay,
                            self.selected_node_ft,
                            self.mouse_pt)

                        # Update pipes
                        for feat, (vertex_index, layer) in self.adj_links_fts_d.iteritems():

                            vertex_id = QgsVertexId(0, 0, vertex_index, QgsVertexId.SegmentVertex)
                            vertex_v2 = feat.geometry().geometry().vertexAt(vertex_id)
                            new_pos_pt_v2 = QgsPointV2(self.mouse_pt.x(), self.mouse_pt.y())
                            new_pos_pt_v2.addZValue(vertex_v2.z())

                            LinkHandler.move_link_vertex(self.params, layer, feat, new_pos_pt_v2, vertex_index)

                    # Pump or valve
                    else:

                        # Update junctions geometry
                        NodeHandler.move_element(self.adj_junctions[0][1],
                                                 self.params.dem_rlay,
                                                 self.adj_junctions[0][0],
                                                 QgsPoint(
                                                    self.adj_junctions[0][0].geometry().asPoint().x() + self.delta_vec.x(),
                                                    self.adj_junctions[0][0].geometry().asPoint().y() + self.delta_vec.y()))

                        NodeHandler.move_element(self.adj_junctions[1][1],
                                                 self.params.dem_rlay,
                                                 self.adj_junctions[1][0],
                                                 QgsPoint(
                                                     self.adj_junctions[1][0].geometry().asPoint().x() + self.delta_vec.x(),
                                                     self.adj_junctions[1][0].geometry().asPoint().y() + self.delta_vec.y()))

                        # in 2.16: NodeHandler.move_element(Parameters.junctions_vlay, self.adj_links_fts[0], self.adj_links_fts[0].geometry().asPoint() + self.delta_vec)

                        if self.pump_or_valve == 'pump':
                            lay = self.params.pumps_vlay
                        elif self.pump_or_valve == 'valve':
                            lay = self.params.valves_vlay

                        # Move the pump/valve
                        LinkHandler.move_pump_valve(lay, self.pump_valve_ft, self.delta_vec)

                        # Move the adjacent pipes' vertices
                        for feat, (vertex_index, layer) in self.adj_links_fts_d.iteritems():

                            vertex_id = QgsVertexId(0, 0, vertex_index, QgsVertexId.SegmentVertex)
                            vertex_v2 = feat.geometry().geometry().vertexAt(vertex_id)
                            new_pos_pt_v2 = QgsPointV2(
                                feat.geometry().vertexAt(vertex_index).x() + self.delta_vec.x(),
                                feat.geometry().vertexAt(vertex_index).y() + self.delta_vec.y())
                            new_pos_pt_v2.addZValue(vertex_v2.z())

                            LinkHandler.move_link_vertex(self.params, layer, feat, new_pos_pt_v2, vertex_index)
                            # In 2.16: LinkHandler.move_pipe_vertex(feat, feat.geometry().vertexAt(vertex_index) + self.delta_vec, vertex_index)

                    self.adj_links_fts_d.clear()

                symbology.refresh_layer(self.iface.mapCanvas(), self.params.junctions_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.params.reservoirs_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.params.tanks_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.params.pipes_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.params.pumps_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.params.valves_vlay)

    def activate(self):

        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        # Snapping
        layers = {
            self.params.junctions_vlay: QgsPointLocator.Vertex,
            self.params.reservoirs_vlay: QgsPointLocator.Vertex,
            self.params.tanks_vlay: QgsPointLocator.Vertex,
            self.params.pipes_vlay: QgsPointLocator.Vertex}
        self.snapper = NetworkUtils.set_up_snapper(layers, self.iface.mapCanvas(), self.params.snap_tolerance)

        # Editing
        if not self.params.junctions_vlay.isEditable():
            self.params.junctions_vlay.startEditing()
        if not self.params.reservoirs_vlay.isEditable():
            self.params.reservoirs_vlay.startEditing()
        if not self.params.tanks_vlay.isEditable():
            self.params.tanks_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()
        if not self.params.pumps_vlay.isEditable():
            self.params.pumps_vlay.startEditing()
        if not self.params.valves_vlay.isEditable():
            self.params.valves_vlay.startEditing()

    def deactivate(self):
        self.rubber_bands_d.clear()
        self.canvas().scene().removeItem(self.vertex_marker)
        self.dock_widget.btn_move_element.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def build_rubber_band(self, points):
        rubber_band = QgsRubberBand(self.canvas(), False)  # False = not a polygon
        rubber_band.setToGeometry(QgsGeometry.fromPolyline(points), None)
        # for point in points:
        #     rubber_band.addPoint(point)
        rubber_band.setColor(QColor(255, 128, 128))
        rubber_band.setWidth(1)
        rubber_band.setBrushStyle(Qt.Dense4Pattern)
        return rubber_band
