# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsFeature, QgsFeatureRequest, QgsProject, QgsTolerance, QgsGeometry,\
    QgsPointLocator, NULL
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMessageBar

from ..model.network_handling import LinkHandler, NodeHandler, NetworkUtils
from ..model.network import Junction
from parameters import Parameters
from ..geo_utils import raster_utils


class AddJunctionTool(QgsMapTool):

    def __init__(self, data_dock, params):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""
        self.params = params

        self.mouse_pt = None
        self.mouse_clicked = False
        self.snapper = None
        self.snapped_feat_id = None
        self.snapped_vertex = None
        self.snapped_vertex_nr = None
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.elev = None

    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_clicked = False

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, self.mouse_pt, 1)
        self.elev = elev
        if elev is not None:
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))
        else:
            self.data_dock.lbl_elev_val.setText('-')

        if not self.mouse_clicked:

            # Mouse not clicked: snapping to closest vertex
            # (retval, result) = self.snapper.snapMapPoint(self.toMapCoordinates(event.pos()))

            match = self.snapper.snapToMap(self.mouse_pt)

            if match.isValid():

                # if len(result) > 0:

                self.snapped_feat_id = match.featureId()
                self.snapped_vertex = match.point()
                self.snapped_vertex_nr = match.vertexIndex()

                # It's a vertex on an existing pipe
                # self.snapped_feat_id = result[0].snappedAtGeometry
                #
                # snapped_vertex = result[0].snappedVertex
                # self.snapped_vertex_nr = result[0].snappedVertexNr

                # self.snapped_vertex = QgsPoint(snapped_vertex.x(), snapped_vertex.y())
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
            node_eid = NetworkUtils.find_next_id(self.params.junctions_vlay, Junction.prefix) # TODO: softcode

            elev = 0
            if self.elev is None and self.params.dem_rlay is not None:
                self.iface.messageBar().pushMessage(
                    Parameters.plug_in_name,
                    'Elevation value not available: element elevation set to 0.',
                    QgsMessageBar.WARNING,
                    5)  # TODO: softcode
            else:
                elev = self.elev

            j_demand = float(self.data_dock.txt_junction_demand.text())
            deltaz = float(self.data_dock.txt_junction_deltaz.text())

            pattern = self.data_dock.cbo_junction_pattern.itemData(
                    self.data_dock.cbo_junction_pattern.currentIndex())
            if pattern is not None:
                pattern_id = pattern.id
            else:
                pattern_id = None

            emitter_coeff_s = self.data_dock.txt_junction_emit_coeff.text()
            if emitter_coeff_s is None or emitter_coeff_s == '':
                emitter_coeff = float(0)
            else:
                emitter_coeff = float(self.data_dock.txt_junction_emit_coeff.text())

            junction_desc = self.data_dock.txt_junction_desc.text()
            junction_tag = self.data_dock.cbo_junction_tag.currentText()

            # No links snapped: create a new stand-alone node
            if self.snapped_feat_id is None:

                NodeHandler.create_new_junction(
                    self.params,
                    self.mouse_pt,
                    node_eid,
                    elev,
                    j_demand,
                    deltaz,
                    pattern_id,
                    emitter_coeff,
                    junction_desc,
                    junction_tag)

            # A link has been snapped
            else:

                # Get the snapped pipe
                request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
                feats = list(self.params.pipes_vlay.getFeatures(request))
                if len(feats) > 0:
                    snapped_pipe = QgsFeature(feats[0])

                    snapped_ft_pts = QgsGeometry.asPolyline(snapped_pipe.geometry())

                    # The new junction is on the start or end node of the pipe
                    if NetworkUtils.points_overlap(QgsGeometry.fromPoint(self.snapped_vertex), QgsGeometry.fromPoint(snapped_ft_pts[0]), self.params.tolerance) or\
                        NetworkUtils.points_overlap(QgsGeometry.fromPoint(self.snapped_vertex), QgsGeometry.fromPoint(snapped_ft_pts[len(snapped_ft_pts) - 1]), self.params.tolerance):

                        NodeHandler.create_new_junction(
                            self.params,
                            self.snapped_vertex,
                            node_eid,
                            self.elev,
                            j_demand,
                            deltaz,
                            pattern_id,
                            emitter_coeff,
                            junction_desc,
                            junction_tag)

                    else:

                        # Split the pipe
                        (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.params, snapped_pipe.geometry())

                        if start_node_ft is None or end_node_ft is None:
                            self.iface.messageBar().pushMessage(
                                Parameters.plug_in_name,
                                'The pipe is missing the start or end nodes. Cannot add a new junction along the pipe.',
                                QgsMessageBar.WARNING,
                                5) # TODO: softcode
                            return

                        # Check that the snapped point on line is distant enough from start/end nodes
                        if start_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.params.min_dist and\
                            end_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.params.min_dist:

                            NodeHandler.create_new_junction(
                                self.params,
                                self.snapped_vertex,
                                node_eid,
                                self.elev,
                                j_demand,
                                deltaz,
                                pattern_id,
                                emitter_coeff,
                                junction_desc,
                                junction_tag)

                            LinkHandler.split_pipe(
                                self.params,
                                snapped_pipe,
                                self.snapped_vertex)
                        else:
                            self.iface.messageBar().pushMessage(
                                Parameters.plug_in_name,
                                'The new junction is too close to either the pipe end or start nodes. Cannot add a new junction along the pipe.',
                                QgsMessageBar.WARNING,
                                5)  # TODO: softcode

    def activate(self):

        # Snapping
        # QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
        #                                               True,
        #                                               QgsSnapper.SnapToSegment,
        #                                               QgsTolerance.MapUnits,
        #                                               self.params.snap_tolerance,
        #                                               True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(self.params.junctions_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToSegment)

        layers = {self.params.junctions_vlay: QgsPointLocator.Vertex, self.params.pipes_vlay: QgsPointLocator.All}
        self.snapper = NetworkUtils.set_up_snapper(layers, self.iface.mapCanvas(), self.params.snap_tolerance)

        # Editing
        if not self.params.junctions_vlay.isEditable():
            self.params.junctions_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()

    def deactivate(self):

        if self.params.pipes_vlay is not None:
            QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                          True,
                                                          QgsSnapper.SnapToSegment,
                                                          0,
                                                          self.params.snap_tolerance,
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