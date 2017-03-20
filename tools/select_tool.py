# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand

from ..model.network_handling import NetworkUtils, NodeHandler, LinkHandler
from parameters import Parameters
from ..geo_utils import raster_utils, vector_utils
from ..rendering import symbology


class SelectTool(QgsMapTool):

    def __init__(self, data_dock, params):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""
        self.params = params

        self.elev = -1
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.rubber_band = QgsRubberBand(self.data_dock.iface.mapCanvas(), QGis.Polygon)
        self.mouse_clicked = False
        self.snapper = None

        self.clicked_pt = None

        self.snap_results = None
        self.adj_links_fts = None

        self.selected_node_ft = None
        self.selected_node_ft_lay = None
        self.mouse_pt = None

        self.layer_selft = {}

    def canvasPressEvent(self, event):

        # if self.snap_results is None:
        #     return

        if event.button() == Qt.RightButton:
            self.mouse_clicked = False
            self.clicked_pt = None

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True
            self.clicked_pt = self.toMapCoordinates(event.pos())

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

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

        # Mouse clicked: draw rectangle
        else:
            if self.snap_results is None:
                end_point = self.toMapCoordinates(event.pos())
                self.show_rect(self.clicked_pt, end_point)

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = False

            # Snapped: one element selected
            if self.snap_results is not None:

                snapped_ft = vector_utils.get_feats_by_id(self.snap_results[0].layer, self.snap_results[0].snappedAtGeometry)[0]
                snapped_layer = self.snap_results[0].layer

                modifiers = QApplication.keyboardModifiers()
                if modifiers == Qt.ShiftModifier:
                    selected_ft_ids = snapped_layer.selectedFeaturesIds()
                    selected_ft_ids.append(snapped_ft.id())
                    snapped_layer.select(selected_ft_ids)
                else:
                    for layer in self.iface.mapCanvas().layers():
                        if layer.id() == self.params.junctions_vlay.id() or \
                                        layer.id() == self.params.reservoirs_vlay.id() or \
                                        layer.id() == self.params.tanks_vlay.id() or \
                                        layer.id() == self.params.pipes_vlay.id() or \
                                        layer.id() == self.params.pumps_vlay.id() or \
                                        layer.id() == self.params.valves_vlay.id():
                            layer.removeSelection()
                    snapped_layer.select(snapped_ft.id())

            # Not snapped: rectangle
            else:
                # There is a rubber band box
                if self.rubber_band.numberOfVertices() > 1:
                    rubber_band_rect = self.rubber_band.asGeometry().boundingBox()

                    for layer in self.iface.mapCanvas().layers():
                        if layer.id() == self.params.junctions_vlay.id() or\
                                layer.id() == self.params.reservoirs_vlay.id() or\
                                layer.id() == self.params.tanks_vlay.id() or\
                                layer.id() == self.params.pipes_vlay.id() or\
                                layer.id() == self.params.pumps_vlay.id() or\
                                layer.id() == self.params.valves_vlay.id():

                            layer.setSelectedFeatures([])
                            if QGis.QGIS_VERSION_INT < 21600:
                                layer.select(rubber_band_rect, False)
                            else:
                                layer.selectByRect(rubber_band_rect, False)

                    self.rubber_band.reset(QGis.Polygon)

                # No rubber band: clear selection
                else:

                    self.params.junctions_vlay.removeSelection()
                    self.params.reservoirs_vlay.removeSelection()
                    self.params.tanks_vlay.removeSelection()
                    self.params.pipes_vlay.removeSelection()
                    self.params.pumps_vlay.removeSelection()
                    self.params.valves_vlay.removeSelection()
                    self.iface.mapCanvas().refresh()

    def activate(self):

        self.layer_selft.clear()

        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        # Snapping
        QgsProject.instance().setSnapSettingsForLayer(self.params.junctions_vlay.id(),
                                                      False,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.reservoirs_vlay.id(),
                                                      False,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.tanks_vlay.id(),
                                                      False,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(self.params.junctions_vlay)
        snap_layer_reservoirs = NetworkUtils.set_up_snap_layer(self.params.reservoirs_vlay)
        snap_layer_tanks = NetworkUtils.set_up_snap_layer(self.params.tanks_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, snapping_type=QgsSnapper.SnapToSegment)

        self.snapper = NetworkUtils.set_up_snapper(
            [snap_layer_junctions, snap_layer_reservoirs, snap_layer_tanks, snap_layer_pipes],
            self.iface.mapCanvas())

        # Editing
        if not self.params.junctions_vlay.isEditable():
            self.params.junctions_vlay.startEditing()
        if not self.params.reservoirs_vlay.isEditable():
            self.params.reservoirs_vlay.startEditing()
        if not self.params.tanks_vlay.isEditable():
            self.params.tanks_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()
        if not self.params.pumps_vlay.isEditable():
            self.params.pumps_vlay.startEditing()
        if not self.params.valves_vlay.isEditable():
            self.params.valves_vlay.startEditing()

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def show_rect(self, start_point, end_point):

        self.rubber_band.reset(QGis.Polygon)
        if start_point.x() == end_point.x() or start_point.y() == end_point.y():
            return

        point1 = QgsPoint(start_point.x(), start_point.y())
        point2 = QgsPoint(start_point.x(), end_point.y())
        point3 = QgsPoint(end_point.x(), end_point.y())
        point4 = QgsPoint(end_point.x(), start_point.y())

        self.rubber_band.addPoint(point1, False)
        self.rubber_band.addPoint(point2, False)
        self.rubber_band.addPoint(point3, False)
        self.rubber_band.addPoint(point4, True)  # true to update canvas
        self.rubber_band.show()
