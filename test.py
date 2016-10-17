from qgis.core import *

line = QgsGeometry.fromPolyline([QgsPoint(0, 0), QgsPoint(2, 0)])
point = line.nearestPoint(QgsGeometry.fromPoint(QgsPoint(1, 1)))
print point.exportToWkt()