# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QPoint
from PyQt4.QtGui import QColor, QMenu
from qgis.core import QgsPoint, QgsSnapper, QgsGeometry, QgsFeatureRequest, QgsProject, QgsTolerance, QGis, QgsPointLocator
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMessageBar

from ..model.network import Pump
from ..model.network_handling import LinkHandler, NetworkUtils, PumpValveCreationException
from parameters import Parameters
from ..geo_utils import raster_utils


class AddPumpTool(QgsMapTool):

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

                self.iface.messageBar().pushMessage(Parameters.plug_in_name, 'You need to snap the cursor to a pipe to add a pump.', QgsMessageBar.INFO, 5)

            # A pipe has been snapped
            else:

                request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
                feats = self.params.pipes_vlay.getFeatures(request)
                features = [feat for feat in feats]
                if len(features) == 1:

                    # Check whether the pipe has a start and an end node
                    (start_node, end_node) = NetworkUtils.find_start_end_nodes(self.params, features[0].geometry())

                    if not start_node or not end_node:
                        self.iface.messageBar().pushMessage(Parameters.plug_in_name, 'The pipe is missing the start or end nodes.', QgsMessageBar.WARNING, 5) # TODO: softcode
                        return

                    # Find endnode closest to pump position
                    dist_1 = start_node.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex))
                    dist_2 = end_node.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex))

                    # Get the attributes of the closest junction
                    (start_node, end_node) = NetworkUtils.find_start_end_nodes(self.params, features[0].geometry(), False, True, True)
                    if dist_1 < dist_2:
                        closest_junction_ft = start_node
                    else:
                        closest_junction_ft = end_node

                    # Create the pump
                    pump_param = ''
                    pump_head = None
                    pump_power = None
                    pump_speed = 0
                    pump_speed_pattern = 0

                    # Head and curve
                    if self.data_dock.cbo_pump_param.itemText(self.data_dock.cbo_pump_param.currentIndex()) == Pump.parameters_head:
                        pump_param = Pump.parameters_head
                        curve = self.data_dock.cbo_pump_head.itemData(self.data_dock.cbo_pump_head.currentIndex())
                        if curve is not None:
                            pump_head = curve.id
                        else:
                            pump_head = None

                    # Power and value
                    elif self.data_dock.cbo_pump_param.itemText(self.data_dock.cbo_pump_param.currentIndex()) == Pump.parameters_power:
                        pump_param = Pump.parameters_power
                        pump_power = float(self.data_dock.txt_pump_power.text())

                    # Speed
                    pump_speed_s = self.data_dock.txt_pump_speed.text()
                    if pump_speed_s is None or pump_speed_s == '':
                        pump_speed = 0
                    else:
                        pump_speed = float(pump_speed_s)

                    # Speed pattern
                    pump_speed_pattern = self.data_dock.cbo_pump_speed_pattern.itemText(
                        self.data_dock.cbo_pump_speed_pattern.currentIndex())

                    # Pump status
                    pump_status = self.data_dock.cbo_pump_status.itemData(
                        self.data_dock.cbo_pump_status.currentIndex())

                    # Pump description
                    pump_desc = self.data_dock.txt_pump_desc.text()

                    # Pump tag
                    pump_tag = self.data_dock.cbo_pump_tag.currentText()

                    try:
                        LinkHandler.create_new_pumpvalve(
                            self.params,
                            self.data_dock,
                            features[0],
                            closest_junction_ft,
                            self.snapped_vertex,
                            self.params.pumps_vlay,
                            {Pump.field_name_param: pump_param,
                             Pump.field_name_head: pump_head,
                             Pump.field_name_power: pump_power,
                             Pump.field_name_speed: pump_speed,
                             Pump.field_name_speed_pattern: pump_speed_pattern,
                             Pump.field_name_status: pump_status,
                             Pump.field_name_description: pump_desc,
                             Pump.field_name_tag: pump_tag})

                        if pump_param == Pump.parameters_head and pump_head is None:
                            self.iface.messageBar().pushMessage(Parameters.plug_in_name,
                                                             'The pump was added, but with a NULL value.',
                                                                QgsMessageBar.INFO,
                                                                5)

                    except PumpValveCreationException as ex:
                        self.iface.messageBar().pushMessage(
                            Parameters.plug_in_name,
                            ex.message,
                            QgsMessageBar.INFO,
                            5)

        elif event.button() == Qt.RightButton:

            self.mouse_clicked = False

            # Check whether it clicked on a valve vertex
            if len(NetworkUtils.find_adjacent_links(self.params, self.snapped_vertex)['pumps']) == 0:
                return

            menu = QMenu()
            invert_action = menu.addAction('Flip orientation')  # TODO: softcode
            action = menu.exec_(self.iface.mapCanvas().mapToGlobal(QPoint(event.pos().x(), event.pos().y())))
            if action == invert_action:

                request = QgsFeatureRequest().setFilterFid(self.snapped_pipe_id)
                feats = self.params.pipes_vlay.getFeatures(request)
                features = [feat for feat in feats]
                if len(features) == 1:
                    adj_links = NetworkUtils.find_links_adjacent_to_link(
                        self.params, self.params.pipes_vlay, features[0], True, False, True)

                    for adj_link in adj_links['pumps']:
                        adj_link_pts = adj_link.geometry().asPolyline()
                        for adj_link_pt in adj_link_pts:
                            if NetworkUtils.points_overlap(adj_link_pt, self.snapped_vertex, self.params.tolerance):

                                geom = adj_link.geometry()

                                if geom.wkbType() == QGis.WKBMultiLineString:
                                    nodes = geom.asMultiPolyline()
                                    for line in nodes:
                                        line.reverse()
                                    newgeom = QgsGeometry.fromMultiPolyline(nodes)
                                    self.params.pumps_vlay.changeGeometry(adj_link.id(), newgeom)

                                if geom.wkbType() == QGis.WKBLineString:
                                    nodes = geom.asPolyline()
                                    nodes.reverse()
                                    newgeom = QgsGeometry.fromPolyline(nodes)
                                    self.params.pumps_vlay.changeGeometry(adj_link.id(), newgeom)

                                self.iface.mapCanvas().refresh()

                                break

    def activate(self):

        # snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToVertexAndSegment)

        self.update_snapper()

        # Editing
        if not self.params.junctions_vlay.isEditable():
            self.params.junctions_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()
        if not self.params.pumps_vlay.isEditable():
            self.params.pumps_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

        self.data_dock.btn_add_pump.setChecked(False)

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

    def update_snapper(self):
        layers = {self.params.pipes_vlay: QgsPointLocator.All}
        self.snapper = NetworkUtils.set_up_snapper(
            layers,
            self.iface.mapCanvas(),
            self.params.snap_tolerance)

    # Needed by Observable
    def update(self, observable):
        self.update_snapper()