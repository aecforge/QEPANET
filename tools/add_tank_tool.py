# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsFeature, QgsFeatureRequest, QgsProject, QgsTolerance, QgsGeometry,\
    QgsPointLocator
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsMessageBar

from ..model.network_handling import LinkHandler, NodeHandler, NetworkUtils
from ..model.network import Tank
from parameters import Parameters
from ..geo_utils import raster_utils


class AddTankTool(QgsMapTool):

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
            # if len(result) > 0:
                # It's a vertex on an existing pipe

            match = self.snapper.snapToMap(self.mouse_pt)

            if match.isValid():

                # self.snapped_feat_id = result[0].snappedAtGeometry
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

            # Find first available ID for Tanks
            tank_eid = NetworkUtils.find_next_id(self.params.tanks_vlay, Tank.prefix) # TODO: softcode

            curve = self.data_dock.cbo_tank_curve.itemData(self.data_dock.cbo_tank_curve.currentIndex())
            if curve is not None:
                tank_curve_id = curve.id
            else:
                tank_curve_id = None

            elev = 0
            if self.elev is None and self.params.dem_rlay is not None:
                self.iface.messageBar().pushMessage(
                    Parameters.plug_in_name,
                    'Elevation value not available: element elevation set to 0.',
                    QgsMessageBar.WARNING,
                    5)  # TODO: softcode
            else:
                elev = self.elev

            diameter = float(self.data_dock.txt_tank_diameter.text())
            deltaz = float(self.data_dock.txt_tank_deltaz.text())
            level_init = float(self.data_dock.txt_tank_level_init.text())
            level_min = float(self.data_dock.txt_tank_level_min.text())
            level_max = float(self.data_dock.txt_tank_level_max.text())
            vol_min = float(self.data_dock.txt_tank_vol_min.text())
            tank_desc = self.data_dock.txt_tank_desc.text()
            tank_tag = self.data_dock.cbo_tank_tag.currentText()

            # No links snapped: create a new stand-alone tank
            if self.snapped_feat_id is None:

                NodeHandler.create_new_tank(
                    self.params,
                    self.mouse_pt,
                    tank_eid,
                    tank_curve_id,
                    diameter,
                    elev,
                    deltaz,
                    level_init,
                    level_min,
                    level_max,
                    vol_min,
                    tank_desc,
                    tank_tag)

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
                            'The pipe is missing the start or end nodes. Cannot add a new tank along the pipe.',
                            QgsMessageBar.WARNING,
                            5)  # TODO: softcode
                        return

                    # Check that the snapped point on line is distant enough from start/end nodes
                    if start_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.params.min_dist and\
                        end_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) > self.params.min_dist:

                        LinkHandler.split_pipe(self.params, snapped_pipe, self.snapped_vertex)

                        # New node on existing line
                        NodeHandler.create_new_tank(
                            self.params,
                            self.snapped_vertex,
                            tank_eid,
                            tank_curve_id,
                            diameter,
                            self.elev,
                            deltaz,
                            level_init,
                            level_min,
                            level_max,
                            vol_min,
                            tank_desc,
                            tank_tag)

                    # Replace pipe start node with new tank
                    elif start_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) <= 0:

                        # Delete junction
                        NodeHandler.delete_node(self.params, self.params.junctions_vlay, start_node_ft, False)

                        # New node on existing line
                        NodeHandler.create_new_tank(
                            self.params,
                            self.snapped_vertex,
                            tank_eid,
                            tank_curve_id,
                            diameter,
                            self.elev,
                            deltaz,
                            level_init,
                            level_min,
                            level_max,
                            vol_min,
                            tank_desc,
                            tank_tag)

                    # Replace pipe end node with new tank
                    elif end_node_ft.geometry().distance(QgsGeometry.fromPoint(self.snapped_vertex)) <= 0:

                        # Delete junction
                        NodeHandler.delete_node(self.params, self.params.junctions_vlay, end_node_ft, False)

                        # New node on existing line
                        NodeHandler.create_new_tank(
                            self.params,
                            self.snapped_vertex,
                            tank_eid,
                            tank_curve_id,
                            diameter,
                            self.elev,
                            deltaz,
                            level_init,
                            level_min,
                            level_max,
                            vol_min,
                            tank_desc,
                            tank_tag)

                    else:
                        self.iface.messageBar().pushMessage(
                            Parameters.plug_in_name,
                            'The selected position is too close to a junction: cannon create the tank.',
                            QgsMessageBar.WARNING,
                            5)  # TODO: softcode

    def activate(self):

        # snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToSegment)

        self.update_snapper()

        # Editing
        if not self.params.tanks_vlay.isEditable():
            self.params.tanks_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

        self.data_dock.btn_add_tank.setChecked(False)

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
        self.snapper = NetworkUtils.set_up_snapper(layers, self.iface.mapCanvas(), self.params.snap_tolerance)

    # Needed by Observable
    def update(self, observable):
        self.update_snapper()