# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QCursor, QColor
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand
from qgis.core import QgsPoint, QgsRaster, QgsVectorLayer, QgsProject, QgsSnapper, QgsTolerance, QGis,\
    QgsVectorDataProvider, QgsFeature, QgsGeometry, QgsFeatureRequest, QgsLineStringV2, QgsPointV2
from ..geo_utils import utils as geo_utils
from ..parameters import Parameters
from ..network import Junction, Pipe
from network_handling import LinkHandler, NodeHandler, NetworkUtils


class AddJunctionTool(QgsMapTool):

    def __init__(self, data_dock, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())

        self.iface = iface
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

        dem_lay = Parameters.dem_rlay
        identify_dem = dem_lay.dataProvider().identify(self.mouse_pt, QgsRaster.IdentifyFormatValue)
        if identify_dem is not None and identify_dem.isValid() and identify_dem.results().get(1) is not None:
            self.elev = identify_dem.results().get(1)
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

            # Find first available ID for Nodes
            node_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'N')

            nodes_caps = Parameters.junctions_vlay.dataProvider().capabilities()
            pipes_caps = Parameters.pipes_vlay.dataProvider().capabilities()

            demand = float(self.data_dock.txt_node_demand.text())
            depth = float(self.data_dock.txt_node_depth.text())
            pattern = self.data_dock.cbo_node_pattern.currentText()

            if nodes_caps and pipes_caps and QgsVectorDataProvider.AddFeatures and QgsVectorDataProvider.DeleteFeatures:
                if self.snapped_feat_id is None:

                    # New stand-alone node
                    NodeHandler.create_new_junction(
                            Parameters.junctions_vlay,
                            self.mouse_pt,
                            node_eid,
                            self.elev,
                            demand,
                            depth,
                            pattern)

                else:

                    # Snapped on endline: just add node
                    # TODO

                    # Snapped along line: split line
                    Parameters.pipes_vlay.beginEditCommand("Add new pipes")

                    # New node on existing line
                    NodeHandler.create_new_junction(
                            Parameters.junctions_vlay,
                            self.snapped_vertex,
                            node_eid,
                            self.elev,
                            demand,
                            depth,
                            pattern)

                    # Get the snapped feature
                    request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
                    feats = [feat for feat in Parameters.pipes_vlay.getFeatures(request)]
                    snapped_pipe = QgsFeature(feats[0])

                    # Get vertex along line next to snapped point
                    a, b, next_vertex = snapped_pipe.geometry().closestSegmentWithContext(self.snapped_vertex)

                    # Split only if vertex is not at line ends
                    loss = snapped_pipe.attribute(Pipe.field_name_loss)
                    roughness = snapped_pipe.attribute(Pipe.field_name_roughness)
                    status = snapped_pipe.attribute(Pipe.field_name_status)

                    if self.snapped_vertex_nr != 0:

                        # Create two new linestrings
                        nodes = snapped_pipe.geometry().asPolyline()

                        # First new polyline
                        pl1_pts = []
                        for n in range(next_vertex):
                            pl1_pts.append(QgsPoint(nodes[n].x(), nodes[n].y()))

                        pl1_pts.append(QgsPoint(self.snapped_vertex.x(), self.snapped_vertex.y()))

                        pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'J')
                        LinkHandler.create_new_pipe(Parameters.pipes_vlay, pipe_eid, 0, 0, loss, roughness, status, pl1_pts, Parameters.dem_rlay)

                        # Second new polyline
                        pl2_pts = []
                        pl2_pts.append(QgsPoint(self.snapped_vertex.x(), self.snapped_vertex.y()))
                        for n in range(len(nodes) - next_vertex):
                            pl2_pts.append(QgsPoint(nodes[n + next_vertex].x(), nodes[n + next_vertex].y()))

                        pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'J')
                        LinkHandler.create_new_pipe(Parameters.pipes_vlay, pipe_eid, 0, 0, loss, roughness, status, pl2_pts, Parameters.dem_rlay)

                        # Delete old pipe
                        Parameters.pipes_vlay.deleteFeature(snapped_pipe.id())

                        Parameters.pipes_vlay.endEditCommand()

    def activate(self):

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(Parameters.pipes_vlay, None, QgsSnapper.SnapToSegment)
        # TODO: remaining layers

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_pipes], self.iface.mapCanvas())

    def deactivate(self):
        self.data_dock.btn_add_junction.setChecked(False)

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def reset_marker(self):
        self.outlet_marker.hide()
        self.canvas().scene().removeItem(self.outlet_marker)