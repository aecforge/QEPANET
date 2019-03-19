from builtins import str
from builtins import range
from builtins import object
from ..tools.parameters import Parameters
from qgis.PyQt.QtGui import QColor
from qgis.core import QgsSvgMarkerSymbolLayer, QgsSymbol, QgsSingleSymbolRenderer, Qgis, QgsLineSymbol,\
    QgsSimpleLineSymbolLayer, QgsMarkerSymbol, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer, \
    QgsGraduatedSymbolRenderer, QgsRendererRange, QgsFillSymbol, QgsProperty
import os, sys


class NodeSymbology(object):
    def __init__(self):
        pass

    def make_simple_node_sym_renderer(self, size=2):

        symbol = QgsMarkerSymbol().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Point
        sim_marker_sym_lay = QgsSimpleMarkerSymbolLayer()
        sim_marker_sym_lay.setColor(QColor(0, 0, 0))
        sim_marker_sym_lay.setFillColor(QColor(0, 0, 0))
        sim_marker_sym_lay.setSize(size)
        symbol.appendSymbolLayer(sim_marker_sym_lay)

        renderer = QgsSingleSymbolRenderer(symbol)
        return renderer

    def make_svg_node_sym_renderer(self, vlay, icon_name, size):

        current_dir = os.path.dirname(__file__)

        svg_style = dict()
        svg_style['name'] = os.path.join(current_dir, icon_name)
        svg_style['size'] = str(size)
        symbol_layer = QgsSvgMarkerSymbolLayer.create(svg_style)
        symbol = QgsSymbol.defaultSymbol(vlay.geometryType())
        symbol.changeSymbolLayer(0, symbol_layer)
        renderer = QgsSingleSymbolRenderer(symbol)

        return renderer

    def make_graduated_sym_renderer(self, layer, field_name, ranges_colors=None):

        feats = layer.getFeatures()

        min_val = sys.float_info.max
        max_val = -min_val

        # Find values range
        for feat in feats:
            attr = feat.attribute(field_name)
            val = float(attr)
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val

        # Define colors
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
            range_list.append(symbology_from_range(layer, r_min, r_max, range_col[1], title))

        renderer = QgsGraduatedSymbolRenderer(field_name, range_list)

        # Line
        symbol = QgsMarkerSymbol().createSimple({})
        symbol.deleteSymbolLayer(0)
        mark_sym_lay = QgsSimpleMarkerSymbolLayer()
        symbol.appendSymbolLayer(mark_sym_lay)

        # renderer.setSourceSymbol(symbol)
        renderer.updateSymbols(symbol)

        return renderer


