from ..tools.parameters import Parameters
from PyQt4.QtGui import QColor
from qgis.core import QgsSvgMarkerSymbolLayerV2, QgsSymbolV2, QgsSingleSymbolRendererV2, QGis, QgsLineSymbolV2,\
    QgsSimpleLineSymbolLayerV2, QgsMarkerSymbolV2, QgsMarkerLineSymbolLayerV2, QgsSimpleMarkerSymbolLayerV2
import os


def make_node_sym_renderer(icon_name, size):

    current_dir = os.path.dirname(__file__)

    svg_style = dict()
    svg_style['name'] = os.path.join(current_dir, icon_name)
    svg_style['size'] = str(size)
    symbol_layer = QgsSvgMarkerSymbolLayerV2.create(svg_style)
    symbol = QgsSymbolV2.defaultSymbol(Parameters.reservoirs_vlay.geometryType())
    symbol.changeSymbolLayer(0, symbol_layer)
    renderer = QgsSingleSymbolRendererV2(symbol)

    return renderer


class LinkSymbology:

    def __init__(self):
        self.marker_sym = None

    def make_link_sym_renderer(self, icon_name, size):

        symbol = QgsLineSymbolV2().createSimple({})
        symbol.deleteSymbolLayer(0)

        # Line
        line_sym_lay = QgsSimpleLineSymbolLayerV2()
        symbol.appendSymbolLayer(line_sym_lay)

        # Symbol
        self.marker_sym = QgsMarkerSymbolV2.createSimple({})
        self.marker_sym.deleteSymbolLayer(0)

        # marker_sym_lay = QgsSimpleMarkerSymbolLayerV2()
        current_dir = os.path.dirname(__file__)
        svg_props = dict()
        svg_props['name'] = os.path.join(current_dir, icon_name)
        svg_props['size'] = str(size)
        marker_sym_lay = QgsSvgMarkerSymbolLayerV2().create(svg_props)
        self.marker_sym.appendSymbolLayer(marker_sym_lay)

        marker_line_sym_lay = QgsMarkerLineSymbolLayerV2()
        marker_line_sym_lay.setSubSymbol(self.marker_sym)  # Causes crash !!!
        marker_line_sym_lay.setPlacement(QgsMarkerLineSymbolLayerV2.CentralPoint)

        symbol.appendSymbolLayer(marker_line_sym_lay)

        # # SVG
        # current_dir = os.path.dirname(__file__)
        # svg_style = dict()
        # svg_style['name'] = os.path.join(current_dir, icon_name)
        # svg_style['size'] = str(size)
        # svg_marker_sym_lay = QgsSvgMarkerSymbolLayerV2.create(svg_style)
        #
        # marker_sym_lay = QgsMarkerLineSymbolLayerV2.create()
        #
        # qmsv2 = QgsMarkerSymbolV2([marker_sym_lay])
        #
        # marker_sym_lay.setSubSymbol(qmsv2) # PURE FUNCTION CALL
        #
        # marker_sym_lay.setPlacement(QgsMarkerLineSymbolLayerV2.CentralPoint)
        # marker_sym_lay.setColor(QColor(0, 255, 0))
        #
        # symbol.appendSymbolLayer(marker_sym_lay)
        #
        # # Line
        # line_sym_lay = QgsSimpleLineSymbolLayerV2()
        # line_sym_lay.setWidth(0.2)
        # line_sym_lay.setColor(QColor(0, 255, 255))
        # symbol.appendSymbolLayer(line_sym_lay)

        renderer = QgsSingleSymbolRendererV2(symbol)

        return renderer

