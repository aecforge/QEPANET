from qgis.core import QgsVectorLayer, QgsVectorFileWriter, QgsRectangle, QgsFeatureRequest, QgsPoint, QgsGeometry,\
    QgsFeature
from qgis.PyQt.QtGui import QColor

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
    :type wkb_type: QgsWkbTypes.Type
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


def findSnappedNode(snapper, snap_results, params):

    pt_locator_ju = snapper.locatorForLayer(params.junctions_vlay)
    pt_locator_re = snapper.locatorForLayer(params.reservoirs_vlay)
    pt_locator_ta = snapper.locatorForLayer(params.tanks_vlay)
    match_ju = pt_locator_ju.nearestVertex(snap_results.point(), 1)
    match_re = pt_locator_re.nearestVertex(snap_results.point(), 1)
    match_ta = pt_locator_ta.nearestVertex(snap_results.point(), 1)

    if match_ju.isValid() or match_re.isValid() or match_ta.isValid():

        if match_ju.isValid():
            node_feat_id = match_ju.featureId()
            request = QgsFeatureRequest().setFilterFid(node_feat_id)
            node = list(params.junctions_vlay.getFeatures(request))
            selected_node_ft_lay = params.junctions_vlay

        if match_re.isValid():
            node_feat_id = match_re.featureId()
            request = QgsFeatureRequest().setFilterFid(node_feat_id)
            node = list(params.reservoirs_vlay.getFeatures(request))
            selected_node_ft_lay = params.reservoirs_vlay

        if match_ta.isValid():
            node_feat_id = match_ta.featureId()
            request = QgsFeatureRequest().setFilterFid(node_feat_id)
            node = list(params.tanks_vlay.getFeatures(request))
            selected_node_ft_lay = params.tanks_vlay

        selected_node_ft = QgsFeature(node[0])

        return (selected_node_ft_lay, selected_node_ft)

    return (None, None)