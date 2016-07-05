# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QCursor, QColor
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnapper
from qgis.core import QgsPoint, QgsRaster, QgsVectorLayer, QgsProject, QgsSnapper, QgsTolerance, QGis,\
    QgsVectorDataProvider, QgsFeature, QgsGeometry
from ..geo_utils import utils as geo_utils
from .. import parameters
from ..network import Node


class AddNodeTool(QgsMapTool):

    def __init__(self, data_dock, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())

        self.iface = iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""

        # This is for snapping:
        self.nodes_vlay_id = geo_utils.LayerUtils.get_lay_id('nodes')  # TODO: softocode
        self.nodes_vlay = geo_utils.LayerUtils.get_lay_from_id(self.nodes_vlay_id)
        self.pipes_vlay_id = geo_utils.LayerUtils.get_lay_id('pipes')  # TODO: softcode
        self.pipes_vlay = geo_utils.LayerUtils.get_lay_from_id(self.pipes_vlay_id)

        self.mouse_pt = None
        self.mouse_clicked = False
        self.snapped_feat_id = None
        self.snapped_vertex = None
        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.elev = -1

    def canvasPressEvent(self, event):
        if event.button() == Qt.RightButton:
            self.mouse_clicked = False

        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        dem_lay = parameters.Parameters.selected_dem_lay
        identify_dem = dem_lay.dataProvider().identify(self.mouse_pt, QgsRaster.IdentifyFormatValue)
        if identify_dem is not None and identify_dem.isValid() and identify_dem.results().get(1) is not None:
            self.elev = identify_dem.results().get(1)
            self.data_dock.lbl_elev_val.setText("{0:.2f}".format(self.elev))

        if not self.mouse_clicked:
            # Mouse not clicked: snapping to closest vertex
            snapper = QgsMapCanvasSnapper(self.canvas())
            (retval, result) = snapper.snapToBackgroundLayers(event.pos())

            if len(result) > 0:
                # It's a vertex on an existing pipe

                self.snapped_feat_id = result[0].snappedAtGeometry

                snapped_vertex = result[0].snappedVertex

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
            print 'return'
            return
        if event.button() == Qt.LeftButton:
            print 'release'
            self.mouse_clicked = False

            # Find first available ID for Nodes
            eid = self.find_next_id()

            self.nodes_vlay.beginEditCommand("Add node")
            caps = self.nodes_vlay.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.AddFeatures:
                new_node_ft = QgsFeature(self.nodes_vlay.pendingFields())
                new_node_ft.setAttribute(Node.eid_field_name, eid)
                new_node_ft.setAttribute(Node.elevation_field_name, self.elev)
                new_node_ft.setGeometry(QgsGeometry.fromPoint(self.snapped_vertex))
                self.nodes_vlay.addFeatures([new_node_ft])
            self.nodes_vlay.endEditCommand()

    def activate(self):

        QgsProject.instance().setSnapSettingsForLayer(self.pipes_vlay_id,
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      QgsTolerance.MapUnits,
                                                      100,
                                                      True)

    def deactivate(self):
        pass

    def isZoomTool(self):
        return False

    def isTransient(self):
        return False

    def isEditTool(self):
        return True

    def reset_marker(self):
        self.outlet_marker.hide()
        self.canvas().scene().removeItem(self.outlet_marker)

    def find_next_id(self):
        features = self.nodes_vlay.getFeatures()
        max_eid = -1
        for feat in features:
            eid = feat.attribute(Node.eid_field_name)
            eid_val = int(eid[1:len(eid)])
            max_eid = max(max_eid, eid_val)

        max_eid += 1
        max_eid = max(max_eid, 1)
        return 'P' + str(max_eid)