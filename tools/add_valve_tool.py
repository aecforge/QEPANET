# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QPoint
from PyQt4.QtGui import QColor, QMenu
from qgis.core import QgsPoint, QgsSnapper, QgsGeometry, QgsFeatureRequest, QgsProject, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker

from ..model.network import Valve, Pipe
from ..model.network_handling import LinkHandler, NetworkUtils
from parameters import Parameters
from ..geo_utils import raster_utils, vector_utils
from ..ui.diameter_dialog import DiameterDialog


class AddValveTool(QgsMapTool):

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
        self.snapped_pipe_id = None
        self.snapped_vertex = None
        self.snapped_vertex_nr = None
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.elev = -1

        self.diameter_dialog = None

    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_clicked = True

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, self.mouse_pt, 1)

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
                feats = self.params.pipes_vlay.getFeatures(request)
                features = [feat for feat in feats]
                if len(features) == 1:

                    # Check whether the pipe has a start and an end node
                    (start_node, end_node) = NetworkUtils.find_start_end_nodes(self.params, features[0].geometry())

                    if not start_node or not end_node:
                        self.iface.messageBar().pushWarning(Parameters.plug_in_name, 'The pipe is missing the start or end nodes.')      # TODO: softcode
                        return

                    # Find endnode closest to valve position
                    dist_1 = start_node.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex))
                    dist_2 = end_node.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex))

                    # Get the attributes of the closest junction
                    (start_node, end_node) = NetworkUtils.find_start_end_nodes(self.params, features[0].geometry(), False, True, True)
                    if dist_1 < dist_2:
                        closest_junction_ft = start_node
                    else:
                        closest_junction_ft = end_node

                    # Create the valve
                    diameter = features[0].attribute(Pipe.field_name_diameter)
                    # diameter = self.data_dock.txt_valve_diameter.text()
                    minor_loss = self.data_dock.txt_valve_minor_loss.text()
                    selected_type = self.data_dock.cbo_valve_type.itemData(self.data_dock.cbo_valve_type.currentIndex())
                    if selected_type != Valve.type_gpv:
                        setting = self.data_dock.txt_valve_setting.text()
                    else:
                        setting = self.data_dock.cbo_valve_curve.itemData(self.cbo_valve_curve.currentIndex())

                    LinkHandler.create_new_pumpvalve(
                        self.params,
                        self.data_dock,
                        features[0],
                        closest_junction_ft,
                        self.snapped_vertex,
                        self.params.valves_vlay,
                        [diameter, minor_loss, setting, selected_type])

        elif event.button() == Qt.RightButton:

            self.mouse_clicked = False

            menu = QMenu()
            diameter_action = menu.addAction('Change diameter...')  # TODO: softcode
            action = menu.exec_(self.iface.mapCanvas().mapToGlobal(QPoint(event.pos().x(), event.pos().y())))

            request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
            feats = self.params.pipes_vlay.getFeatures(request)
            features = [feat for feat in feats]
            if len(features) == 1:
                adj_links = NetworkUtils.find_links_adjacent_to_link(
                    self.params, self.params.pipes_vlay, features[0], True, True, False)

                for valve_ft in adj_links['valves']:

                    # valve_ft = vector_utils.get_feats_by_id(self.params.valves_vlay, self.snapped_pipe_id)[0]

                    if action == diameter_action:
                        self.diameter_dialog = DiameterDialog(self.iface.mainWindow(), self.params)
                        self.diameter_dialog.exec_()  # Exec creates modal dialog
                        new_diameter = self.diameter_dialog.get_diameter()
                        if new_diameter is None:
                            return

                        # Update valve diameter
                        vector_utils.update_attribute(self.params.valves_vlay, valve_ft, Valve.field_name_diameter, new_diameter)

                        # Modify pipes diameters
                        adj_pipes_fts = NetworkUtils.find_links_adjacent_to_link(
                            self.params, self.params.valves_vlay, valve_ft, False, True, True)

                        if adj_pipes_fts:

                            for adj_pipe_ft in adj_pipes_fts['pipes']:

                                vector_utils.update_attribute(self.params.pipes_vlay,
                                                              adj_pipe_ft,
                                                              Pipe.field_name_diameter,
                                                              new_diameter)

                            self.iface.messageBar().pushInfo(
                                Parameters.plug_in_name,
                                'Diameters of pipes adjacent to valve updated.')  # TODO: softcode

    def activate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToVertexAndSegment)
        self.snapper = NetworkUtils.set_up_snapper([snap_layer_pipes], self.iface.mapCanvas())

        # Editing
        if not self.params.valves_vlay.isEditable():
            self.params.valves_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
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