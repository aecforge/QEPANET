# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEpanetDockWidget
                                 A QGIS plugin
 This plugin links QGIS and EPANET.
                             -------------------
        begin                : 2016-07-04
        git sha              : $Format:%H$
        copyright            : (C) 2016 by DICAM - UNITN
        email                : albertodeluca3@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
from tools.add_node_tool import AddNodeTool
from tools.move_node_tool import MoveNodeTool

from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import pyqtSignal

from qgis.core import QgsMapLayer, QgsMapLayerRegistry

import parameters
from geo_utils import utils
from parameters import Parameters

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qepanet_dockwidget_base.ui'))


class QEpanetDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface):
        """Constructor."""
        super(QEpanetDockWidget, self).__init__(iface.mainWindow())
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface

        QtCore.QObject.connect(self.btn_add_node, QtCore.SIGNAL('pressed()'), self.add_node)
        QtCore.QObject.connect(self.btn_move_node, QtCore.SIGNAL('pressed()'), self.move_node)

        QtCore.QObject.connect(self.cbo_dem, QtCore.SIGNAL('activated(int)'), self.cbo_dem_activated)

        # QgsMapLayerRegistry.instance().layersAdded.connect(self.update_layers_combos)
        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.update_layers_combos)
        QgsMapLayerRegistry.instance().layerRemoved.connect(self.update_layers_combos)

        self.update_layers_combos()

        if self.cbo_nodes.count() >= 0:
            layer_id = self.cbo_nodes.itemData(0)
            Parameters.nodes_vlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_pipes.count() >= 0:
            layer_id = self.cbo_pipes.itemData(0)
            Parameters.pipes_rlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_pumps.count() >= 0:
            layer_id = self.cbo_pumps.itemData(0)
            Parameters.pumps_rlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_reservoirs.count() >= 0:
            layer_id = self.cbo_reservoirs.itemData(0)
            Parameters.reservoirs_rlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_sources.count() >= 0:
            layer_id = self.cbo_sources.itemData(0)
            Parameters.sources_rlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_valves.count() >= 0:
            layer_id = self.cbo_valves.itemData(0)
            Parameters.valves_rlay = utils.LayerUtils.get_lay_from_id(layer_id)

        if self.cbo_dem.count() >= 0:
            layer_id = self.cbo_dem.itemData(0)
            Parameters.dem_rlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def add_node(self):
        tool = AddNodeTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)

    def move_node(self):
        tool = MoveNodeTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)

    def cbo_dem_activated(self, index):
        layer_id = self.cbo_dem.itemData(index)
        Parameters.dem_rlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def update_layers_combos(self):

        nodes_lay_id = self.cbo_nodes.itemData(self.cbo_nodes.currentIndex())
        pipes_lay_id = self.cbo_pipes.itemData(self.cbo_pipes.currentIndex())
        pumps_lay_id = self.cbo_pumps.itemData(self.cbo_pumps.currentIndex())
        reservoirs_lay_id = self.cbo_reservoirs.itemData(self.cbo_reservoirs.currentIndex())
        sources_lay_id = self.cbo_sources.itemData(self.cbo_sources.currentIndex())
        valves_lay_id = self.cbo_valves.itemData(self.cbo_valves.currentIndex())

        dem_lay_id = self.cbo_dem.itemData(0)

        self.cbo_nodes.clear()
        self.cbo_pipes.clear()
        self.cbo_pumps.clear()
        self.cbo_reservoirs.clear()
        self.cbo_sources.clear()
        self.cbo_valves.clear()

        self.cbo_dem.clear()

        layers = self.iface.legendInterface().layers()
        raster_count = 0
        for layer in layers:
            if layer is not None:
                if QgsMapLayer is not None:
                    if layer.type() == QgsMapLayer.RasterLayer:
                        raster_count += 1
                        self.cbo_dem.addItem(layer.name(), layer.id())
                    else:
                        self.cbo_nodes.addItem(layer.name(), layer.id())
                        self.cbo_pipes.addItem(layer.name(), layer.id())
                        self.cbo_pumps.addItem(layer.name(), layer.id())
                        self.cbo_reservoirs.addItem(layer.name(), layer.id())
                        self.cbo_sources.addItem(layer.name(), layer.id())
                        self.cbo_valves.addItem(layer.name(), layer.id())

        if self.cbo_nodes.count() == 0:
            parameters.Parameters.nodes_vlay = None
        if self.cbo_pipes.count() == 0:
            Parameters.pipes_vlay = None
        if self.cbo_pumps.count() == 0:
            Parameters.pumps_vlay = None
        if self.cbo_reservoirs.count() == 0:
            Parameters.reservoirs_vlay = None
        if self.cbo_sources.count() == 0:
            Parameters.sources_vlay = None
        if self.cbo_valves.count() == 0:
            Parameters.valves_vlay = None

        if self.cbo_dem.count() == 0:
            parameters.Parameters.dem_rlay = None

        # Reset combo selections
        self.set_combo_index(self.cbo_nodes, nodes_lay_id)
        self.set_combo_index(self.cbo_pipes, pipes_lay_id)
        self.set_combo_index(self.cbo_pumps, pumps_lay_id)
        self.set_combo_index(self.cbo_reservoirs, reservoirs_lay_id)
        self.set_combo_index(self.cbo_sources, sources_lay_id)
        self.set_combo_index(self.cbo_valves, valves_lay_id)

        self.set_combo_index(self.cbo_dem, dem_lay_id)

    def set_combo_index(self, combo, layer_id):
        index = combo.findData(layer_id)
        if index >= 0:
            combo.setCurrentIndex(index)