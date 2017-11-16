# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QPoint
from PyQt4.QtGui import QColor, QMenu
from qgis.core import QgsPoint, QgsSnapper, QgsGeometry, QgsFeatureRequest, QgsProject, QgsTolerance, QGis, QgsPointLocator
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMessageBar

from ..model.network import Valve, Pipe
from ..model.network_handling import LinkHandler, NetworkUtils, PumpValveCreationException
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
                # self.snapped_pipe_id = result[0].snappedAtGeometry
                # snapped_vertex = result[0].snappedVertex
                # self.snapped_vertex_nr = result[0].snappedVertexNr
                # self.snapped_vertex = QgsPoint(snapped_vertex.x(), snapped_vertex.y())

                self.snapped_pipe_id = match.featureId()
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
                self.snapped_pipe_id = None
                self.vertex_marker.hide()

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return

        if event.button() == Qt.LeftButton:

            self.mouse_clicked = False

            # No pipe snapped: notify user
            if self.snapped_pipe_id is None:

                self.iface.messageBar().pushMessage(Parameters.plug_in_name, 'You need to snap the cursor to a pipe to add a valve.', QgsMessageBar.INFO, 5)

            # A pipe has been snapped
            else:

                request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
                feats = self.params.pipes_vlay.getFeatures(request)
                features = [feat for feat in feats]
                if len(features) == 1:

                    # Check whether the pipe has a start and an end node
                    (start_node, end_node) = NetworkUtils.find_start_end_nodes(self.params, features[0].geometry())

                    if not start_node or not end_node:
                        self.iface.messageBar().pushMessage(Parameters.plug_in_name, 'The pipe is missing the start or end nodes.', QgsMessageBar.WARNING, 5)      # TODO: softcode
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
                        valve_curve = self.data_dock.cbo_valve_curve.itemData(self.data_dock.cbo_valve_curve.currentIndex())
                        if valve_curve is not None:
                            setting = valve_curve.id
                        else:
                            setting = None

                    # Pump status
                    valve_status = self.data_dock.cbo_valve_status.itemData(
                        self.data_dock.cbo_valve_status.currentIndex())

                    try:
                        LinkHandler.create_new_pumpvalve(
                            self.params,
                            self.data_dock,
                            features[0],
                            closest_junction_ft,
                            self.snapped_vertex,
                            self.params.valves_vlay,
                            [diameter, minor_loss, setting, selected_type, valve_status])

                    except PumpValveCreationException as ex:
                        self.iface.messageBar().pushMessage(
                            Parameters.plug_in_name,
                            ex.message,
                            QgsMessageBar.INFO,
                            5)

        elif event.button() == Qt.RightButton:

            self.mouse_clicked = False

            # Check whether it clicked on a valve vertex
            if len(NetworkUtils.find_adjacent_links(self.params, self.snapped_vertex)['valves']) == 0:
                return

            menu = QMenu()
            diameter_action = menu.addAction('Change diameter...')  # TODO: softcode
            invert_action = menu.addAction('Flip orientation')  # TODO: softcode
            action = menu.exec_(self.iface.mapCanvas().mapToGlobal(QPoint(event.pos().x(), event.pos().y())))

            request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
            feats = self.params.pipes_vlay.getFeatures(request)
            features = [feat for feat in feats]
            if len(features) == 1:
                adj_links = NetworkUtils.find_links_adjacent_to_link(
                    self.params, self.params.pipes_vlay, features[0], True, True, False)

                for valve_ft in adj_links['valves']:

                    if action == diameter_action:
                        old_diam = valve_ft.attribute(Valve.field_name_diameter)
                        self.diameter_dialog = DiameterDialog(self.iface.mainWindow(), self.params, old_diam)
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

                            self.iface.messageBar().pushMessage(
                                Parameters.plug_in_name,
                                'Diameters of pipes adjacent to valve updated.',
                                QgsMessageBar.INFO,
                                5)  # TODO: softcode

                    elif action == invert_action:

                        request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
                        feats = self.params.pipes_vlay.getFeatures(request)
                        features = [feat for feat in feats]
                        if len(features) == 1:
                            adj_links = NetworkUtils.find_links_adjacent_to_link(
                                self.params, self.params.pipes_vlay, features[0], True, True, False)

                            for adj_link in adj_links['valves']:
                                adj_link_pts = adj_link.geometry().asPolyline()
                                for adj_link_pt in adj_link_pts:
                                    if NetworkUtils.points_overlap(adj_link_pt, self.snapped_vertex,
                                                                   self.params.tolerance):

                                        geom = adj_link.geometry()

                                        if geom.wkbType() == QGis.WKBMultiLineString:
                                            nodes = geom.asMultiPolyline()
                                            for line in nodes:
                                                line.reverse()
                                            newgeom = QgsGeometry.fromMultiPolyline(nodes)
                                            self.params.valves_vlay.changeGeometry(adj_link.id(), newgeom)

                                        if geom.wkbType() == QGis.WKBLineString:
                                            nodes = geom.asPolyline()
                                            nodes.reverse()
                                            newgeom = QgsGeometry.fromPolyline(nodes)
                                            self.params.valves_vlay.changeGeometry(adj_link.id(), newgeom)

                                        self.iface.mapCanvas().refresh()

                                        break

    def activate(self):

        # QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
        #                                               True,
        #                                               QgsSnapper.SnapToSegment,
        #                                               QgsTolerance.MapUnits,
        #                                               self.params.snap_tolerance,
        #                                               True)

        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToVertexAndSegment)

        layers = {self.params.pipes_vlay: QgsPointLocator.All}
        self.snapper = NetworkUtils.set_up_snapper(layers, self.iface.mapCanvas(), self.params.snap_tolerance)

        # Editing
        if not self.params.junctions_vlay.isEditable():
            self.params.junctions_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()
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