# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QCursor, QColor
from qgis.core import QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsTolerance, QgsSnapper
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand

from network_handling import NetworkUtils, NodeHandler, LinkHandler
from parameters import Parameters


class MoveNodeTool(QgsMapTool):

    def __init__(self, data_dock):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""

        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.mouse_clicked = False
        self.snapper = None
        self.snapped_lay = None
        self.snapped_feat_id = None
        self.selected_node_ft = None
        self.mouse_pt = None

        self.rubber_bands_d = {}

        self.adj_pipes_fts_d = {}

        self.snapped_feat_id = None

    def canvasPressEvent(self, event):

        if self.snapped_feat_id is None:
            return

        if event.button() == Qt.RightButton:
            self.mouse_clicked = False

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True
            request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
            junctions_list = [feat for feat in Parameters.junctions_vlay.getFeatures(request)]
            self.selected_node_ft = QgsFeature(junctions_list[0])

            adjacent_pipes_fts = NetworkUtils.find_adjacent_pipes(self.selected_node_ft.geometry())

            rb_index = 0
            for adjacent_pipes_ft in adjacent_pipes_fts:
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

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        if not self.mouse_clicked:

            (retval, result) = self.snapper.snapMapPoint(self.toMapCoordinates(event.pos()))

            if len(result) > 0:

                self.snapped_feat_id = result[0].snappedAtGeometry
                self.snapped_lay = result[0].layer

                snapped_vertex = result[0].snappedVertex

                self.vertex_marker.setCenter(QgsPoint(snapped_vertex.x(), snapped_vertex.y()))
                self.vertex_marker.setColor(QColor(255, 0, 0))
                self.vertex_marker.setIconSize(10)
                self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)  # or ICON_CROSS, ICON_X
                self.vertex_marker.setPenWidth(3)
                self.vertex_marker.show()
            else:
                self.snapped_feat_id = None
                self.vertex_marker.hide()
                self.selected_node_ft = None

        else:
            if self.snapped_feat_id is not None:
                # Mouse clicked and vertex selected
                # Update rubber bands
                for key, value in self.rubber_bands_d.iteritems():
                    self.rubber_bands_d[key].movePoint(1, self.mouse_pt)

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return
        if event.button() == 1:
            self.mouse_clicked = False

            # Remove rubber bands
            for key in self.rubber_bands_d.keys():
                self.iface.mapCanvas().scene().removeItem(self.rubber_bands_d[key])
                del self.rubber_bands_d[key]

            if self.selected_node_ft.id() is not None:

                # Update node geometry
                NodeHandler.move_junction(self.selected_node_ft, self.mouse_pt)
                self.refresh_layer(Parameters.junctions_vlay)

                # Update links geometries
                for feat, vertex_index in self.adj_pipes_fts_d.iteritems():
                    LinkHandler.move_pipe_vertex(feat, self.mouse_pt, vertex_index)

                self.refresh_layer(Parameters.pipes_vlay)
                self.adj_pipes_fts_d.clear()

    def activate(self):

        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        # Snapping
        QgsProject.instance().setSnapSettingsForLayer(Parameters.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(Parameters.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(Parameters.tanks_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        snap_layer_reservoirs = NetworkUtils.set_up_snap_layer(Parameters.reservoirs_vlay)
        snap_layer_tanks = NetworkUtils.set_up_snap_layer(Parameters.tanks_vlay)

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_reservoirs, snap_layer_tanks], self.iface.mapCanvas())

        # Editing
        if not Parameters.junctions_vlay.isEditable():
            Parameters.junctions_vlay.startEditing()
        if not Parameters.reservoirs_vlay.isEditable():
            Parameters.reservoirs_vlay.startEditing()
        if not Parameters.tanks_vlay.isEditable():
            Parameters.tanks_vlay.startEditing()
        if not Parameters.pipes_vlay.isEditable():
            Parameters.pipes_vlay.startEditing()
        if not Parameters.pumps_vlay.isEditable():
            Parameters.pumps_vlay.startEditing()
        if not Parameters.valves_vlay.isEditable():
            Parameters.valves_vlay.startEditing()

    def deactivate(self):
        self.rubber_bands_d.clear()
        self.data_dock.btn_move_node.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def refresh_layer(self, layer):
        if self.iface.mapCanvas().isCachingEnabled():
            layer.setCacheImage(None)
        else:
            self.iface.mapCanvas().refresh()