# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt, QTimer
from PyQt4.QtGui import QCursor, QColor
from qgis.gui import QgsMapTool, QgsVertexMarker, QgsRubberBand, QgsMapCanvasSnapper
from qgis.core import QgsPoint, QgsRaster, QgsVectorLayer, QgsProject, QgsSnapper, QgsTolerance, QGis, QgsFeatureRequest, QgsFeature, QgsGeometry
import qgis
from ..geo_utils import utils as geo_utils
from ..geo_utils import vector_utils as vutils


class MoveNodeTool(QgsMapTool):

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

        self.outlet_marker = QgsVertexMarker(self.canvas())

        self.vertex_marker = QgsVertexMarker(self.canvas())
        self.mouse_clicked = False
        self.snapped_feat_id = None

        self.rubber_bands_d = {}

    def canvasPressEvent(self, event):

        if self.snapped_feat_id is None:
            return

        if event.button() == Qt.RightButton:
            self.mouse_clicked = False
        if event.button() == Qt.LeftButton:
            self.mouse_clicked = True
            request = QgsFeatureRequest().setFilterFid(self.snapped_feat_id)
            list = [feat for feat in self.nodes_vlay.getFeatures(request)]
            selected_node_ft = QgsFeature(list[0])
            selected_node_ft_eid = selected_node_ft.attribute('id')  # TODO: softcode

            # Find links that start or end in selected point
            expression = u'"start_node" = \'' + selected_node_ft_eid + '\' or "end_node" = \'' + selected_node_ft_eid + '\''
            request = QgsFeatureRequest().setFilterExpression(expression)
            adjacent_pipes_fts = self.pipes_vlay.getFeatures(request)

            rb_index = 0;
            for adjacent_pipes_ft in adjacent_pipes_fts:
                closest = adjacent_pipes_ft.geometry().closestVertex(selected_node_ft.geometry().asPoint())

                next_vertext_id = -1
                if closest[1] == 0:
                    next_vertext_id = closest[1] + 1
                else:
                    next_vertext_id = closest[1] - 1

                rubber_band_start_pt = adjacent_pipes_ft.geometry().vertexAt(next_vertext_id)

                self.rubber_bands_d[rb_index] = QgsRubberBand(self.canvas(), False)  # False = not a polygon
                points = [rubber_band_start_pt, selected_node_ft.geometry().asPoint()]
                self.rubber_bands_d[rb_index].setToGeometry(QgsGeometry.fromPolyline(points), None)
                self.rubber_bands_d[rb_index].setColor(QColor(255, 128, 128))
                self.rubber_bands_d[rb_index].setWidth(1)
                self.rubber_bands_d[rb_index].setBrushStyle(Qt.Dense4Pattern)

                rb_index += 1

    def canvasMoveEvent(self, event):

        if not self.mouse_clicked:
            # Mouse not clicked: snapping to closest vertex
            snapper = QgsMapCanvasSnapper(self.canvas())
            (retval, result) = snapper.snapToCurrentLayer(event.pos(), QgsSnapper.SnapToVertex, -1)

            if len(result) > 0:

                self.snapped_feat_id = result[0].snappedAtGeometry

                snapped_vertex = result[0].snappedVertex

                self.vertex_marker.setCenter(QgsPoint(snapped_vertex.x(), snapped_vertex.y()))
                self.vertex_marker.setColor(QColor(255, 0, 0))
                self.vertex_marker.setIconSize(10)
                self.vertex_marker.setIconType(QgsVertexMarker.ICON_CIRCLE)  # or ICON_CROSS, ICON_X
                self.vertex_marker.setPenWidth(3)
                self.vertex_marker.show()
            else:
                self.snapped_feat_id = None
                self.vertex_marker.hide()

        else:
            if self.snapped_feat_id is not None:
                # Mouse clicked and vertex selected
                pt = self.toMapCoordinates(event.pos())

                # Update rubber bands
                for key, value in self.rubber_bands_d.iteritems():
                    self.rubber_bands_d[key].movePoint(1, pt)

    def canvasReleaseEvent(self, event):

        if not self.mouse_clicked:
            return
        if event.button() == 1:
            self.mouse_clicked = False

            # Remove rubber bands
            for key in self.rubber_bands_d.keys():
                self.iface.mapCanvas().scene().removeItem(self.rubber_bands_d[key])
                del self.rubber_bands_d[key]

    def activate(self):

        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

        QgsProject.instance().setSnapSettingsForLayer(self.nodes_vlay_id,
                                                      True,
                                                      QgsSnapper.SnapToVertex,
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