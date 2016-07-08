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
from tools.add_junction_tool import AddJunctionTool
from tools.add_pipe_tool import AddPipeTool
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

        # Buttons, set checkable
        self.btn_add_junction.setCheckable(True)
        self.btn_add_reservoir.setCheckable(True)
        self.btn_add_tank.setCheckable(True)
        self.btn_add_pipe.setCheckable(True)
        self.btn_add_pump.setCheckable(True)
        self.btn_add_valve.setCheckable(True)

        self.btn_move_node.setCheckable(True)
        self.btn_move_link.setCheckable(True)

        # Buttons, set actions
        QtCore.QObject.connect(self.btn_add_junction, QtCore.SIGNAL('pressed()'), self.add_junction)
        QtCore.QObject.connect(self.btn_add_reservoir, QtCore.SIGNAL('pressed()'), self.add_reservoir)
        QtCore.QObject.connect(self.btn_add_tank, QtCore.SIGNAL('pressed()'), self.add_tank)

        QtCore.QObject.connect(self.btn_add_pipe, QtCore.SIGNAL('pressed()'), self.add_pipe)
        QtCore.QObject.connect(self.btn_add_pump, QtCore.SIGNAL('pressed()'), self.add_pump)
        QtCore.QObject.connect(self.btn_add_valve, QtCore.SIGNAL('pressed()'), self.add_valve)

        QtCore.QObject.connect(self.btn_move_node, QtCore.SIGNAL('pressed()'), self.move_node)
        QtCore.QObject.connect(self.btn_move_link, QtCore.SIGNAL('pressed()'), self.move_link)

        # Combo boxes
        QtCore.QObject.connect(self.cbo_junctions, QtCore.SIGNAL('activated(int)'), self.cbo_junctions_activated)
        QtCore.QObject.connect(self.cbo_reservoirs, QtCore.SIGNAL('activated(int)'), self.cbo_reservoirs_activated)
        QtCore.QObject.connect(self.cbo_tanks, QtCore.SIGNAL('activated(int)'), self.cbo_tanks_activated)

        QtCore.QObject.connect(self.cbo_pipes, QtCore.SIGNAL('activated(int)'), self.cbo_pipes_activated)
        QtCore.QObject.connect(self.cbo_pumps, QtCore.SIGNAL('activated(int)'), self.cbo_pumps_activated)
        QtCore.QObject.connect(self.cbo_valves, QtCore.SIGNAL('activated(int)'), self.cbo_valves_activated)

        QtCore.QObject.connect(self.cbo_dem, QtCore.SIGNAL('activated(int)'), self.cbo_dem_activated)

        # QgsMapLayerRegistry.instance().layersAdded.connect(self.update_layers_combos)
        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.update_layers_combos)
        QgsMapLayerRegistry.instance().layerRemoved.connect(self.update_layers_combos)

        self.update_layers_combos()
        self.update_patterns_combo()

        if self.cbo_junctions.count() >= 0:
            layer_id = self.cbo_junctions.itemData(self.cbo_junctions.currentIndex())
            Parameters.junctions_vlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_pipes.count() >= 0:
            layer_id = self.cbo_pipes.itemData(self.cbo_pipes.currentIndex())
            Parameters.pipes_vlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_pumps.count() >= 0:
            layer_id = self.cbo_pumps.itemData(self.cbo_pumps.currentIndex())
            Parameters.pumps_vlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_reservoirs.count() >= 0:
            layer_id = self.cbo_reservoirs.itemData(self.cbo_reservoirs.currentIndex())
            Parameters.reservoirs_vlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_tanks.count() >= 0:
            layer_id = self.cbo_tanks.itemData(self.cbo_tanks.currentIndex())
            Parameters.tanks_vlay = utils.LayerUtils.get_lay_from_id(layer_id)
        if self.cbo_valves.count() >= 0:
            layer_id = self.cbo_valves.itemData(self.cbo_valves.currentIndex())
            Parameters.valves_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

        if self.cbo_dem.count() >= 0:
            layer_id = self.cbo_dem.itemData(0)
            Parameters.dem_rlay = utils.LayerUtils.get_lay_from_id(layer_id)



    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def add_junction(self):
        tool = AddJunctionTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)

        # Cursor
        cursor = QtGui.QCursor()
        cursor.setShape(QtCore.Qt.CrossCursor)
        self.iface.mapCanvas().setCursor(cursor)

    def add_pipe(self):
        tool = AddPipeTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)

        # Cursor
        cursor = QtGui.QCursor()
        cursor.setShape(QtCore.Qt.CrossCursor)
        self.iface.mapCanvas().setCursor(cursor)

    def add_reservoir(self):
        pass

    def add_tank(self):
        pass

    def add_pump(self):
        pass

    def add_valve(self):
        pass

    def move_node(self):
        tool = MoveNodeTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)

        # Cursor
        cursor = QtGui.QCursor()
        cursor.setShape(QtCore.Qt.CrossCursor)
        self.iface.mapCanvas().setCursor(cursor)

    def move_link(self):
        pass

    # TODO: update snappers in all the tools that use snapping
    def cbo_junctions_activated(self, index):
        layer_id = self.cbo_junctions.itemData(index)
        Parameters.junctions_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_reservoirs_activated(self, index):
        layer_id = self.cbo_reservoirs.itemData(index)
        Parameters.reservoirs_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_tanks_activated(self, index):
        layer_id = self.cbo_tanks.itemData(index)
        Parameters.tanks_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_pipes_activated(self, index):
        layer_id = self.cbo_pipes.itemData(index)
        Parameters.pipes_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_pumps_activated(self, index):
        layer_id = self.cbo_pumps.itemData(index)
        Parameters.pumps_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_valves_activated(self, index):
        layer_id = self.cbo_valves.itemData(index)
        Parameters.valves_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_dem_activated(self, index):
        layer_id = self.cbo_dem.itemData(index)
        Parameters.dem_rlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def update_layers_combos(self):

        nodes_lay_id = self.cbo_junctions.itemData(self.cbo_junctions.currentIndex())
        pipes_lay_id = self.cbo_pipes.itemData(self.cbo_pipes.currentIndex())
        pumps_lay_id = self.cbo_pumps.itemData(self.cbo_pumps.currentIndex())
        reservoirs_lay_id = self.cbo_reservoirs.itemData(self.cbo_reservoirs.currentIndex())
        tanks_lay_id = self.cbo_tanks.itemData(self.cbo_tanks.currentIndex())
        valves_lay_id = self.cbo_valves.itemData(self.cbo_valves.currentIndex())

        dem_lay_id = self.cbo_dem.itemData(0)

        self.cbo_junctions.clear()
        self.cbo_pipes.clear()
        self.cbo_pumps.clear()
        self.cbo_reservoirs.clear()
        self.cbo_tanks.clear()
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
                        self.cbo_junctions.addItem(layer.name(), layer.id())
                        self.cbo_pipes.addItem(layer.name(), layer.id())
                        self.cbo_pumps.addItem(layer.name(), layer.id())
                        self.cbo_reservoirs.addItem(layer.name(), layer.id())
                        self.cbo_tanks.addItem(layer.name(), layer.id())
                        self.cbo_valves.addItem(layer.name(), layer.id())

        if self.cbo_junctions.count() == 0:
            Parameters.junctions_vlay = None
        if self.cbo_pipes.count() == 0:
            Parameters.pipes_vlay = None
        if self.cbo_pumps.count() == 0:
            Parameters.pumps_vlay = None
        if self.cbo_reservoirs.count() == 0:
            Parameters.reservoirs_vlay = None
        if self.cbo_tanks.count() == 0:
            Parameters.tanks_vlay = None
        if self.cbo_valves.count() == 0:
            Parameters.valves_vlay = None

        if self.cbo_dem.count() == 0:
            Parameters.dem_rlay = None

        # Reset combo selections
        self.set_combo_index(self.cbo_junctions, nodes_lay_id)
        self.set_combo_index(self.cbo_pipes, pipes_lay_id)
        self.set_combo_index(self.cbo_pumps, pumps_lay_id)
        self.set_combo_index(self.cbo_reservoirs, reservoirs_lay_id)
        self.set_combo_index(self.cbo_tanks, tanks_lay_id)
        self.set_combo_index(self.cbo_valves, valves_lay_id)

        self.set_combo_index(self.cbo_dem, dem_lay_id)

    def update_patterns_combo(self):
        self.cbo_node_pattern.clear()
        for value in Parameters.patterns['names'].itervalues():
            self.cbo_node_pattern.addItem(value)

    def set_combo_index(self, combo, layer_id):
        index = combo.findData(layer_id)
        if index >= 0:
            combo.setCurrentIndex(index)