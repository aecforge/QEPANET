# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsGeometry, QgsFeatureRequest, QgsProject, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker

from network import Valve
from network_handling import LinkHandler, NetworkUtils
from parameters import Parameters
from ..geo_utils import raster_utils


class AddValveTool(QgsMapTool):

    def __init__(self, data_dock):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""

        self.mouse_pt = None
        self.mouse_clicked = False
        self.snapper = None
        self.snapped_pipe_id = None
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

        elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, self.mouse_pt, 1)

        if elev is not None:
            self.elev = elev
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        if not self.mouse_clicked:

            # Mouse not clicked: snapping to closest vertex
            (retval, result) = self.snapper.snapMapPoint(self.toMapCoordinates(event.pos()))
            if len(result) > 0:
                # It's a vertex on an existing pipe

                self.snapped_pipe_id = result[0].snappedAtGeometry

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
                self.snapped_pipe_id = None
                self.vertex_marker.hide()

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return

        if event.button() == Qt.LeftButton:

            self.mouse_clicked = False

            # No pipe snapped: notify user
            if self.snapped_pipe_id is None:

                self.iface.messageBar().pushInfo(Parameters.plug_in_name, 'You need to snap the cursor to a pipe to add a valve.')

            # A pipe has been snapped
            else:

                request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
                feats = Parameters.pipes_vlay.getFeatures(request)
                features = [feat for feat in feats]
                if len(features) == 1:

                    # Check whether the pipe has a start and an end node
                    pipe_endnodes = NetworkUtils.find_start_end_junctions(features[0].geometry())

                    if len(pipe_endnodes) < 2:
                        self.iface.messageBar().pushWarning(Parameters.plug_in_name, 'The pipe is missing the start or end nodes.')      # TODO: softcode
                        return

                    # Find endnode closest to valve position
                    dist_1 = pipe_endnodes[0].geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex))
                    dist_2 = pipe_endnodes[1].geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex))

                    # Get the attributes of the closest node
                    if dist_1 < dist_2:
                        closest_junction_ft = pipe_endnodes[0]
                    else:
                        closest_junction_ft = pipe_endnodes[1]

                    # Create the valve
                    diameter = self.txt_valve_diameter.text()
                    minor_loss = self.txt_valve_minor_loss.text()
                    selected_type = self.cbo_valve_type.itemData(self.cbo_valve_type.currentIndex())
                    if selected_type != Valve.type_gpv:
                        setting = self.txt_valve_setting.text()
                    else:
                        setting = self.cbo_valve_curve.itemData(self.cbo_valve_curve.currentIndex())

                    LinkHandler.create_new_valve(
                        features[0],
                        closest_junction_ft,
                        self.snapped_vertex,
                        diameter,
                        minor_loss,
                        setting,
                        type)

    def activate(self):

        QgsProject.instance().setSnapSettingsForLayer(Parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)

        snap_layer_pipes = NetworkUtils.set_up_snap_layer(Parameters.pipes_vlay, None, QgsSnapper.SnapToVertexAndSegment)
        self.snapper = NetworkUtils.set_up_snapper([snap_layer_pipes], self.iface.mapCanvas())

        # Editing
        if not Parameters.valves_vlay.isEditable():
            Parameters.valves_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(Parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

        self.data_dock.btn_add_valve.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def reset_marker(self):
        self.outlet_marker.hide()
        self.canvas().scene().removeItem(self.outlet_marker)