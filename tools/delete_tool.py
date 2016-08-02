# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import QCursor, QColor
from qgis.core import QgsPoint, QgsFeatureRequest, QgsFeature, QgsGeometry, QgsProject, QgsTolerance, QgsSnapper, QgsVector
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand

from ..model.network_handling import NetworkUtils, NodeHandler, LinkHandler
from parameters import Parameters
from ..geo_utils import raster_utils, vector_utils
from ..rendering import symbology


class DeleteTool(QgsMapTool):

    def __init__(self, data_dock, parameters):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""
        self.parameters = parameters

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

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        elev = raster_utils.read_layer_val_from_coord(self.parameters.dem_rlay, self.mouse_pt, 1)
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

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return

        if event.button() == 1:
            self.mouse_clicked = False

            if self.snap_results is not None:

                snapped_ft = vector_utils.get_feats_by_id(self.snap_results[0].layer, self.snap_results[0].snappedAtGeometry)[0]
                snapped_layer = self.snap_results[0].layer

                # If reservoir or tank: delete and stitch pipes
                if snapped_layer == self.parameters.junctions_vlay or \
                            snapped_layer == self.parameters.reservoirs_vlay or \
                        snapped_layer == self.parameters.tanks_vlay:

                    # The node is a junction
                    if snapped_layer == self.parameters.junctions_vlay:

                        adj_links_fts = NetworkUtils.find_adjacent_links(self.parameters, snapped_ft.geometry())

                        # Only pipes adjacent to node: it's a simple junction
                        if not adj_links_fts['pumps'] and not adj_links_fts['valves']:

                            # Delete node
                            NodeHandler.delete_node(self.parameters, snapped_layer, snapped_ft)

                            # Delete adjacent pipes
                            adj_pipes = NetworkUtils.find_adjacent_links(self.parameters, snapped_ft.geometry())
                            for adj_pipe in adj_pipes['pipes']:
                                LinkHandler.delete_link(self.parameters.pipes_vlay, adj_pipe)

                        # The node is part of a pump or valve
                        else:

                            if adj_links_fts['pumps']:
                                LinkHandler.delete_link(self.parameters, self.parameters.pumps_vlay, snapped_ft)

                            elif adj_links_fts['valves']:
                                LinkHandler.delete_link(self.parameters, self.parameters.valves_vlay, snapped_ft)


                    # The node is a reservoir or a tank
                    elif snapped_layer == self.parameters.reservoirs_vlay or \
                                    snapped_layer == self.parameters.tanks_vlay:

                        adj_pipes = NetworkUtils.find_adjacent_links(self.parameters, snapped_ft.geometry())['pipes']

                        NodeHandler._delete_feature(snapped_layer, snapped_ft)

                        for adj_pipe in adj_pipes:
                            LinkHandler.delete_link(self.parameters, self.parameters.pipes_vlay, adj_pipe)

                # If pipe: delete
                elif snapped_layer == self.parameters.pipes_vlay:

                    LinkHandler.delete_link(self.parameters, snapped_layer, snapped_ft)

                symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.junctions_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.reservoirs_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.tanks_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.pipes_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.pumps_vlay)
                symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.valves_vlay)

    def activate(self):

        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        # Snapping
        QgsProject.instance().setSnapSettingsForLayer(self.parameters.junctions_vlay.id(),
                                                      False,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.reservoirs_vlay.id(),
                                                      False,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.tanks_vlay.id(),
                                                      False,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(self.parameters.junctions_vlay)
        snap_layer_reservoirs = NetworkUtils.set_up_snap_layer(self.parameters.reservoirs_vlay)
        snap_layer_tanks = NetworkUtils.set_up_snap_layer(self.parameters.tanks_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.parameters.pipes_vlay, snapping_type=QgsSnapper.SnapToSegment)

        self.snapper = NetworkUtils.set_up_snapper(
            [snap_layer_junctions, snap_layer_reservoirs, snap_layer_tanks, snap_layer_pipes],
            self.iface.mapCanvas())

        # Editing
        if not self.parameters.junctions_vlay.isEditable():
            self.parameters.junctions_vlay.startEditing()
        if not self.parameters.reservoirs_vlay.isEditable():
            self.parameters.reservoirs_vlay.startEditing()
        if not self.parameters.tanks_vlay.isEditable():
            self.parameters.tanks_vlay.startEditing()
        if not self.parameters.pipes_vlay.isEditable():
            self.parameters.pipes_vlay.startEditing()
        if not self.parameters.pumps_vlay.isEditable():
            self.parameters.pumps_vlay.startEditing()
        if not self.parameters.valves_vlay.isEditable():
            self.parameters.valves_vlay.startEditing()

    def deactivate(self):
        self.data_dock.btn_move_element.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True