class LinkSymbology(object):

    def __init__(self):
        self.marker_sym = None

    def make_simple_link_sym_renderer(self, width=0.2):

        symbol = QgsLineSymbol().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Line
        line_sym_lay = QgsSimpleLineSymbolLayer()
        line_sym_lay.setWidth(width)
        symbol.appendSymbolLayer(line_sym_lay)

        renderer = QgsSingleSymbolRenderer(symbol)
        return renderer

    def make_svg_link_sym_renderer(self, icon_name, svg_size=7, line_width=0.2):

        symbol = QgsLineSymbol().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Line
        line_sym_lay = QgsSimpleLineSymbolLayer()
        line_sym_lay.setWidth(line_width)
        symbol.appendSymbolLayer(line_sym_lay)

        # Symbol
        self.marker_sym = QgsMarkerSymbol.createSimple({})
        self.marker_sym.deleteSymbolLayer(0)

        # marker_sym_lay = QgsSimpleMarkerSymbolLayerV2()
        current_dir = os.path.dirname(__file__)
        svg_props = dict()
        svg_props['name'] = os.path.join(current_dir, icon_name)
        svg_props['size'] = str(svg_size)
        marker_sym_lay = QgsSvgMarkerSymbolLayer.create(svg_props)
        self.marker_sym.appendSymbolLayer(marker_sym_lay)

        marker_line_sym_lay = QgsMarkerLineSymbolLayer()
        marker_line_sym_lay.setSubSymbol(self.marker_sym)  # Causes crash !!!
        marker_line_sym_lay.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)

        symbol.appendSymbolLayer(marker_line_sym_lay)

        renderer = QgsSingleSymbolRenderer(symbol)
        return renderer

    def make_flow_sym_renderer(self, layer, field_name, ranges_colors=None):

        feats = layer.getFeatures()

        min_val = sys.float_info.max
        max_val = -min_val

        # Find values range
        for feat in feats:
            attr = feat.attribute(field_name)
            val = float(attr)
            if val < min_val:
                min_val = val
            if val > max_val:
                max_val = val

        # Define colors
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
            range_list.append(symbology_from_range(layer, r_min, r_max, range_col[1], title))

        renderer = QgsGraduatedSymbolRenderer(field_name, range_list)

        # Line
        symbol = QgsLineSymbol().createSimple({})
        symbol.deleteSymbolLayer(0)
        line_sym_lay = QgsSimpleLineSymbolLayer()
        line_sym_lay.setWidth(0.2)
        symbol.appendSymbolLayer(line_sym_lay)

        # Define arrows for flow and velocities
        if u'Link flow' in layer.name() in layer.name():
            self.marker_sym = QgsMarkerSymbol.createSimple({'name': 'triangle', 'color': 'black'})
            data_def_angle = QgsProperty()
            data_def_angle_exp =\
                'case ' \
                    'when  "' + field_name + '"  >= 0 ' \
                        'then degrees(azimuth( start_point( $geometry), end_point($geometry))) ' \
                    'else ' \
                        'case ' \
                            'when degrees(azimuth( start_point( $geometry), end_point($geometry)))  < 180 ' \
                                'then degrees(azimuth( start_point( $geometry), end_point($geometry))) + 180 ' \
                            'else ' \
                                'degrees(azimuth( start_point( $geometry), end_point($geometry))) - 180 ' \
                        'end ' \
                'end'
            data_def_angle.setExpressionString(data_def_angle_exp)
            data_def_angle.setActive(True)
            self.marker_sym.setDataDefinedAngle(data_def_angle)

            # Size: 0 if attribute = 0
            data_def_size = QgsProperty()
            data_def_size_exp =\
                'case ' \
                    'when "' + field_name + '" = 0 ' \
                        'then 0 ' \
                    'else ' \
                        '2 ' \
                'end'
            data_def_size.setExpressionString(data_def_size_exp)
            data_def_size.setActive(True)
            self.marker_sym.setDataDefinedSize(data_def_size)


            marker_sym_lay = QgsMarkerLineSymbolLayer()
            marker_sym_lay.setColor(QColor(0, 0, 0))
            marker_sym_lay.setFillColor(QColor(0, 0, 0))
            marker_sym_lay.setPlacement(QgsMarkerLineSymbolLayer.CentralPoint)
            marker_sym_lay.setRotateMarker(False)
            marker_sym_lay.setSubSymbol(self.marker_sym)

            self.marker_sym.appendSymbolLayer(marker_sym_lay)

            symbol.appendSymbolLayer(marker_sym_lay)

        # renderer.setSourceSymbol(symbol)
        renderer.updateSymbols(symbol)

        return renderer


def symbology_from_range(layer, min_val, max_val, color, title):
    symbol = get_default_symbol(layer.geometryType())
    symbol.setColor(color)
    srange = QgsRendererRange(min_val, max_val, symbol, title)
    return srange


def get_default_symbol( geom_type):
    symbol = QgsSymbol.defaultSymbol(geom_type)
    if symbol is None:
        if geom_type == Qgis.Point:
            symbol = QgsMarkerSymbol()
        elif geom_type == Qgis.Line:
            symbol = QgsLineSymbol()
        elif geom_type == Qgis.Polygon:
            symbol = QgsFillSymbol()
    return symbol


def refresh_layer(map_canvas, layer):

    map_canvas.refresh()
