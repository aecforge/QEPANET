# -*- coding: utf-8 -*-

import sys
import traceback

from PyQt4.QtCore import Qt
from PyQt4.QtGui import QColor
from qgis.core import QgsPoint, QgsSnapper, QgsGeometry, QgsProject, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand

from ..model.network import Pipe
from ..model.network_handling import LinkHandler, NodeHandler, NetworkUtils
from parameters import Parameters
from ..geo_utils import raster_utils


class AddPipeTool(QgsMapTool):

    def __init__(self, data_dock):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
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

        elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, self.mouse_pt, 1)
        if elev is not None:
            self.elev = elev
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        # Mouse not clicked: snapping to closest vertex
        (retval, result) = self.snapper.snapMapPoint(self.toMapCoordinates(event.pos()))

        if len(result) > 0:

            # Pipe starts from an existing vertex
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

            self.first_click = not self.first_click

        elif event.button() == Qt.RightButton:

            try:

                # Finalize line
                pipe_band_geom = self.rubber_band.asGeometry()

                rubberband_pts = pipe_band_geom.asPolyline()
                rubberband_pts = self.remove_duplicated_point(rubberband_pts)

                # Check whether the pipe points are located on existing nodes
                junct_nrs = [0]
                for p in range(1, len(rubberband_pts) - 1):
                    overlapping_nodes = NetworkUtils.find_overlapping_nodes(rubberband_pts[p])
                    if overlapping_nodes['junctions'] or overlapping_nodes['reservoirs'] or overlapping_nodes['tanks']:
                        junct_nrs.append(p)

                junct_nrs.append(len(rubberband_pts) - 1)

                new_pipes_nr = len(junct_nrs) - 1

                new_pipes_fts = []
                for np in range(new_pipes_nr):

                    demand = float(self.data_dock.txt_pipe_demand.text())
                    diameter = float(self.data_dock.txt_pipe_diameter.text())
                    loss = float(self.data_dock.txt_pipe_loss.text())
                    roughness = float(self.data_dock.lbl_pipe_roughness_val_val.text())
                    status = self.data_dock.cbo_pipe_status.currentText()
                    pipe_eid = NetworkUtils.find_next_id(Parameters.pipes_vlay, 'P')  # TODO: softcode
                    pipe_ft = LinkHandler.create_new_pipe(
                        pipe_eid,
                        demand,
                        diameter,
                        loss,
                        roughness,
                        status,
                        rubberband_pts[junct_nrs[np]:junct_nrs[np+1]+1])
                    self.rubber_band.reset()

                    new_pipes_fts.append(pipe_ft)

                # Create start and end node, if they don't exist
                (start_junction, end_junction) = NetworkUtils.find_start_end_nodes(new_pipes_fts[0].geometry())
                new_start_junction = None
                if not start_junction:
                    new_start_junction = rubberband_pts[0]
                    junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J') # TODO: sofcode
                    elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, new_start_junction, 1)
                    depth = float(self.data_dock.txt_node_depth.text())
                    if self.data_dock.cbo_node_pattern.currentIndex() != -1:
                        pattern_id = self.data_dock.cbo_node_pattern.itemData(self.data_dock.cbo_node_pattern.currentIndex()).id
                    else:
                        pattern_id = 0
                    NodeHandler.create_new_junction(new_start_junction, junction_eid, elev, demand, depth, pattern_id)

                (start_junction, end_junction) = NetworkUtils.find_start_end_nodes(new_pipes_fts[len(new_pipes_fts) - 1].geometry())
                new_end_junction = None
                if not end_junction:
                    new_end_junction = rubberband_pts[len(rubberband_pts) - 1]
                    junction_eid = NetworkUtils.find_next_id(Parameters.junctions_vlay, 'J')  # TODO: sofcode
                    elev = raster_utils.read_layer_val_from_coord(Parameters.dem_rlay, new_end_junction, 1)
                    depth = float(self.data_dock.txt_node_depth.text())
                    if self.data_dock.cbo_node_pattern.currentIndex() != -1:
                        pattern_id = self.data_dock.cbo_node_pattern.itemData(
                            self.data_dock.cbo_node_pattern.currentIndex()).id
                    else:
                        pattern_id = 0
                    NodeHandler.create_new_junction(new_end_junction, junction_eid, elev, demand, depth, pattern_id)

                # If end or start node intersects a pipe, split it
                if new_start_junction:
                    for pipe_ft in Parameters.pipes_vlay.getFeatures():
                        if pipe_ft.attribute(Pipe.field_name_eid) != pipe_eid and\
                                        pipe_ft.geometry().distance(QgsGeometry.fromPoint(new_start_junction)) < Parameters.tolerance:
                            LinkHandler.split_pipe(pipe_ft, new_start_junction)

                if new_end_junction:
                    for pipe_ft in Parameters.pipes_vlay.getFeatures():
                        if pipe_ft.attribute(Pipe.field_name_eid) != pipe_eid and\
                                        pipe_ft.geometry().distance(QgsGeometry.fromPoint(new_end_junction)) < Parameters.tolerance:
                            LinkHandler.split_pipe(pipe_ft, new_end_junction)

            except Exception as e:
                self.rubber_band.reset()
                self.iface.messageBar().pushWarning('Cannot add new pipe to ' + Parameters.pipes_vlay.name() + ' layer', repr(e))
                traceback.print_exc(file=sys.stdout)

    def activate(self):

        QgsProject.instance().setSnapSettingsForLayer(Parameters.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(Parameters.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(Parameters.tanks_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(Parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      Parameters.snap_tolerance,
                                                      True)

        snap_layer_junctions = NetworkUtils.set_up_snap_layer(Parameters.junctions_vlay)
        snap_layer_reservoirs = NetworkUtils.set_up_snap_layer(Parameters.reservoirs_vlay)
        snap_layer_tanks = NetworkUtils.set_up_snap_layer(Parameters.tanks_vlay)
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(Parameters.pipes_vlay, None, QgsSnapper.SnapToSegment)

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_reservoirs, snap_layer_tanks, snap_layer_pipes], self.iface.mapCanvas())

        # Editing
        if not Parameters.junctions_vlay.isEditable():
            Parameters.junctions_vlay.startEditing()
        if not Parameters.pipes_vlay.isEditable():
            Parameters.pipes_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(Parameters.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(Parameters.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(Parameters.tanks_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(Parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

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

    def remove_duplicated_point(self, pts):

        # This is needed because the rubber band sometimes returns duplicated points

        purged_pts = [pts[0]]
        for p in enumerate(range(len(pts) - 1), 1):
            if pts[p[0]] == pts[p[0]-1]:
                continue
            else:
                purged_pts.append(pts[p[0]])

        return purged_pts
