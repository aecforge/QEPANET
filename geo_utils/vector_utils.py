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
    return error


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


def find_closest_vertex_on_geometry(coord, geom):
    """
    :param coord:
    :type coord: QgsPoint
    :param geom:
    :type geom: QgsGeometry
    :return:
    """

    return geom.closestSegmentWithContext(coord)[1]


def get_feats_by_id(vlay, ft_id):
    if ft_id is None:
        return None
    request = QgsFeatureRequest().setFilterFid(ft_id)
    feats = list(vlay.getFeatures(request))
    return feats


def update_attribute(layer, feat, attribute_name, new_val, edit_command_name='Update attribute'):

    layer.beginEditCommand(edit_command_name)

    layer.changeAttributeValue(
        feat.id(),
        feat.fieldNameIndex(attribute_name),
        new_val)

    layer.endEditCommand()