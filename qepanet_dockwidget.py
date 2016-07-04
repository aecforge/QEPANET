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
from PyQt4 import QtCore

from PyQt4 import QtGui, uic
from PyQt4.QtCore import pyqtSignal

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

        QtCore.QObject.connect(self.btn_add_node, QtCore.SIGNAL("pressed()"), self.add_tool)
        QtCore.QObject.connect(self.btn_move_node, QtCore.SIGNAL("pressed()"), self.move_tool)

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def add_tool(self):
        tool = AddNodeTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)

    def move_tool(self):
        tool = MoveNodeTool(self, self.iface)
        self.iface.mapCanvas().setMapTool(tool)