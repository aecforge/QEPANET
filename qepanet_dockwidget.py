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

        QgsMapLayerRegistry.instance().layersAdded.connect(self.update_dem_combo)
        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.update_dem_combo)
        QgsMapLayerRegistry.instance().layerRemoved.connect(self.update_dem_combo)

        self.update_dem_combo()
        if self.cbo_dem.count() > 0:
            layer_id = self.cbo_dem.itemData(0)
            parameters.Parameters.selected_dem_lay = utils.LayerUtils.get_lay_from_id(layer_id)

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
        parameters.Parameters.selected_dem_lay = utils.LayerUtils.get_lay_from_id(layer_id)

    def update_dem_combo(self):
        self.cbo_dem.clear()
        layers = self.iface.legendInterface().layers()
        raster_count = 0
        for layer in layers:
            if layer is not None:
                if QgsMapLayer is not None:
                    if layer.type() == QgsMapLayer.RasterLayer:
                        raster_count += 1
                        self.cbo_dem.addItem(layer.name(), layer.id())

        if self.cbo_dem.count() == 0:
            parameters.Parameters.selected_dem_lay = None