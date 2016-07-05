# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QCursor, QColor
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnapper
from qgis.core import QgsPoint, QgsRaster, QgsVectorLayer, QgsProject, QgsSnapper, QgsTolerance, QGis,\
    QgsVectorDataProvider, QgsFeature, QgsGeometry
from ..geo_utils import utils as geo_utils
from .. import parameters


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
        self.mouseClicked = False
        self.snapped_feat_id = None

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):

        self.mouse_pt = self.toMapCoordinates(event.pos())

        dem_lay = parameters.Parameters.selected_dem_lay
        identify_dem = dem_lay.dataProvider().identify(self.mouse_pt, QgsRaster.IdentifyFormatValue)

        if not self.mouse_clicked:
            # Mouse not clicked: snapping to closest vertex
            snapper = QgsMapCanvasSnapper(self.canvas())
            (retval, result) = snapper.snapToBackgroundLayers(event.pos(), QgsSnapper.SnapToVertexAndSegment, -1)

            if len(result) > 0:
                # It's a vertex on an existing pipe

                self.snapped_feat_id = result[0].snappedAtGeometry

                snapped_vertex = result[0].snappedVertex

                self.vertex_marker.setCenter(QgsPoint(snapped_vertex.x(), snapped_vertex.y()))
                self.vertex_marker.setColor(QColor(255, 0, 0))
                self.vertex_marker.setIconSize(10)
                self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)  # or ICON_CROSS, ICON_X
                self.vertex_marker.setPenWidth(3)
                self.vertex_marker.show()

            else:

                # It's a new, isolated vertex
                self.snapped_feat_id = None
                self.vertex_marker.hide()

        else:
            if self.snapped_feat_id is not None:
                # Mouse clicked and vertex selected
                # Update rubber bands
                for key, value in self.rubber_bands_d.iteritems():
                    self.rubber_bands_d[key].movePoint(1, self.mouse_pt)

    def canvasReleaseEvent(self, event):

        if not self.mouseClicked:
            return
        if event.button() == Qt.LeftButton:
            self.mouseClicked = False

            caps = self.nodes_vlay.dataProvider().capabilities()
            if caps & QgsVectorDataProvider.AddFeatures:
                pass
                # feat = QgsFeature(self.nodes_vlay.pendingFields())
                # # Or set a single attribute by key or by index:
                # feat.setAttribute(Node.eid_field_name, ???)
                # feat.setAttribute(Node.elevation_field_name, ???)
                # feat.setGeometry(QgsGeometry.fromPoint(self.mouse_pt))
                # layer.addFeatures([feat])

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

    # def snap_to_point(self, coord):
    #
        # # Snap to closest stream
        # synthnet_lay_id = utils.LayerUtils.get_lay_id(ProjectNames.get_synthnet_layer_name())
        # synthnet_lay = utils.LayerUtils.get_lay_from_id(synthnet_lay_id)
        #
        # closest_feat = vutils.find_closest_feature(synthnet_lay, coord, 100)
        #
        # if closest_feat is not None:
        #
        #     closest_point = vutils.find_closest_point_on_geometry(coord, closest_feat.geometry())
        #     TestTool.outlet_pt = closest_point
        #
        #     # Flash cursor position
        #     self.outlet_marker = QgsVertexMarker(self.canvas())
        #     self.outlet_marker.setIconSize(20)
        #     self.outlet_marker.setCenter(TestTool.outlet_pt)
        #     self.outlet_marker.setIconType(QgsVertexMarker.ICON_X)
        #
        #     # if QGis.QGIS_VERSION_INT >= 21200:
        #     #     self.outlet_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)
        #
        #     self.outlet_marker.setColor(Qt.red)
        #     self.outlet_marker.show()
        #     QTimer.singleShot(500, self.reset_marker)