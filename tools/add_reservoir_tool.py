# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsFeature, QgsFeatureRequest
from qgis.gui import QgsMapTool, QgsVertexMarker

from network_handling import LinkHandler, NodeHandler, NetworkUtils
from parameters import Parameters
from ..geo_utils import raster_utils


class AddReservoirTool(QgsMapTool):

    def __init__(self, data_dock):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""

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

        elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, self.mouse_pt, 1)

        if elev is not None:
            self.elev = elev
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        if not self.mouse_clicked:

            # Mouse not clicked: snapping to closest vertex
            (retval, result) = self.snapper.snapPoint(event.pos())
            if len(result) > 0:
                # It's a vertex on an existing pipe
                self.snapped_feat_id = result[0].snappedAtGeometry

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
                self.snapped_feat_id = None
                self.vertex_marker.hide()

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return

        if event.button() == Qt.LeftButton:

            self.mouse_clicked = False

            # Find first available ID for reservoirs
            eid = NetworkUtils.find_next_id(Parameters.reservoirs_vlay, 'R') # TODO: softcode

            pressure = float(self.data_dock.txt_reservoir_pressure.text())
            elev_corr = float(self.data_dock.txt_reservoir_elev_corr.text())

            # No links snapped: create a new stand-alone node
            if self.snapped_feat_id is None:

                NodeHandler.create_new_reservoir(
                    Parameters.reservoirs_vlay,
                    self.mouse_pt,
                    eid,
                    self.elev,
                    elev_corr,
                    pressure)

            # A link has been snapped
            else:

                # New node on existing line
                NodeHandler.create_new_reservoir(
                    Parameters.reservoirs_vlay,
                    self.snapped_vertex,
                    eid,
                    self.elev,
                    elev_corr,
                    pressure)

                # Get the snapped pipe and split it
                request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
                feats = list(Parameters.pipes_vlay.getFeatures(request))
                if len(feats) > 0:

                    snapped_pipe = QgsFeature(feats[0])
                    (start_node_ft, end_node_ft) = NetworkUtils.get_start_end_nodes(snapped_pipe.geometry())

                    # Check that the snapped point on pipe is distant enough from start/end nodes
                    if start_node_ft.geometry().distance(self.snapped_vertex) > Parameters.min_dist and\
                        end_node_ft.geometry().distance(self.snapped_vertex) > Parameters.min_dist:
                        LinkHandler.split_pipe(snapped_pipe, self.snapped_vertex)

    def activate(self):

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(Parameters.pipes_vlay, None, QgsSnapper.SnapToSegment)

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_pipes], self.iface.mapCanvas())

    def deactivate(self):
        self.data_dock.btn_add_reservoir.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def reset_marker(self):
        self.outlet_marker.hide()
        self.canvas().scene().removeItem(self.outlet_marker)