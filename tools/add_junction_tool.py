# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsFeature, QgsFeatureRequest, QgsProject, QgsTolerance, QgsGeometry
from qgis.gui import QgsMapTool, QgsVertexMarker

from ..model.network_handling import LinkHandler, NodeHandler, NetworkUtils
from parameters import Parameters
from ..geo_utils import raster_utils


class AddJunctionTool(QgsMapTool):

    def __init__(self, data_dock, parameters):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""
        self.parameters = parameters

        self.mouse_pt = None
        self.mouse_clicked = False
        self.snapper = None
        self.snapped_feat_id = None
        self.snapped_vertex = None
        self.snapped_vertex_nr = None
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.elev = -1

    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_clicked = False

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        elev = raster_utils.read_layer_val_from_coord(self.parameters.dem_rlay, self.mouse_pt, 1)

        if elev is not None:
            self.elev = elev
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        if not self.mouse_clicked:

            # Mouse not clicked: snapping to closest vertex
            (retval, result) = self.snapper.snapMapPoint(self.toMapCoordinates(event.pos()))

            if len(result) > 0:

                # It's a vertex on an existing pipe
                self.snapped_feat_id = result[0].snappedAtGeometry

                snapped_vertex = result[0].snappedVertex
                self.snapped_vertex_nr = result[0].snappedVertexNr

                self.snapped_vertex = QgsPoint(snapped_vertex.x(), snapped_vertex.y())
                self.vertex_marker.setCenter(self.snapped_vertex)
                self.vertex_marker.setColor(QColor(255, 0, 0))
                self.vertex_marker.setIconSize(10)
                self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
                self.vertex_marker.setPenWidth(3)
                self.vertex_marker.show()

            else:

                # It's a new, isolated vertex
                self.snapped_feat_id = None
                self.vertex_marker.hide()

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return

        if event.button() == Qt.LeftButton:

            self.mouse_clicked = False

            # Find first available ID for Junctions
            node_eid = NetworkUtils.find_next_id(self.parameters.junctions_vlay, 'J') # TODO: softcode

            j_demand = float(self.data_dock.txt_junction_demand.text())
            depth = float(self.data_dock.txt_junction_depth.text())

            if self.data_dock.cbo_junction_pattern.currentIndex() != -1:
                pattern_id = self.data_dock.cbo_junction_pattern.itemData(self.data_dock.cbo_junction_pattern.currentIndex()).id
            else:
                pattern_id = None

            # No links snapped: create a new stand-alone node
            if self.snapped_feat_id is None:

                NodeHandler.create_new_junction(
                    self.parameters,
                    self.mouse_pt,
                    node_eid,
                    self.elev,
                    j_demand,
                    depth,
                    pattern_id)

            # A link has been snapped
            else:

                # Get the snapped pipe
                request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
                feats = list(self.parameters.pipes_vlay.getFeatures(request))
                if len(feats) > 0:
                    snapped_pipe = QgsFeature(feats[0])

                    snapped_ft_pts = QgsGeometry.asPolyline(snapped_pipe.geometry())

                    # The new junction is on the start or end node of the pipe
                    if NetworkUtils.points_overlap(QgsGeometry.fromPoint(self.snapped_vertex), QgsGeometry.fromPoint(snapped_ft_pts[0]), self.parameters.tolerance) or\
                        NetworkUtils.points_overlap(QgsGeometry.fromPoint(self.snapped_vertex), QgsGeometry.fromPoint(snapped_ft_pts[len(snapped_ft_pts) - 1]), self.parameters.tolerance):

                        NodeHandler.create_new_junction(
                            self.parameters,
                            self.snapped_vertex,
                            node_eid,
                            self.elev,
                            j_demand,
                            depth,
                            pattern_id)

                    else:

                        # Split the pipe
                        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.parameters, snapped_pipe.geometry())

                        if start_node_ft is None or end_node_ft is None:
                            self.iface.messageBar().pushWarning(
                                Parameters.plug_in_name,
                                'The pipe is missing the start or end nodes. Cannot add a new junction along the pipe.') # TODO: softcode
                            return

                        # Check that the snapped point on line is distant enough from start/end nodes
                        if start_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.parameters.min_dist and\
                            end_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.parameters.min_dist:

                            NodeHandler.create_new_junction(
                                self.parameters,
                                self.snapped_vertex,
                                node_eid,
                                self.elev,
                                j_demand,
                                depth,
                                pattern_id)

                            LinkHandler.split_pipe(
                                self.parameters,
                                snapped_pipe,
                                self.snapped_vertex)
                        else:
                            self.iface.messageBar().pushWarning(
                                Parameters.plug_in_name,
                                'The new junction is too close to either the pipe end or start nodes. Cannot add a new junction along the pipe.')  # TODO: softcode

    def activate(self):

        # Snapping
        QgsProject.instance().setSnapSettingsForLayer(self.parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(self.parameters.junctions_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.parameters.pipes_vlay, None, QgsSnapper.SnapToSegment)

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_pipes], self.iface.mapCanvas())

        # Editing
        if not self.parameters.junctions_vlay.isEditable():
            self.parameters.junctions_vlay.startEditing()
        if not self.parameters.pipes_vlay.isEditable():
            self.parameters.pipes_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      0,
                                                      self.parameters.snap_tolerance,
                                                      True)

        self.data_dock.btn_add_junction.setChecked(False)

        self.canvas().scene().removeItem(self.vertex_marker)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def reset_marker(self):
        self.outlet_marker.hide()
        self.canvas().scene().removeItem(self.outlet_marker)