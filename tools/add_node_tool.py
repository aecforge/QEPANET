# -*- coding: utf-8 -*-

from PyQt4.QtCore import Qt, QTimer
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand
from qgis.core import QgsPoint, QgsRaster, QgsVectorLayer, QgsProject, QgsSnapper, QgsTolerance, QGis
from ..geo_utils import utils as geo_utils


class AddNodeTool(QgsMapTool):

    def __init__(self, data_dock, iface):
        QgsMapTool.__init__(self, iface.mapCanvas())

        self.iface = iface
        """:type : QgisInterface"""
        self.data_dock = data_dock
        """:type : DataDock"""

        # This is for snapping:
        self.outlet_marker = QgsVertexMarker(self.canvas())

        self.mouseClicked = None
        self.rubber_bands_lines = []

    def canvasPressEvent(self, event):
        pass

    def canvasMoveEvent(self, event):
        x = event.pos().x()
        y = event.pos().y()
        pt = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(x, y)

    def canvasReleaseEvent(self, event):

        if not self.mouseClicked:
            return
        if event.button() == 1:
            self.mouseClicked = False
            self.rbAcc.reset(True)

            # Get the click
            x = event.pos().x()
            y = event.pos().y()

            pt = self.iface.mapCanvas().getCoordinateTransform().toMapCoordinates(x, y)

    def activate(self):

        pipes_vlay_id = geo_utils.LayerUtils.get_lay_id('pipes')  # TODO: softocode
        QgsProject.instance().setSnapSettingsForLayer(pipes_vlay_id,
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