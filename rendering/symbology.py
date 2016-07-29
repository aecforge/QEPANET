from ..tools.parameters import Parameters
from PyQt4.QtGui import QColor
from qgis.core import QgsSvgMarkerSymbolLayerV2, QgsSymbolV2, QgsSingleSymbolRendererV2, QGis, QgsLineSymbolV2,\
    QgsSimpleLineSymbolLayerV2, QgsMarkerSymbolV2, QgsMarkerLineSymbolLayerV2, QgsSimpleMarkerSymbolLayerV2
import os


class NodeSymbology:
    def __init__(self):
        pass

    def make_simple_node_sym_renderer(self, size=2):

        symbol = QgsMarkerSymbolV2().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Point
        sim_marker_sym_lay = QgsSimpleMarkerSymbolLayerV2()
        sim_marker_sym_lay.setColor(QColor(0, 0, 0))
        sim_marker_sym_lay.setFillColor(QColor(0, 0, 0))
        sim_marker_sym_lay.setSize(size)
        symbol.appendSymbolLayer(sim_marker_sym_lay)

        renderer = QgsSingleSymbolRendererV2(symbol)
        return renderer

    def make_svg_node_sym_renderer(self, vlay, icon_name, size):

        current_dir = os.path.dirname(__file__)

        svg_style = dict()
        svg_style['name'] = os.path.join(current_dir, icon_name)
        svg_style['size'] = str(size)
        symbol_layer = QgsSvgMarkerSymbolLayerV2.create(svg_style)
        symbol = QgsSymbolV2.defaultSymbol(vlay.geometryType())
        symbol.changeSymbolLayer(0, symbol_layer)
        renderer = QgsSingleSymbolRendererV2(symbol)

        return renderer


class LinkSymbology:

    def __init__(self):
        self.marker_sym = None

    def make_simple_link_sym_renderer(self, width=0.2):

        symbol = QgsLineSymbolV2().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Line
        line_sym_lay = QgsSimpleLineSymbolLayerV2()
        line_sym_lay.setWidth(width)
        symbol.appendSymbolLayer(line_sym_lay)

        renderer = QgsSingleSymbolRendererV2(symbol)
        return renderer

    def make_svg_link_sym_renderer(self, icon_name, svg_size=7, line_width=0.2):

        symbol = QgsLineSymbolV2().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Line
        line_sym_lay = QgsSimpleLineSymbolLayerV2()
        line_sym_lay.setWidth(line_width)
        symbol.appendSymbolLayer(line_sym_lay)

        # Symbol
        self.marker_sym = QgsMarkerSymbolV2.createSimple({})
        self.marker_sym.deleteSymbolLayer(0)

        # marker_sym_lay = QgsSimpleMarkerSymbolLayerV2()
        current_dir = os.path.dirname(__file__)
        svg_props = dict()
        svg_props['name'] = os.path.join(current_dir, icon_name)
        svg_props['size'] = str(svg_size)
        marker_sym_lay = QgsSvgMarkerSymbolLayerV2().create(svg_props)
        self.marker_sym.appendSymbolLayer(marker_sym_lay)

        marker_line_sym_lay = QgsMarkerLineSymbolLayerV2()
        marker_line_sym_lay.setSubSymbol(self.marker_sym)  # Causes crash !!!
        marker_line_sym_lay.setPlacement(QgsMarkerLineSymbolLayerV2.CentralPoint)

        symbol.appendSymbolLayer(marker_line_sym_lay)

        renderer = QgsSingleSymbolRendererV2(symbol)
        return renderer


def refresh_layer(map_canvas, layer):
    if map_canvas.isCachingEnabled():
        layer.setCacheImage(None)
    else:
        map_canvas.refresh()
