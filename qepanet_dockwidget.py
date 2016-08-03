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

from PyQt4 import QtCore, uic, QtGui
from PyQt4.QtCore import pyqtSignal
from PyQt4.QtGui import QFileDialog, QMessageBox
from qgis.core import QgsMapLayer, QgsMapLayerRegistry, QgsCoordinateReferenceSystem,\
    QgsProject, QgsSnapper, QgsTolerance

from geo_utils import utils
from ui.patterns_gui import PatternsDialog
from model.network import Tables, Pump, Valve
from rendering import symbology
from tools.add_junction_tool import AddJunctionTool
from tools.add_pipe_tool import AddPipeTool
from tools.add_pump_tool import AddPumpTool
from tools.add_reservoir_tool import AddReservoirTool
from tools.add_tank_tool import AddTankTool
from tools.add_valve_tool import AddValveTool
from tools.move_tool import MoveTool
from tools.data_stores import ShapefileDS
from tools.exceptions import ShpExistsExcpetion
from tools.delete_tool import DeleteTool
from tools.parameters import Parameters, RegExValidators, ConfigFile
from ui import misc

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qepanet_dockwidget.ui'))


class QEpanetDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, parameters):
        """Constructor."""
        super(QEpanetDockWidget, self).__init__(iface.mainWindow())
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.parameters = parameters
        self.parameters.attach(self)

        self.setupUi(self)
        self.setWindowTitle(parameters.plug_in_name)

        self.decimals = 1

        self.tool = None

        # Tools buttons
        self.btn_add_junction.setCheckable(True)
        self.btn_add_reservoir.setCheckable(True)
        self.btn_add_tank.setCheckable(True)
        self.btn_add_pipe.setCheckable(True)
        self.btn_add_pump.setCheckable(True)
        self.btn_add_valve.setCheckable(True)

        self.btn_move_element.setCheckable(True)
        self.btn_delete_element.setCheckable(True)

        QtCore.QObject.connect(self.btn_add_junction, QtCore.SIGNAL('pressed()'), self.add_junction)
        QtCore.QObject.connect(self.btn_add_reservoir, QtCore.SIGNAL('pressed()'), self.add_reservoir)
        QtCore.QObject.connect(self.btn_add_tank, QtCore.SIGNAL('pressed()'), self.add_tank)

        QtCore.QObject.connect(self.btn_add_pipe, QtCore.SIGNAL('pressed()'), self.add_pipe)
        QtCore.QObject.connect(self.btn_add_pump, QtCore.SIGNAL('pressed()'), self.add_pump)
        QtCore.QObject.connect(self.btn_add_valve, QtCore.SIGNAL('pressed()'), self.add_valve)

        QtCore.QObject.connect(self.btn_move_element, QtCore.SIGNAL('pressed()'), self.move_element)
        QtCore.QObject.connect(self.btn_delete_element, QtCore.SIGNAL('pressed()'), self.delete_element)

        # Layers
        QtCore.QObject.connect(self.cbo_junctions, QtCore.SIGNAL('activated(int)'), self.cbo_junctions_activated)
        QtCore.QObject.connect(self.cbo_reservoirs, QtCore.SIGNAL('activated(int)'), self.cbo_reservoirs_activated)
        QtCore.QObject.connect(self.cbo_tanks, QtCore.SIGNAL('activated(int)'), self.cbo_tanks_activated)
        QtCore.QObject.connect(self.cbo_pipes, QtCore.SIGNAL('activated(int)'), self.cbo_pipes_activated)
        QtCore.QObject.connect(self.cbo_pumps, QtCore.SIGNAL('activated(int)'), self.cbo_pumps_activated)
        QtCore.QObject.connect(self.cbo_valves, QtCore.SIGNAL('activated(int)'), self.cbo_valves_activated)
        QtCore.QObject.connect(self.cbo_dem, QtCore.SIGNAL('activated(int)'), self.cbo_dem_activated)

        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.update_layers_combos)
        QgsMapLayerRegistry.instance().layerRemoved.connect(self.update_layers_combos)
        self.update_layers_combos()
        self.preselect_layers_combos()

        QtCore.QObject.connect(self.btn_symbology, QtCore.SIGNAL('pressed()'), self.apply_symbologies)

        # Junctions
        self.txt_node_demand.setValidator(RegExValidators.get_pos_decimals())
        self.txt_node_depth.setValidator(RegExValidators.get_pos_decimals())

        self.update_patterns_combo()

        # Reservoirs
        self.txt_reservoir_head.setValidator(RegExValidators.get_pos_decimals())
        self.txt_reservoir_elev_corr.setValidator(RegExValidators.get_pos_neg_decimals())

        self.update_curves_combo()

        # Tanks
        # -

        # Pipes
        self.txt_pipe_demand.setValidator(RegExValidators.get_pos_decimals())
        self.txt_pipe_diameter.setValidator(RegExValidators.get_pos_decimals())
        self.txt_pipe_loss.setValidator(RegExValidators.get_pos_decimals())

        self.cbo_pipe_roughness.clear()
        self.cbo_pipe_roughness.addItem('Asphalted cast iron', ['0.015', '0.04']) # TODO: put everything in txt file
        self.cbo_pipe_roughness.addItem('Cast iron', ['0.03', '0.06'])
        self.cbo_pipe_roughness.addItem('Commercial steel', ['0.05', '0.15'])
        self.cbo_pipe_roughness.addItem('Concrete', ['0.3', '3'])
        self.cbo_pipe_roughness.addItem('Galvanized iron', ['0.015', '0.03'])
        self.cbo_pipe_roughness.addItem('PVC, glass, drawn', ['0', '0.02'])
        self.update_roughness_params(self.cbo_pipe_roughness.itemData(self.cbo_pipe_roughness.currentIndex()))
        QtCore.QObject.connect(self.cbo_pipe_roughness, QtCore.SIGNAL('activated(int)'), self.cbo_pipe_roughness_activated)

        self.sli_pipe_roughness.valueChanged.connect(self.roughness_slider_changed)

        self.cbo_pipe_status.clear()
        self.cbo_pipe_status.addItem('Open')  # TODO: softcode
        self.cbo_pipe_status.addItem('Closed')  # TODO: softcode
        self.cbo_pipe_status.addItem('CV')  # TODO: sofcode

        # Pumps
        self.cbo_pump_param.addItem(Pump.parameters_head)
        self.cbo_pump_param.addItem(Pump.parameters_power)
        self.txt_pump_power.setValidator(RegExValidators.get_pos_decimals())

        QtCore.QObject.connect(self.cbo_pump_param, QtCore.SIGNAL('activated(int)'), self.cbo_pump_param_activated)

        # Valves
        self.cbo_valve_type.clear()
        for key, value in Valve.types.iteritems():
            self.cbo_valve_type.addItem(value, key)

        QtCore.QObject.connect(self.cbo_valve_type, QtCore.SIGNAL('activated(int)'), self.cbo_valve_type_activated)

        # Other tools
        QtCore.QObject.connect(self.btn_create_layers, QtCore.SIGNAL('pressed()'), self.create_layers)

        self.txt_snap_tolerance.setText(str(parameters.snap_tolerance))
        self.txt_snap_tolerance.setValidator(RegExValidators.get_pos_decimals())
        QtCore.QObject.connect(self.txt_snap_tolerance, QtCore.SIGNAL('editingFinished()'), self.snap_tolerance_changed)

        QtCore.QObject.connect(self.btn_pattern_editor, QtCore.SIGNAL('pressed()'), self.pattern_editor)

        # TODO: read parameters from parameters file and set previous GUI settings

    # This method needed by observable
    def update(self, observable):
        # Update components
        self.update_patterns_combo()
        self.update_curves_combo()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def add_junction(self):

        if type(self.iface.mapCanvas().mapTool()) is AddJunctionTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_add_junction.setChecked(True)

        else:
            # Check for junctions and pipes layers selected
            if self.cbo_junctions.count() == 0 or self.cbo_pipes.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte the junctions and pipes layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_add_junction.setChecked(True)
                return

            self.tool = AddJunctionTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def add_reservoir(self):

        if type(self.iface.mapCanvas().mapTool()) is AddReservoirTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_add_reservoir.setChecked(True)

        else:
            # Check for reservoirs and pipes layers selected
            if self.cbo_reservoirs.count() == 0 or self.cbo_pipes.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte the reservoirs and pipes layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_add_reservoir.setChecked(True)
                return

            self.tool = AddReservoirTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def add_tank(self):

        if type(self.iface.mapCanvas().mapTool()) is AddTankTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_add_tank.setChecked(False)

        else:
            # Check for tanks and pipes layers selected
            if self.cbo_tanks.count() == 0 or self.cbo_pipes.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte the tanks and pipes layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_add_tank.setChecked(True)
                return

            tool = AddTankTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def add_pipe(self):

        if type(self.iface.mapCanvas().mapTool()) is AddPipeTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_add_pipe.setChecked(True)

        else:
            # Check for junctions and pipes layers selected
            if self.cbo_junctions.count() == 0 or self.cbo_pipes.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte the junctions and pipes layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_add_pipe.setChecked(True)
                return

            self.tool = AddPipeTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def add_pump(self):

        if type(self.iface.mapCanvas().mapTool()) is AddPumpTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_add_pump.setChecked(True)

        else:

            # Check for junctions, pipes and pumps layers selected
            if self.cbo_junctions.count() == 0 or self.cbo_pipes.count() == 0 or self.cbo_pumps.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte the junctions, pipes and pumps layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_add_pump.setChecked(True)
                return

            self.tool = AddPumpTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def add_valve(self):

        if type(self.iface.mapCanvas().mapTool()) is AddValveTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_add_valve.setChecked(True)

        else:

            # Check for junctions, pipes and valves layers selected
            if self.cbo_junctions.count() == 0 or self.cbo_pipes.count() == 0 or self.cbo_valves.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte the junctions, pipes and valves layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_add_valve.setChecked(True)
                return

            self.tool = AddValveTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def move_element(self):

        if type(self.iface.mapCanvas().mapTool()) is MoveTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_move_element.setChecked(True)

        else:

            # Check for all layers selected
            if self.cbo_junctions.count() == 0 or self.cbo_reservoirs.count() == 0 or self.cbo_tanks.count() == 0 or\
                    self.cbo_pipes.count() == 0 or self.cbo_pumps.count() == 0 or self.cbo_valves.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte all the vector layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_move_element.setChecked(True)
                return

            self.tool = MoveTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def delete_element(self):

        if type(self.iface.mapCanvas().mapTool()) is DeleteTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.btn_delete_element.setChecked(True)

        else:

            # Check for all layers selected
            if self.cbo_junctions.count() == 0 or self.cbo_reservoirs.count() == 0 or self.cbo_tanks.count() == 0 or\
                    self.cbo_pipes.count() == 0 or self.cbo_pumps.count() == 0 or self.cbo_valves.count() == 0:
                self.iface.messageBar().pushWarning(
                    Parameters.plug_in_name,
                    'Please selecte all the vector layers inside the Layers section of the plugin\'s dock panel.')  # TODO: softcode)
                self.btn_delete_element.setChecked(True)
                return

            self.tool = DeleteTool(self, self.parameters)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def cbo_pump_param_activated(self):
        selected_param = self.cbo_pump_param.itemText(self.cbo_pump_param.currentIndex())
        self.lbl_pump_power.setEnabled(selected_param == Pump.parameters_power)
        self.txt_pump_power.setEnabled(selected_param == Pump.parameters_power)
        self.lbl_pump_head.setEnabled(selected_param == Pump.parameters_head)
        self.cbo_pump_head.setEnabled(selected_param == Pump.parameters_head)

    def cbo_valve_type_activated(self):
        selected_type = self.cbo_valve_type.itemData(self.cbo_valve_type.currentIndex())

        setting_on = True
        setting_label = '-'
        if selected_type == Valve.type_pbv or selected_type == Valve.type_prv or selected_type == Valve.type_psv:
            setting_label = 'Pressure[m]' # TODO: softcode
        elif selected_type == Valve.type_fcv:
            setting_label = 'Flow [???]:' # TODO: softcode
        elif selected_type == Valve.type_tcv:
            setting_label = 'Loss coeff. [-]:' # TODO: softcode
        elif selected_type == Valve.type_gpv:
            setting_on = False

        self.lbl_valve_setting.setEnabled(setting_on)
        self.txt_valve_setting.setEnabled(setting_on)
        self.lbl_valve_curve.setEnabled(not setting_on)
        self.cbo_valve_curve.setEnabled(not setting_on)

        if setting_on:
            self.lbl_valve_setting.setText(setting_label)

    def create_layers(self):

        shp_folder = QFileDialog.getExistingDirectory(
            self.iface.mainWindow(),
            'Select the directory where the Shapefiles will be created')

        if shp_folder is None or shp_folder == '':
            return

        try:
            srid = self.iface.mapCanvas().mapRenderer().destinationCrs().authid()
            srid = int(srid[srid.find(':')+1:])
            ShapefileDS.create_shapefiles(shp_folder, QgsCoordinateReferenceSystem(srid))
        except ShpExistsExcpetion as e:
            self.iface.messageBar().pushInfo(Parameters.plug_in_name, e.message)

        # Load layers in QGIS
        self.parameters.valves_vlay = self.iface.addVectorLayer(os.path.join(shp_folder, Tables.valves_table_name + '.shp'), Tables.valves_table_name, 'ogr')
        self.parameters.pumps_vlay = self.iface.addVectorLayer(os.path.join(shp_folder, Tables.pumps_table_name + '.shp'), Tables.pumps_table_name, 'ogr')
        self.parameters.pipes_vlay = self.iface.addVectorLayer(os.path.join(shp_folder, Tables.pipes_table_name + '.shp'), Tables.pipes_table_name, 'ogr')
        self.parameters.tanks_vlay = self.iface.addVectorLayer(os.path.join(shp_folder, Tables.tanks_table_name + '.shp'), Tables.tanks_table_name, 'ogr')
        self.parameters.reservoirs_vlay = self.iface.addVectorLayer(os.path.join(shp_folder, Tables.reservoirs_table_name + '.shp'), Tables.reservoirs_table_name, 'ogr')
        self.parameters.junctions_vlay = self.iface.addVectorLayer(os.path.join(shp_folder, Tables.junctions_table_name + '.shp'), Tables.junctions_table_name, 'ogr')

        self.update_layers_combos()
        self.preselect_layers_combos()

        self.apply_symbologies()

    def roughness_slider_changed(self):
        self.lbl_pipe_roughness_val_val.setText(str(self.sli_pipe_roughness.value() / float(10**self.decimals)))

    # TODO: update snappers in all the tools that use snapping
    def cbo_junctions_activated(self, index):
        layer_id = self.cbo_junctions.itemData(index)
        self.parameters.junctions_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_reservoirs_activated(self, index):
        layer_id = self.cbo_reservoirs.itemData(index)
        self.parameters.reservoirs_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_tanks_activated(self, index):
        layer_id = self.cbo_tanks.itemData(index)
        self.parameters.tanks_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_pipes_activated(self, index):
        layer_id = self.cbo_pipes.itemData(index)
        self.parameters.pipes_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_pumps_activated(self, index):
        layer_id = self.cbo_pumps.itemData(index)
        self.parameters.pumps_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_valves_activated(self, index):
        layer_id = self.cbo_valves.itemData(index)
        self.parameters.valves_vlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_dem_activated(self, index):
        layer_id = self.cbo_dem.itemData(index)
        self.parameters.dem_rlay = utils.LayerUtils.get_lay_from_id(layer_id)

    def cbo_pipe_roughness_activated(self):
        self.update_roughness_params(self.get_combo_current_data(self.cbo_pipe_roughness))

    def snap_tolerance_changed(self):
        self.parameters.snap_tolerance(float(self.txt_snap_tolerance.text()))

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.junctions_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.reservoirs_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.tanks_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToVertex,
                                                      QgsTolerance.MapUnits,
                                                      self.parameters.snap_tolerance,
                                                      True)

        QgsProject.instance().setSnapSettingsForLayer(self.parameters.pipes_vlay.id(),
                                                      True,
                                                      QgsSnapper.SnapToSegment,
                                                      0,
                                                      self.parameters.snap_tolerance,
                                                      True)

    def pattern_editor(self):

        # Read patterns path
        config_file = ConfigFile(Parameters.config_file_path)
        patterns_file_path = config_file.get_patterns_file_path()
        if patterns_file_path is None or patterns_file_path == '':
            QMessageBox.information(
                self.iface.mainWindow(),
                Parameters.plug_in_name,
                u'Please select the file where the patterns will be saved it in the next dialog.',
                QMessageBox.Ok)

            patterns_file_path = QFileDialog.getOpenFileName(
                self.iface.mainWindow(),
                'Select patterns file',
                None,
                'Patterns files (*.txt *.inp)')

            if patterns_file_path is None or patterns_file_path == '':
                return
            else:
                # Save patterns file path in configuration file
                config_file.set_patterns_file_path(patterns_file_path)

        self.parameters.patterns_file = patterns_file_path

        pattern_dialog = PatternsDialog(self.iface.mainWindow(), self.parameters)
        pattern_dialog.show()

    def update_layers_combos(self):

        prev_nodes_lay_id = self.cbo_junctions.itemData(self.cbo_junctions.currentIndex())
        prev_pipes_lay_id = self.cbo_pipes.itemData(self.cbo_pipes.currentIndex())
        prev_pumps_lay_id = self.cbo_pumps.itemData(self.cbo_pumps.currentIndex())
        prev_reservoirs_lay_id = self.cbo_reservoirs.itemData(self.cbo_reservoirs.currentIndex())
        prev_tanks_lay_id = self.cbo_tanks.itemData(self.cbo_tanks.currentIndex())
        prev_valves_lay_id = self.cbo_valves.itemData(self.cbo_valves.currentIndex())

        prev_dem_lay_id = self.cbo_dem.itemData(self.cbo_dem.currentIndex())

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

        # Reset combo selections
        self.parameters.junctions_vlay = self.set_layercombo_index(self.cbo_junctions, prev_nodes_lay_id)
        self.parameters.reservoirs_vlay = self.set_layercombo_index(self.cbo_reservoirs, prev_reservoirs_lay_id)
        self.parameters.tanks_vlay = self.set_layercombo_index(self.cbo_tanks, prev_tanks_lay_id)
        self.parameters.pipes_vlay = self.set_layercombo_index(self.cbo_pipes, prev_pipes_lay_id)
        self.parameters.pumps_vlay = self.set_layercombo_index(self.cbo_pumps, prev_pumps_lay_id)
        self.parameters.valves_vlay = self.set_layercombo_index(self.cbo_valves, prev_valves_lay_id)

        self.parameters.dem_rlay = self.set_layercombo_index(self.cbo_dem, prev_dem_lay_id)

    def preselect_layers_combos(self):

        for layer_id in QgsMapLayerRegistry.instance().mapLayers():

            layer = utils.LayerUtils.get_lay_from_id(layer_id)

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == Tables.junctions_table_name:
                self.set_layercombo_index(self.cbo_junctions, layer_id)
                self.parameters.junctions_vlay = layer

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == Tables.pipes_table_name:
                self.set_layercombo_index(self.cbo_pipes, layer_id)
                self.parameters.pipes_vlay = layer

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == Tables.pumps_table_name:
                self.set_layercombo_index(self.cbo_pumps, layer_id)
                self.parameters.pumps_vlay = layer

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == Tables.reservoirs_table_name:
                self.set_layercombo_index(self.cbo_reservoirs, layer_id)
                self.parameters.reservoirs_vlay = layer

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == Tables.tanks_table_name:
                self.set_layercombo_index(self.cbo_tanks, layer_id)
                self.parameters.tanks_vlay = layer

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == Tables.valves_table_name:
                self.set_layercombo_index(self.cbo_valves, layer_id)
                self.parameters.valves_vlay = layer

            if utils.LayerUtils.get_lay_from_id(layer_id).name() == 'dem':
                self.set_layercombo_index(self.cbo_dem, layer_id)
                self.parameters.dem_rlay = layer

    def apply_symbologies(self):

        if self.parameters.junctions_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_simple_node_sym_renderer(3)
            self.parameters.junctions_vlay.setRendererV2(renderer)

        if self.parameters.reservoirs_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_svg_node_sym_renderer(self.parameters.reservoirs_vlay, misc.reservoir_icon_svg_name, 7)
            self.parameters.reservoirs_vlay.setRendererV2(renderer)

        if self.parameters.tanks_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_svg_node_sym_renderer(self.parameters.tanks_vlay, misc.tank_icon_svg_name, 7)
            self.parameters.tanks_vlay.setRendererV2(renderer)

        if self.parameters.pipes_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_simple_link_sym_renderer()
            self.parameters.pipes_vlay.setRendererV2(renderer)

        if self.parameters.pumps_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_svg_link_sym_renderer(misc.pump_icon_svg_name, 7)
            self.parameters.pumps_vlay.setRendererV2(renderer)

        if self.parameters.valves_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_svg_link_sym_renderer(misc.valve_icon_svg_name, 7)
            self.parameters.valves_vlay.setRendererV2(renderer)

        symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.junctions_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.reservoirs_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.tanks_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.pipes_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.pumps_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.parameters.valves_vlay)

    def update_patterns_combo(self):
        self.cbo_node_pattern.clear()
        if self.parameters.junctions_vlay is not None:
            for pattern in self.parameters.patterns:
                self.cbo_node_pattern.addItem(pattern.desc, pattern)

    def update_curves_combo(self):
        self.cbo_tank_curve.clear()
        self.cbo_pump_head.clear()
        if self.parameters.curves is not None:
            for value in self.parameters.curves:
                self.cbo_tank_curve.addItem(value.name, value)
                self.cbo_pump_head.addItem(value.name, value)

    def get_combo_current_data(self, combo):
        index = self.cbo_pipe_roughness.currentIndex()
        return combo.itemData(index)

    def set_layercombo_index(self, combo, prev_layer_id):
        index = combo.findData(prev_layer_id)
        if index >= 0:
            combo.setCurrentIndex(index)
            return utils.LayerUtils.get_lay_from_id(self.get_combo_current_data(combo))
        else:
            if combo.count() > 0:
                combo.setCurrentIndex(0)
                return utils.LayerUtils.get_lay_from_id(combo.itemData(0))
            else:
                return None

    def find_decimals(self, float_string):
        float_string.replace(',', '.')
        if '.' in float_string:
            decimals = len(float_string[float_string.index('.'):])
        else:
            decimals = 1
        return decimals

    def update_roughness_params(self, roughness_range):
        self.decimals = max(self.find_decimals(roughness_range[0]), self.find_decimals(roughness_range[1]))

        min_roughness = roughness_range[0]
        max_roughness = roughness_range[1]
        self.lbl_pipe_roughness_min.setText(min_roughness)
        self.lbl_pipe_roughness_max.setText(max_roughness)
        self.lbl_pipe_roughness_val_val.setText(roughness_range[0])

        min_roughness_mult = float(roughness_range[0]) * 10 ** self.decimals
        max_roughness_mult = float(roughness_range[1]) * 10 ** self.decimals
        self.sli_pipe_roughness.setMinimum(min_roughness_mult)
        self.sli_pipe_roughness.setMaximum(max_roughness_mult)
        self.sli_pipe_roughness.setValue(min_roughness_mult)

    def set_cursor(self, cursor_shape):
        cursor = QtGui.QCursor()
        cursor.setShape(cursor_shape)
        self.iface.mapCanvas().setCursor(cursor)