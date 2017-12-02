# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsFeature, QgsFeatureRequest, QgsProject, QgsTolerance, QgsGeometry, QgsPointLocator
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMessageBar

from ..model.network_handling import LinkHandler, NodeHandler, NetworkUtils
from ..model.network import Reservoir
from parameters import Parameters
from ..geo_utils import raster_utils


class AddReservoirTool(QgsMapTool):

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
        self.elev = -1

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
            # if len(result) > 0:

            match = self.snapper.snapToMap(self.mouse_pt)

            if match.isValid():

                # It's a vertex on an existing pipe
                # self.snapped_feat_id = result[0].snappedAtGeometry
                #
                # snapped_vertex = result[0].snappedVertex
                # self.snapped_vertex_nr = result[0].snappedVertexNr
                # self.snapped_vertex = QgsPoint(snapped_vertex.x(), snapped_vertex.y())

                self.snapped_feat_id = match.featureId()
                self.snapped_vertex = match.point()
                self.snapped_vertex_nr = match.vertexIndex()

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

            # Find first available ID for reservoirs
            eid = NetworkUtils.find_next_id(self.params.reservoirs_vlay, Reservoir.prefix) # TODO: softcode

            elev = 0
            if self.elev is None and self.params.dem_rlay is not None:
                self.iface.messageBar().pushMessage(
                    Parameters.plug_in_name,
                    'Elevation value not available: element eleveation set to 0.',
                    QgsMessageBar.WARNING,
                    5)  # TODO: softcode
            else:
                elev = self.elev

            deltaz = float(self.data_dock.txt_reservoir_deltaz.text())
            pressure_head = float(self.data_dock.txt_reservoir_pressure_head.text())

            pattern = self.data_dock.cbo_reservoir_pattern.itemData(self.data_dock.cbo_reservoir_pattern.currentIndex())
            if pattern is not None:
                pattern_id = pattern.id
            else:
                pattern_id = None

            reservoir_desc = self.data_dock.txt_reservoir_desc.text()

            # No links snapped: create a new stand-alone node
            if self.snapped_feat_id is None:

                NodeHandler.create_new_reservoir(
                    self.params,
                    self.mouse_pt,
                    eid,
                    elev,
                    deltaz,
                    pressure_head,
                    pattern_id,
                    reservoir_desc)

            # A link has been snapped
            else:

                # Get the snapped pipe and split it
                request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
                feats = list(self.params.pipes_vlay.getFeatures(request))
                if len(feats) > 0:

                    snapped_pipe = QgsFeature(feats[0])
                    (start_node_ft, end_node_ft) = NetworkUtils.find_start_end_nodes(self.params, snapped_pipe.geometry())

                    if start_node_ft is None or end_node_ft is None:
                        self.iface.messageBar().pushMessage(
                            Parameters.plug_in_name,
                            'The pipe is missing the start or end nodes. Cannot add a new reservoir along the pipe.',
                            QgsMessageBar.WARNING,
                            5)  # TODO: softcode
                        return

                    # Check that the snapped point on pipe is distant enough from start/end nodes
                    if start_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.params.min_dist and\
                        end_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.params.min_dist:

                        LinkHandler.split_pipe(self.params, snapped_pipe, self.snapped_vertex)

                        # New node on existing line
                        NodeHandler.create_new_reservoir(
                            self.params,
                            self.snapped_vertex,
                            eid,
                            self.elev,
                            deltaz,
                            pressure_head,
                            pattern_id,
                            reservoir_desc)

                    elif start_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) <= 0:

                        # Delete junction
                        NodeHandler.delete_node(self.params, self.params.junctions_vlay, start_node_ft, False)

                        # New node on existing line
                        NodeHandler.create_new_reservoir(
                            self.params,
                            self.snapped_vertex,
                            eid,
                            self.elev,
                            deltaz,
                            pressure_head,
                            pattern_id,
                            reservoir_desc)

                    elif end_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) <= 0:

                        # Delete junction
                        NodeHandler.delete_node(self.params, self.params.junctions_vlay, end_node_ft, False)

                        # New node on existing line
                        NodeHandler.create_new_reservoir(
                            self.params,
                            self.snapped_vertex,
                            eid,
                            self.elev,
                            deltaz,
                            pressure_head,
                            pattern_id,
                            reservoir_desc)

                    else:
                        self.iface.messageBar().pushMessage(
                            Parameters.plug_in_name,
                            'The selected position is too close to a junction: cannot create the reservoir.',
                            QgsMessageBar.WARNING,
                            5)  # TODO: softcode

    def activate(self):

        # QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
        #                                               True,
        #                                               QgsSnapper.SnapToSegment,
        #                                               QgsTolerance.MapUnits,
        #                                               self.params.snap_tolerance,
        #                                               True)

        # # snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        # snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToSegment)

        layers = {self.params.pipes_vlay: QgsPointLocator.All}
        self.snapper = NetworkUtils.set_up_snapper(layers, self.iface.mapCanvas(), self.params.snap_tolerance)

        # Editing
        if not self.params.reservoirs_vlay.isEditable():
            self.params.reservoirs_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

        self.data_dock.btn_add_reservoir.setChecked(False)

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