# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QEpanet
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
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, Qt
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QFileDialog, QApplication
from qgis.core import QgsProject

from tools.parameters import Parameters, ConfigFile
from geo_utils.utils import LayerUtils

# Initialize Qt resources from file resources.py

# Import the code for the DockWidget
from ui.qepanet_dockwidget import QEpanetDockWidget, MyQFileDialog
import os.path
import resources


class QEpanet:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        self.params = Parameters()

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'QEpanet_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&QEPANET')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'QEpanet')
        self.toolbar.setObjectName(u'QEpanet')

        #print "** INITIALIZING QEpanet"

        self.pluginIsActive = False
        self.dockwidget = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('QEpanet', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/QEpanet/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'QEPANET'),
            callback=self.run,
            parent=self.iface.mainWindow())

    #--------------------------------------------------------------------------

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin dockwidget is closed"""

        #print "** CLOSING QEpanet"

        # disconnects
        self.dockwidget.closingPlugin.disconnect(self.onClosePlugin)

        # remove this statement if dockwidget is to remain
        # for reuse if plugin is reopened
        # Commented next statement since it causes QGIS crashe
        # when closing the docked window:
        # self.dockwidget = None

        self.pluginIsActive = False


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        #print "** UNLOAD QEpanet"

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&QEPANET'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    # --------------------------------------------------------------------------

    def run(self):
        """Run method that loads and starts the plugin"""

        # Restore cursor
        QApplication.setOverrideCursor(Qt.ArrowCursor)

        # Check for config file existance
        if not os.path.exists(Parameters.config_file_path):
            QMessageBox.critical(
                self.iface.mainWindow(),
                Parameters.plug_in_name,
                u'The config.ini file was not found. It should be located inside the plugin directory. Please refer to'
                u'the plugin documentation to solve the problem.',
                QMessageBox.Ok)

            return

        config_file = ConfigFile(Parameters.config_file_path)

        # # Read patterns
        # patterns_file_path = config_file.get_patterns_file_path()
        # self.params.patterns_file = patterns_file_path
        # if patterns_file_path is not None and os.path.isfile(patterns_file_path):
        #     InpFile.read_patterns(self.params)
        #
        # # Read curves
        # curves_file_path = config_file.get_curves_file_path()
        # self.params.curves_file = curves_file_path
        # if curves_file_path is not None and os.path.isfile(curves_file_path):
        #     InpFile.read_curves(self.params)

        file_dialog = MyQFileDialog()
        file_dialog.setWindowTitle('Select an INP file or create a new one')  # TODO: Softcode
        file_dialog.setLabelText(QFileDialog.Accept, 'Select')  # TODO: sofcode
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setFilter("INP files (*.inp)")

        inp_file_path = None
        if file_dialog.exec_():
            inp_file_path = file_dialog.selectedFiles()[0]
            if not inp_file_path.lower().endswith('.inp'):
                inp_file_path += '.inp'

            self.params.last_project_dir = os.path.dirname(inp_file_path)

        if inp_file_path is None:
            return

        if not self.pluginIsActive:
            self.pluginIsActive = True

        if self.dockwidget is None:
            # Create the dockwidget (after translation) and keep reference
            self.dockwidget = QEpanetDockWidget(self.iface, self.params, inp_file_path)
            self.params.attach(self.dockwidget)

            # Connect to provide cleanup on closing of dockwidget
            self.dockwidget.closingPlugin.connect(self.onClosePlugin)

            # Show the dockwidget
            self.iface.addDockWidget(Qt.RightDockWidgetArea, self.dockwidget)

        self.dockwidget.show()