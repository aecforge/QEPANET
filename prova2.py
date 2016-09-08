import PyQt4.QtCore
import PyQt4.QtGui
import qgis.core
import qgis.gui

class Caghe1:



    def __init__(self):
        # Densify vertices
        import qgis.core as qc
        import sys

        qc.QgsApplication.setPrefixPath("C:/OSGeo4W64/bin", True)
        qgs = qc.QgsApplication(sys.argv, False)
        qgs.initQgis()

        from qgis.core import QgsGeometry, QgsPoint, QgsPointV2, QgsWKBTypes, QgsLineStringV2

        points = [QgsPoint(0, 0), QgsPoint(0, 1)]
        pipe_geom_2 = QgsGeometry.fromPolyline(points)

        line_coords = []
        for vertex in pipe_geom_2.asPolyline():
            line_coords.append(QgsPointV2(QgsWKBTypes.PointZ, vertex.x(), vertex.y(), 100))

        linestring = QgsLineStringV2()
        linestring.setPoints(line_coords)
        geom_3d = QgsGeometry(linestring)

caghe = Caghe1()