# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QCursor, QColor
from qgis.core import QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsTolerance, QgsSnapper,\
    QgsVector, QgsVertexId, QgsPointV2
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
        self.data_dock = data_dock
        """:type : DataDock"""
        self.params = params

        self.elev = -1
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.mouse_clicked = False
        self.snapper = None

        self.clicked_pt = None

        self.snap_results = None
        self.adj_links_fts = None

        self.selected_node_ft = None
        self.selected_node_ft_lay = None
        self.mouse_pt = None
        self.pump_valve_selected = False
        self.pump_or_valve = None
        self.pump_valve_ft = None
        self.adj_junctions = None
        self.delta_vec = None

        self.rubber_bands_d = {}

        self.adj_pipes_fts_d = {}

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
            for snap_result in self.snap_results:
                if snap_result.layer.name() == self.params.junctions_vlay.name() or\
                        snap_result.layer.name() == self.params.reservoirs_vlay.name() or\
                        snap_result.layer.name() == self.params.tanks_vlay.name():

                    node_feat_id = snap_result.snappedAtGeometry
                    request = QgsFeatureRequest().setFilterFid(node_feat_id)
                    node = list(snap_result.layer.getFeatures(request))
                    self.selected_node_ft = QgsFeature(node[0])
                    self.selected_node_ft_lay = snap_result.layer
                    self.adj_links_fts = NetworkUtils.find_adjacent_links(self.params, self.selected_node_ft.geometry())

            # No selected nodes: it's just a vertex
            if self.selected_node_ft is None:

                self.rubber_bands_d[0] = QgsRubberBand(self.canvas(), False)  # False = not a polygon
                points = []
                points.append(self.snap_results[0].beforeVertex)
                points.append(self.snap_results[0].snappedVertex)
                points.append(self.snap_results[0].afterVertex)

                self.rubber_bands_d[0].setToGeometry(QgsGeometry.fromPolyline(points), None)
                self.rubber_bands_d[0].setColor(QColor(255, 128, 128))
                self.rubber_bands_d[0].setWidth(1)
                self.rubber_bands_d[0].setBrushStyle(Qt.Dense4Pattern)

            # It's a node
            else:

                # Only pipes adjacent to node
                if not self.adj_links_fts['pumps'] and not self.adj_links_fts['valves']:

                    self.pump_valve_selected = False
                    rb_index = 0

                    for adjacent_pipes_ft in self.adj_links_fts['pipes']:
                        closest = adjacent_pipes_ft.geometry().closestVertex(self.selected_node_ft.geometry().asPoint())

                        if closest[1] == 0:
                            next_vertext_id = closest[1] + 1
                        else:
                            next_vertext_id = closest[1] - 1

                        self.adj_pipes_fts_d[adjacent_pipes_ft] = closest[1]

                        rubber_band_start_pt = adjacent_pipes_ft.geometry().vertexAt(next_vertext_id)

                        self.rubber_bands_d[rb_index] = QgsRubberBand(self.canvas(), False)  # False = not a polygon
                        points = [rubber_band_start_pt, self.selected_node_ft.geometry().asPoint()]
                        self.rubber_bands_d[rb_index].setToGeometry(QgsGeometry.fromPolyline(points), None)
                        self.rubber_bands_d[rb_index].setColor(QColor(255, 128, 128))
                        self.rubber_bands_d[rb_index].setWidth(1)
                        self.rubber_bands_d[rb_index].setBrushStyle(Qt.Dense4Pattern)

                        rb_index += 1

                # Node adjacent to pump or valve
                else:

                    self.pump_valve_selected = True

                    if self.adj_links_fts['pumps'] or self.adj_links_fts['valves']:

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

                        adj_pipes = adj_links['pipes']

                        # Find the nodes adjacent to the pump/valve
                        self.adj_junctions = NetworkUtils.find_start_end_nodes(self.params, self.pump_valve_ft.geometry())

                        pump_valve = self.pump_valve_ft.geometry().asPolyline()

                        adj_pipe_pts_1 = adj_pipes[0].geometry().asPolyline()
                        if NetworkUtils.points_overlap(pump_valve[0], adj_pipe_pts_1[0], self.params.tolerance) or \
                                NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve[0]), adj_pipe_pts_1[-1], self.params.tolerance):
                            closest_1 = adj_pipes[0].geometry().closestVertex(pump_valve[0])

                            self.adj_pipes_fts_d[adj_pipes[0]] = closest_1[1]

                        adj_pipe_pts_2 = adj_pipes[1].geometry().asPolyline()
                        if NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve[1]), adj_pipe_pts_2[0], self.params.tolerance) or \
                                NetworkUtils.points_overlap(QgsGeometry.fromPoint(pump_valve[1]), adj_pipe_pts_2[-1], self.params.tolerance):
                            closest_2 = adj_pipes[1].geometry().closestVertex(pump_valve[1])

                            self.adj_pipes_fts_d[adj_pipes[1]] = closest_2[1]

                    if closest_1[1] == 0:
                        second_last_1 = closest_1[1] + 1
                    else:
                        second_last_1 = closest_1[1] - 1

                    if closest_2[1] == 0:
                        second_last_2 = closest_2[1] + 1
                    else:
                        second_last_2 = closest_2[1] - 1

                    self.rubber_bands_d[0] = QgsRubberBand(self.canvas(), False)  # False = not a polygon
                    points = []
                    points.append(adj_pipe_pts_1[second_last_1])
                    points.append(QgsPoint(closest_1[0][0], closest_1[0][1]))
                    points.append(QgsPoint(closest_2[0][0], closest_2[0][1]))
                    points.append(adj_pipe_pts_2[second_last_2])

                    self.rubber_bands_d[0].setToGeometry(QgsGeometry.fromPolyline(points), None)
                    self.rubber_bands_d[0].setColor(QColor(255, 128, 128))
                    self.rubber_bands_d[0].setWidth(1)
                    self.rubber_bands_d[0].setBrushStyle(Qt.Dense4Pattern)

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, self.mouse_pt, 1)
        if elev is not None:
            self.elev = elev
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        # Mouse not clicked
        if not self.mouse_clicked:

            (retval, results) = self.snapper.snapMapPoint(self.toMapCoordinates(event.pos()))

            if results:

                self.snap_results = results

                snapped_pt = self.snap_results[0].snappedVertex

                self.vertex_marker.setCenter(QgsPoint(snapped_pt.x(), snapped_pt.y()))
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
            # Update rubber bands
            if self.snap_results is not None:

                if self.adj_links_fts is None:

                    snapped_pt = self.snap_results[0].snappedVertex
                    self.rubber_bands_d[0].movePoint(1, self.mouse_pt)

                else:

                    # It's just a junction
                    if not self.pump_valve_selected:
                        for key, value in self.rubber_bands_d.iteritems():
                            self.rubber_bands_d[key].movePoint(1, self.mouse_pt)

                    # It's a pump/valve
                    else:
                        snapped_pt = self.snap_results[0].snappedVertex

                        self.delta_vec = QgsVector(self.mouse_pt.x() - snapped_pt.x(), self.mouse_pt.y() - snapped_pt.y())
                        # In 2.16+: self.delta_vec = QgsVector(self.mouse_pt - snapped_pt)

                        for key, value in self.rubber_bands_d.iteritems():
                            self.rubber_bands_d[key].movePoint(1, QgsPoint(snapped_pt.x() + self.delta_vec.x(), snapped_pt.y() + self.delta_vec.y()))
                            # in 2.16: self.rubber_bands_d[key].movePoint(1, snapped_pt + self.delta_vec)
                            self.rubber_bands_d[key].movePoint(2, QgsPoint(snapped_pt.x() + self.delta_vec.x(), snapped_pt.y() + self.delta_vec.y()))
                            # in 2.16: self.rubber_bands_d[key].movePoint(2, snapped_pt + self.delta_vec)

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return
        if event.button() == 1:
            self.mouse_clicked = False

            # Remove rubber bands
            for key in self.rubber_bands_d.keys():
                self.iface.mapCanvas().scene().removeItem(self.rubber_bands_d[key])
                del self.rubber_bands_d[key]

            if self.snap_results is not None:

                # No adjacent links: it's just a pipe vertex
                if self.adj_links_fts is None:
                    feat = vector_utils.get_feats_by_id(self.snap_results[0].layer, self.snap_results[0].snappedAtGeometry)

                    vertex_id = QgsVertexId(0, 0, self.snap_results[0].snappedVertexNr, QgsVertexId.SegmentVertex)
                    vertex_v2 = feat[0].geometry().geometry().vertexAt(vertex_id)

                    new_pos_pt_v2 = QgsPointV2(self.mouse_pt.x(), self.mouse_pt.y())
                    new_pos_pt_v2.addZValue(vertex_v2.z())

                    LinkHandler.move_pipe_vertex(self.params, feat[0], new_pos_pt_v2, self.snap_results[0].snappedVertexNr)

                # It's a node
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
                        for feat, vertex_index in self.adj_pipes_fts_d.iteritems():

                            vertex_id = QgsVertexId(0, 0, vertex_index, QgsVertexId.SegmentVertex)
                            vertex_v2 = feat.geometry().geometry().vertexAt(vertex_id)
                            new_pos_pt_v2 = QgsPointV2(self.mouse_pt.x(), self.mouse_pt.y())
                            new_pos_pt_v2.addZValue(vertex_v2.z())

                            LinkHandler.move_pipe_vertex(self.params, feat, new_pos_pt_v2, vertex_index)

                    # Pump or valve
                    else:

                        # Update junctions geometry
                        NodeHandler.move_element(self.params.junctions_vlay,
                                                 self.params.dem_rlay,
                                                 self.adj_junctions[0],
                                                 QgsPoint(
                                                    self.adj_junctions[0].geometry().asPoint().x() + self.delta_vec.x(),
                                                    self.adj_junctions[0].geometry().asPoint().y() + self.delta_vec.y()))

                        NodeHandler.move_element(self.params.junctions_vlay,
                                                 self.params.dem_rlay,
                                                 self.adj_junctions[1],
                                                 QgsPoint(
                                                     self.adj_junctions[1].geometry().asPoint().x() + self.delta_vec.x(),
                                                     self.adj_junctions[1].geometry().asPoint().y() + self.delta_vec.y()))

                        # in 2.16: NodeHandler.move_element(Parameters.junctions_vlay, self.adj_junctions[0], self.adj_junctions[0].geometry().asPoint() + self.delta_vec)
                        # in 2.16: NodeHandler.move_element(Parameters.junctions_vlay, self.adj_junctions[1], self.adj_junctions[1].geometry().asPoint() + self.delta_vec)

                        # Pump or valve
                        if self.pump_or_valve == 'pump':
                            lay = self.params.pumps_vlay
                        elif self.pump_or_valve == 'valve':
                            lay = self.params.valves_vlay

                        # Move the pump/valve
                        LinkHandler.move_pump_valve(lay, self.pump_valve_ft, self.delta_vec)

                        # Move the adjacent pipes' vertices
                        for feat, vertex_index in self.adj_pipes_fts_d.iteritems():


                            vertex_id = QgsVertexId(0, 0, vertex_index, QgsVertexId.SegmentVertex)
                            vertex_v2 = feat.geometry().geometry().vertexAt(vertex_id)
                            new_pos_pt_v2 = QgsPointV2(
                                feat.geometry().vertexAt(vertex_index).x() + self.delta_vec.x(),
                                feat.geometry().vertexAt(vertex_index).y() + self.delta_vec.y())
                            new_pos_pt_v2.addZValue(vertex_v2.z())

                            LinkHandler.move_pipe_vertex(self.params, feat, new_pos_pt_v2, vertex_index)
                            # In 2.16: LinkHandler.move_pipe_vertex(feat, feat.geometry().vertexAt(vertex_index) + self.delta_vec, vertex_index)

                    self.adj_pipes_fts_d.clear()

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
        QgsProject.instance().setSnapSettingsForLayer(self.params.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.tanks_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(self.params.junctions_vlay)
        snap_layer_reservoirs = NetworkUtils.set_up_snap_layer(self.params.reservoirs_vlay)
        snap_layer_tanks = NetworkUtils.set_up_snap_layer(self.params.tanks_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay)

        self.snapper = NetworkUtils.set_up_snapper(
            [snap_layer_junctions, snap_layer_reservoirs, snap_layer_tanks, snap_layer_pipes],
            self.iface.mapCanvas())

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
        self.data_dock.btn_move_element.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True