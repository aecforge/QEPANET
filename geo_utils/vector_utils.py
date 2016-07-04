from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QGis, QgsSingleSymbolRendererV2, QgsSymbolV2, \
    QgsSimpleLineSymbolLayerV2, QgsSimpleFillSymbolLayerV2, QgsRendererCategoryV2, QgsCategorizedSymbolRendererV2, \
    QgsLineSymbolV2, QgsRectangle, QgsFeatureRequest, QgsPoint, QgsGeometry
from PyQt4.QtGui import QColor

__author__ = 'deluca'


def load_shp_to_layer(shp_path, layer_name='xxx'):

    vlayer = QgsVectorLayer(shp_path, layer_name, "ogr")

    if not vlayer.isValid():
        raise NameError("Error opening Shapefile: ", shp_path)

    return vlayer


def save_layer2shapefile(vlayer, shp_path):
    """
    :type vlayer: QgsVectorLayer
    :type shp_path: String
    :type wkb_type: QGis.WkbType
    :return:
    """

    error = QgsVectorFileWriter.writeAsVectorFormat(vlayer, shp_path, "CP1250", vlayer.crs(), "ESRI Shapefile")


def get_ws_renderer():
    """
    :rtype: QgsSingleSymbolRendererV2
    """

    # Colors
    fill_color = QColor()
    fill_color.setRgb(0, 0, 255)
    fill_color.setAlpha(64)
    border_color = QColor()
    border_color.setRgb(0, 0, 255)
    border_color.setAlpha(255)

    # Symbol layer
    symbol_layer = QgsSimpleFillSymbolLayerV2()
    symbol_layer.setBorderColor(border_color)
    symbol_layer.setFillColor(fill_color)

    symbol = QgsSymbolV2.defaultSymbol(QGis.Polygon)
    """:type : QgsSymbolV2"""
    symbol.changeSymbolLayer(0, symbol_layer)

    # Renderer
    renderer = QgsSingleSymbolRendererV2(symbol)
    """:type : QgsSingleSymbolRendererV2"""
    return renderer


def get_channel_renderer():
    """
    :rtype: QgsSingleSymbolRendererV2
    """

    symbol = QgsLineSymbolV2 ()
    symbol.setColor(QColor(0, 0, 255))
    symbol.setWidth(1)

    categories = [QgsRendererCategoryV2("Collettore", symbol, "Collettore principale")]

    renderer = QgsCategorizedSymbolRendererV2("", categories)
    renderer.setClassAttribute("Coll")
    return renderer

    # # Symbol layer
    # symbol_layer = QgsSimpleLineSymbolLayerV2()
    # symbol_layer.setColor(QColor(0, 0, 255))
    # symbol_layer.setWidth(1)
    #
    # symbol = QgsSymbolV2.defaultSymbol(QGis.Line)
    # symbol.changeSymbolLayer(0, symbol_layer)
    #
    # # Renderer
    # renderer = QgsSingleSymbolRendererV2(symbol)
    # return renderer


def find_closest_feature(vlayer, map_coord, tolerance_units):

    search_rect = QgsRectangle(map_coord.x() - tolerance_units,
                               map_coord.y() - tolerance_units,
                               map_coord.x() + tolerance_units,
                               map_coord.y() + tolerance_units)
    request = QgsFeatureRequest()
    request.setFilterRect(search_rect)
    request.setFlags(QgsFeatureRequest.ExactIntersect)
    for feature in vlayer.getFeatures(request):
        return feature


def find_closest_point_on_geometry(coord, geom):
    """
    :param coord:
    :type coord: QgsPoint
    :param geom:
    :type geom: QgsGeometry
    :return:
    """

    return geom.closestSegmentWithContext(coord)[1]