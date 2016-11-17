import sys
from collections import OrderedDict
from qgis.core import *
from PyQt4.QtGui import *
from sipconfig import _Macro


class RampRenderer:

    def __init__(self):
        pass

    @staticmethod
    def get_renderer(layer, field_name, ranges_colors=None):

        feats = layer.getFeatures()

        min_val = sys.float_info.max
        max_val = -min_val

        for feat in feats:
            attr = feat.attribute(field_name)
            val = float(attr)
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val

        if ranges_colors is None:
            ranges_colors = []
            colors = [
                QColor(0, 255, 0),
                QColor(128, 255, 0),
                QColor(255, 255, 0),
                QColor(255, 128, 0),
                QColor(255, 0, 0)]

            intv_nr = len(colors)
            intv = (max_val - min_val) / intv_nr
            for c in range(intv_nr):
                vrange = [min_val + intv * c, min_val + intv * (c + 1)]

                if c == len(colors) - 1:
                    vrange[1] = max_val

                ranges_colors.append([vrange, colors[c]])

        range_list = []
        for range_col in ranges_colors:
            r_min = range_col[0][0]
            r_max = range_col[0][1]
            title = str(r_min) + ' - ' + str(r_max)
            range_list.append(RampRenderer.symbology_from_range(layer, r_min, r_max, range_col[1], title))

        renderer = QgsGraduatedSymbolRendererV2(field_name, range_list)
        return renderer

    @staticmethod
    def symbology_from_range(layer, min_val, max_val, color, title):
        symbol = RampRenderer.get_default_symbol(layer.geometryType())
        symbol.setColor(color)
        srange = QgsRendererRangeV2(min_val, max_val, symbol, title)
        return srange

    @staticmethod
    def get_default_symbol(geom_type):
        symbol = QgsSymbolV2.defaultSymbol(geom_type)
        if symbol is None:
            if geom_type == QGis.Point:
                symbol = QgsMarkerSymbolV2()
            elif geom_type == QGis.Line:
                symbol = QgsLineSymbolV2()
            elif geom_type == QGis.Polygon:
                symbol = QgsFillSymbolV2()
        return symbol