# -*- coding: utf-8 -*-

import sys, traceback

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QCursor, QColor
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMessageBar
from qgis.core import QgsPoint, QgsRaster, QgsVectorLayer, QgsProject, QgsSnapper, QgsTolerance, QGis,\
    QgsVectorDataProvider, QgsFeature, QgsGeometry, QgsFeatureRequest, QgsLineStringV2, QgsPointV2
from ..geo_utils import utils as geo_utils
from ..parameters import Parameters
from ..network import Junction, Pipe
from network_handling import LinkHandler, NodeHandler, NetworkUtils


class AddPipeTool(QgsMapTool):

    def __init__(self, data_dock, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())

        self.iface = iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""

        self.mouse_pt = None
        self.mouse_clicked = False
        self.first_click = False
        self.rubber_band = QgsRubberBand(self.canvas(), False)
        self.rubber_band.setColor(QColor(255, 128, 128))
        self.rubber_band.setWidth(1)
        self.rubber_band.setBrushStyle(Qt.Dense4Pattern)
        self.rubber_band.reset()

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

        last_ix = self.rubber_band.numberOfVertices()

        self.rubber_band.movePoint(last_ix - 1, (self.snapped_vertex if self.snapped_vertex is not None else self.mouse_pt))

        dem_lay = Parameters.dem_rlay
        identify_dem = dem_lay.dataProvider().identify(self.mouse_pt, QgsRaster.IdentifyFormatValue)
        if identify_dem is not None and identify_dem.isValid() and identify_dem.results().get(1) is not None:
            self.elev = identify_dem.results().get(1)
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        # Mouse not clicked: snapping to closest vertex
        (retval, results) = self.snapper.snapPoint(event.pos())

        if len(results) > 0:

            # Pipe starts from an existing vertex
            self.snapped_feat_id = results[0].snappedAtGeometry

            snapped_vertex = results[0].snappedVertex
            self.snapped_vertex_nr = results[0].snappedVertexNr

            self.snapped_vertex = QgsPoint(snapped_vertex.x(), snapped_vertex.y())
            self.vertex_marker.setCenter(self.snapped_vertex)
            self.vertex_marker.setColor(QColor(255, 0, 0))
            self.vertex_marker.setIconSize(10)
            self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
            self.vertex_marker.setPenWidth(3)
            self.vertex_marker.show()

        else:

            # It's a new, isolated pipe
            self.snapped_vertex = None
            self.snapped_feat_id = None
            self.vertex_marker.hide()

    def canvasReleaseEvent(self, event):

        # if not self.mouse_clicked:
        #     return
        if event.button() == Qt.LeftButton:

            # Update rubber bands
            self.rubber_band.addPoint((self.snapped_vertex if self.snapped_vertex is not None else self.mouse_pt), True)
            if self.first_click:
                self.rubber_band.addPoint((self.snapped_vertex if self.snapped_vertex is not None else self.mouse_pt), True)

            # Create new node
            self.first_click = not self.first_click

        elif event.button() == Qt.RightButton:

            try:

                # Finalize line
                pipe_band_geom = self.rubber_band.asGeometry()

                pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'P')

                demand = float(self.data_dock.txt_pipe_demand.text())
                diameter = float(self.data_dock.txt_pipe_diameter.text())
                loss = float(self.data_dock.txt_pipe_loss.text())
                roughness = float(self.data_dock.lbl_pipe_roughness_val_val.text())
                status = self.data_dock.cbo_pipe_status.currentText()

                LinkHandler.create_new_pipe(
                    Parameters.pipes_vlay,
                    pipe_eid,
                    demand,
                    diameter,
                    loss,
                    roughness,
                    status,
                    pipe_band_geom.asPolyline())
                self.rubber_band.reset()

                # Create start and end junctions



            except Exception as e:
                self.rubber_band.reset()
                self.iface.messageBar().pushWarning('Cannot add new pipe to ' + Parameters.pipes_vlay.name() + ' layer', repr(e))
                traceback.print_exc(file=sys.stdout)

    def activate(self):

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(Parameters.pipes_vlay, None, QgsSnapper.SnapToSegment)
        # TODO: remaining layers

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_pipes], self.iface.mapCanvas())

    def deactivate(self):
        self.rubber_band.reset()
        self.data_dock.btn_add_pipe.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def reset_marker(self):
        self.outlet_marker.hide()
        self.canvas().scene().removeItem(self.outlet_marker)