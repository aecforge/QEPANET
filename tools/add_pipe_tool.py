# -*- coding: utf-8 -*-

import sys
import traceback

from PyQt4.QtCore import Qt, QPoint
from PyQt4.QtGui import QColor, QMenu
from qgis.core import QgsPoint, QgsSnapper, QgsGeometry, QgsProject, QgsTolerance
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand

from ..model.network import Pipe, Junction
from ..model.network_handling import LinkHandler, NodeHandler, NetworkUtils
from parameters import Parameters
from ..geo_utils import raster_utils, vector_utils
from ..ui.section_editor import PipeSectionDialog
from ..ui.diameter_dialog import DiameterDialog


class AddPipeTool(QgsMapTool):

    def __init__(self, data_dock, params):
        QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

        self.iface = data_dock.iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""
        self.params = params

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
        self.elev = None

        self.diameter_dialog = None

    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_clicked = False

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        last_ix = self.rubber_band.numberOfVertices()

        self.rubber_band.movePoint(last_ix - 1, (self.snapped_vertex if self.snapped_vertex is not None else self.mouse_pt))

        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, self.mouse_pt, 1)
        self.elev = elev
        if elev is not None:
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))
        else:
            self.data_dock.lbl_elev_val.setText('-')

        # Mouse not clicked: snapping to closest vertex
        (retval, result) = self.snapper.snapMapPoint(self.mouse_pt)

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

            # try:

                pipe_band_geom = self.rubber_band.asGeometry()

                # No rubber band geometry and feature snapped: pop the context menu
                if pipe_band_geom is None and self.snapped_feat_id is not None:
                    menu = QMenu()
                    section_action = menu.addAction('Section...')  # TODO: softcode
                    diameter_action = menu.addAction('Change diameter...')  # TODO: softcode
                    action = menu.exec_(self.iface.mapCanvas().mapToGlobal(QPoint(event.pos().x(), event.pos().y())))

                    pipe_ft = vector_utils.get_feats_by_id(self.params.pipes_vlay, self.snapped_feat_id)[0]
                    if action == section_action:
                        if self.params.dem_rlay is None:
                            self.iface.messageBar().pushWarning(
                                Parameters.plug_in_name,
                                'No DEM selected. Cannot edit section!')  # TODO: softcode
                        else:
                            pipe_dialog = PipeSectionDialog(
                                self.iface.mainWindow(),
                                self.iface,
                                self.params,
                                pipe_ft)
                            pipe_dialog.exec_()

                    elif action == diameter_action:

                        old_diam = pipe_ft.attribute(Pipe.field_name_diameter)
                        self.diameter_dialog = DiameterDialog(self.iface.mainWindow(), self.params, old_diam)
                        self.diameter_dialog.exec_()  # Exec creates modal dialog
                        new_diameter = self.diameter_dialog.get_diameter()
                        if new_diameter is None:
                            return

                        # Update pipe diameter
                        vector_utils.update_attribute(self.params.pipes_vlay, pipe_ft, Pipe.field_name_diameter, new_diameter)

                        # Check if a valve is present
                        adj_valves = NetworkUtils.find_links_adjacent_to_link(
                            self.params, self.params.pipes_vlay, pipe_ft, True, True, False)

                        if adj_valves['valves']:
                            self.iface.messageBar().pushWarning(
                                Parameters.plug_in_name,
                                'Valves detected on the pipe: need to update their diameters too!')  # TODO: softcode

                    return

                # There's a rubber band: create new pipe
                if pipe_band_geom is not None:
                    # Finalize line
                    rubberband_pts = pipe_band_geom.asPolyline()[:-1]
                    rubberband_pts = self.remove_duplicated_point(rubberband_pts)

                    if len(rubberband_pts) < 2:
                        return

                    # Check whether the pipe points are located on existing nodes
                    junct_nrs = [0]
                    for p in range(1, len(rubberband_pts) - 1):
                        overlapping_nodes = NetworkUtils.find_overlapping_nodes(self.params, rubberband_pts[p])
                        if overlapping_nodes['junctions'] or overlapping_nodes['reservoirs'] or overlapping_nodes['tanks']:
                            junct_nrs.append(p)

                    junct_nrs.append(len(rubberband_pts) - 1)

                    new_pipes_nr = len(junct_nrs) - 1

                    new_pipes_fts = []
                    new_pipes_eids = []

                    for np in range(new_pipes_nr):

                        demand = float(self.data_dock.txt_pipe_demand.text())
                        diameter = float(self.data_dock.txt_pipe_diameter.text())
                        loss = float(self.data_dock.txt_pipe_loss.text())
                        roughness = float(self.data_dock.lbl_pipe_roughness_val_val.text())
                        status = self.data_dock.cbo_pipe_status.currentText()
                        material = self.data_dock.cbo_pipe_roughness.currentText()
                        pipe_eid = NetworkUtils.find_next_id(self.params.pipes_vlay, Pipe.prefix)  # TODO: softcode

                        pipe_ft = LinkHandler.create_new_pipe(
                            self.params,
                            pipe_eid,
                            diameter,
                            loss,
                            roughness,
                            status,
                            material,
                            rubberband_pts[junct_nrs[np]:junct_nrs[np+1]+1],
                            True)
                        self.rubber_band.reset()

                        new_pipes_fts.append(pipe_ft)
                        new_pipes_eids.append(pipe_eid)

                    # Create start and end node, if they don't exist
                    (start_junction, end_junction) = NetworkUtils.find_start_end_nodes(self.params, new_pipes_fts[0].geometry())
                    new_start_junction = None
                    if not start_junction:
                        new_start_junction = rubberband_pts[0]
                        junction_eid = NetworkUtils.find_next_id(self.params.junctions_vlay, Junction.prefix)
                        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, new_start_junction, 1)
                        depth = float(self.data_dock.txt_junction_depth.text())
                        j_demand = float(self.data_dock.txt_junction_demand.text())

                        pattern = self.data_dock.cbo_junction_pattern.itemData(
                            self.data_dock.cbo_junction_pattern.currentIndex())
                        if pattern is not None:
                            pattern_id = pattern.id
                        else:
                            pattern_id = None
                        NodeHandler.create_new_junction(self.params, new_start_junction, junction_eid, elev, j_demand, depth, pattern_id)

                    (start_junction, end_junction) = NetworkUtils.find_start_end_nodes(self.params, new_pipes_fts[len(new_pipes_fts) - 1].geometry())
                    new_end_junction = None
                    if not end_junction:
                        new_end_junction = rubberband_pts[len(rubberband_pts) - 1]
                        junction_eid = NetworkUtils.find_next_id(self.params.junctions_vlay, Junction.prefix)
                        elev = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, new_end_junction, 1)
                        depth = float(self.data_dock.txt_junction_depth.text())

                        pattern = self.data_dock.cbo_junction_pattern.itemData(
                            self.data_dock.cbo_junction_pattern.currentIndex())
                        if pattern is not None:
                            pattern_id = pattern.id
                        else:
                            pattern_id = None
                        NodeHandler.create_new_junction(self.params, new_end_junction, junction_eid, elev, demand, depth, pattern_id)

                    # If end or start node intersects a pipe, split it
                    if new_start_junction:
                        for pipe_ft in self.params.pipes_vlay.getFeatures():
                            if pipe_ft.attribute(Pipe.field_name_eid) != new_pipes_eids[0] and\
                                            pipe_ft.geometry().distance(QgsGeometry.fromPoint(new_start_junction)) < self.params.tolerance:
                                LinkHandler.split_pipe(self.params, pipe_ft, new_start_junction)

                    if new_end_junction:
                        for pipe_ft in self.params.pipes_vlay.getFeatures():
                            if pipe_ft.attribute(Pipe.field_name_eid) != new_pipes_eids[-1] and\
                                            pipe_ft.geometry().distance(QgsGeometry.fromPoint(new_end_junction)) < self.params.tolerance:
                                LinkHandler.split_pipe(self.params, pipe_ft, new_end_junction)

            # except Exception as e:
            #     self.rubber_band.reset()
            #     self.iface.messageBar().pushWarning('Cannot add new pipe to ' + self.params.pipes_vlay.name() + ' layer', repr(e))
            #     traceback.print_exc(file=sys.stdout)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.rubber_band.reset()

    def activate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(self.params.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.params.snap_tolerance,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(self.params.tanks_vlay.id(),
                                                      True,
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
        snap_layer_pipes = NetworkUtils.set_up_snap_layer(self.params.pipes_vlay, None, QgsSnapper.SnapToSegment)

        self.snapper = NetworkUtils.set_up_snapper([snap_layer_junctions, snap_layer_reservoirs, snap_layer_tanks, snap_layer_pipes], self.iface.mapCanvas())

        # Editing
        if not self.params.junctions_vlay.isEditable():
            self.params.junctions_vlay.startEditing()
        if not self.params.pipes_vlay.isEditable():
            self.params.pipes_vlay.startEditing()

    def deactivate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.params.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.params.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(self.params.tanks_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      0,
                                                      True)
        QgsProject.instance().setSnapSettingsForLayer(self.params.pipes_vlay.id(),
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
