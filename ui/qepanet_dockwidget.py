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
from PyQt4.QtCore import Qt, pyqtSignal
from PyQt4.QtGui import QFileDialog, QMessageBox, QApplication, QPixmap, QLabel, QColor, QToolTip, QCursor
from qgis.gui import QgsGenericProjectionSelector, QgsMessageBar

from ..geo_utils.utils import LayerUtils as lay_utils
from options_dialogs import HydraulicsDialog, QualityDialog, ReactionsDialog, TimesDialog, EnergyDialog, ReportDialog
from output_ui import OutputAnalyserDialog, LogDialog
from ..model.options_report import Options
from curvespatterns_ui import GraphDialog
from ..model.inp_writer import InpFile
from ..model.inp_reader import InpReader
from ..model.network import *
from ..model.network_handling import NetworkUtils
from ..model.network_handling import LinkHandler
from ..model.runner import ModelRunner
from ..model.system_ops import Curve
from ..rendering import symbology
from ..tools.add_junction_tool import AddJunctionTool
from ..tools.add_pipe_tool import AddPipeTool
from ..tools.add_pump_tool import AddPumpTool
from ..tools.add_reservoir_tool import AddReservoirTool
from ..tools.add_tank_tool import AddTankTool
from ..tools.add_valve_tool import AddValveTool
from ..tools.move_tool import MoveTool
from ..tools.data_stores import MemoryDS
from ..tools.exceptions import ShpExistsExcpetion
from ..tools.delete_tool import DeleteTool
from ..tools.parameters import Parameters, RegExValidators, ConfigFile
from tags_dialog import TagsDialog
from utils import prepare_label as pre_l, set_up_button
import misc

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'qepanet_dockwidget.ui'))


class QEpanetDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()

    def __init__(self, iface, params, inp_file_path):
        """Constructor."""
        super(QEpanetDockWidget, self).__init__(iface.mainWindow())
        self.iface = iface
        self.params = params
        self.inp_file_path = inp_file_path
        self.params.attach(self)

        self.setupUi(self)
        self.setWindowTitle(params.plug_in_name)

        self.decimals = 1

        self.tool = None

        # Dialogs
        self.hydraulics_dialog = None
        self.quality_dialog = None
        self.reactions_dialog = None
        self.times_dialog = None
        self.energy_dialog = None
        self.report_dialog = None
        self.output_dialog = None

        self.log_dialog = None

        # Inp file
        self.btn_project_new.clicked.connect(self.project_new_clicked)
        self.btn_project_load.clicked.connect(self.project_load_clicked)
        self.btn_project_save.clicked.connect(self.project_save_clicked)
        self.btn_project_saveas.clicked.connect(self.project_saveas_clicked)

        curr_dir = os.path.dirname(os.path.abspath(__file__))

        # Project buttons
        set_up_button(self.btn_project_new, os.path.join(curr_dir, 'i_new.png',), tooltip_text='New project')
        set_up_button(self.btn_project_load, os.path.join(curr_dir, 'i_load.png'), tooltip_text='Open project')
        set_up_button(self.btn_project_save, os.path.join(curr_dir, 'i_save.png'), tooltip_text='Save project')
        set_up_button(self.btn_project_saveas, os.path.join(curr_dir, 'i_saveas.png'), tooltip_text='Save project as')

        # Tools buttons
        set_up_button(self.btn_add_junction, os.path.join(curr_dir, 'i_junction.png'), True, 12, 12,
                           'Create junction')  # TODO: softcode
        set_up_button(self.btn_add_reservoir, os.path.join(curr_dir, 'i_reservoir.png'), True, 14, 14,
                           'Create reservoir')  # TODO: softcode
        set_up_button(self.btn_add_tank, os.path.join(curr_dir, 'i_tank.png'), True, 14, 12,
                           'Create tank')  # TODO: softcode
        set_up_button(self.btn_add_pipe, os.path.join(curr_dir, 'i_pipe.png'), True, 13, 5,
                           'Create/edit pipe')  # TODO: softcode
        set_up_button(self.btn_add_pump, os.path.join(curr_dir, 'i_pump.png'), True, 15, 11,
                           'Create pump')  # TODO: softcode
        set_up_button(self.btn_add_valve, os.path.join(curr_dir, 'i_valve.png'), True, 13, 14,
                           'Create valve')  # TODO: softcode
        set_up_button(self.btn_move_element, os.path.join(curr_dir, 'i_move.png'), True, 15, 15,
                           'Move element')  # TODO: softcode
        set_up_button(self.btn_delete_element, os.path.join(curr_dir, 'i_delete2.png'), True, 13, 15,
                           'Delete element(s)')  # TODO: softcode

        # EPANET button
        set_up_button(self.btn_epanet_run, os.path.join(curr_dir, 'i_run.png'), tooltip_text='Run')

        self.btn_move_element.setCheckable(True)
        self.btn_delete_element.setCheckable(True)

        self.btn_add_junction.clicked.connect(self.add_junction)
        self.btn_add_reservoir.clicked.connect(self.add_reservoir)
        self.btn_add_tank.clicked.connect(self.add_tank)

        self.btn_add_pipe.clicked.connect(self.add_pipe)
        self.btn_add_pump.clicked.connect(self.add_pump)
        self.btn_add_valve.clicked.connect(self.add_valve)

        self.btn_move_element.clicked.connect(self.move_element)
        self.btn_delete_element.clicked.connect(self.delete_element)

        self.chk_block_logic.setChecked(True)
        self.chk_block_logic.clicked.connect(self.chk_block_logic_clicked)

        self.lbl_block_logic = HelpLabel('(What is this?)')
        # image = QPixmap(os.path.join(curr_dir, 'i_question_mark.png'))
        # self.lbl_block_logic.setPixmap(image)
        self.lay_block_logic.addWidget(self.lbl_block_logic)

        # Layers
        self.cbo_dem.activated.connect(self.cbo_dem_activated)

        QgsMapLayerRegistry.instance().legendLayersAdded.connect(self.update_layers_combos)
        QgsMapLayerRegistry.instance().layerRemoved.connect(self.update_layers_combos)
        self.update_layers_combos()
        self.preselect_layers_combos()

        self.btn_symbology.clicked.connect(self.apply_symbologies)

        # Junctions ----------------------------------------------------------------------------------------------------
        self.lbl_junction_demand.setText(pre_l('Demand', self.params.options.flow_units))  # TODO: softcode
        self.lbl_junction_deltaz.setText(pre_l('Delta Z', self.params.options.units_deltaz[self.params.options.units]))
        self.txt_junction_demand.setValidator(RegExValidators.get_pos_decimals())
        self.txt_junction_deltaz.setValidator(RegExValidators.get_pos_neg_decimals())
        self.txt_junction_emit_coeff.setValidator(RegExValidators.get_pos_decimals())

        self.update_patterns_combo()

        # Reservoirs ---------------------------------------------------------------------------------------------------
        self.txt_reservoir_deltaz.setValidator(RegExValidators.get_pos_decimals())
        self.lbl_reservoir_deltaz.setText(pre_l('Delta Z', self.params.options.units_deltaz[self.params.options.units]))
        self.txt_reservoir_deltaz.setValidator(RegExValidators.get_pos_neg_decimals())
        self.lbl_reservoir_pressure_head.setText(pre_l('Pressure head', self.params.options.units_deltaz[self.params.options.units]))
        self.txt_reservoir_pressure_head.setValidator(RegExValidators.get_pos_neg_decimals())

        self.update_curves_combo()

        # Tanks --------------------------------------------------------------------------------------------------------
        self.lbl_tank_deltaz.setText(pre_l('Delta Z', self.params.options.units_deltaz[self.params.options.units]))
        self.txt_tank_deltaz.setValidator(RegExValidators.get_pos_neg_decimals())

        # Pipes --------------------------------------------------------------------------------------------------------
        self.lbl_pipe_demand.setText(pre_l('Demand', self.params.options.flow_units))  # TODO: softcode
        self.lbl_pipe_diameter.setText(pre_l('Diameter', self.params.options.units_diameter_pipes[self.params.options.units]))  # TODO: softcode
        self.lbl_pipe_loss.setText(pre_l('Minor loss', '-'))

        self.txt_pipe_demand.setText('0')
        self.txt_pipe_demand.setValidator(RegExValidators.get_pos_decimals())
        self.txt_pipe_diameter.setValidator(RegExValidators.get_pos_decimals())
        self.txt_pipe_loss.setValidator(RegExValidators.get_pos_decimals())

        # TODO: put everything in txt file QUI
        roughnesses_od = {
            'Cast iron':  {
                'C-M': [0.011, 0.015],
                'D-W': [0.1, 5],
                'H-W': [64, 130]},
            'Concrete': {
                'C-M': [0.01, 0.014],
                'D-W': [0.1, 3.0],
                'H-W': [100, 140]},
            'Galvanized iron': {
                'C-M': [0.007, 0.008],
                'D-W': [0.015, 0.05],
                'H-W': [110, 130]},
            'Plastic': {
                'C-M': [0.007, 0.014],
                'D-W': [0.015, 1],
                'H-W': [130, 150]},
            'Steel': {
                'C-M': [0.008, 0.012],
                'D-W': [0.03, 1],
                'H-W': [90, 110]},
            'Vitrified clay': {
                'C-M': [0.008, 0.01],
                'D-W': [0.05, 0.15],
                'H-W': [100, 120]},
       }

        self.cbo_pipe_roughness.clear()

        for key, value in roughnesses_od.iteritems():
            val_min, val_max = value[Options.headloss_cm]
            self.cbo_pipe_roughness.addItem(key, value)

        self.update_roughness_params(
            self.cbo_pipe_roughness.itemData(self.cbo_pipe_roughness.currentIndex())[self.params.options.headloss])
        QtCore.QObject.connect(self.cbo_pipe_roughness, QtCore.SIGNAL('activated(int)'), self.cbo_pipe_roughness_activated)

        self.sli_pipe_roughness.valueChanged.connect(self.roughness_slider_changed)

        self.cbo_pipe_status.clear()
        self.cbo_pipe_status.addItem('Open')  # TODO: softcode
        self.cbo_pipe_status.addItem('Closed')  # TODO: softcode
        self.cbo_pipe_status.addItem('CV')  # TODO: sofcode

        self.txt_pipe_vertex_dist.setValidator(RegExValidators.get_pos_decimals())
        self.txt_pipe_vertex_dist.setText(str(self.params.vertex_dist))
        self.txt_pipe_vertex_dist.textChanged.connect(self.pipe_vertex_dist_changed)

        # Pumps --------------------------------------------------------------------------------------------------------
        self.cbo_pump_param.addItem(Pump.parameters_head)
        self.cbo_pump_param.addItem(Pump.parameters_power)
        self.cbo_pump_param.setCurrentIndex(1)

        self.txt_pump_power.setValidator(RegExValidators.get_pos_decimals())

        QtCore.QObject.connect(self.cbo_pump_param, QtCore.SIGNAL('activated(int)'), self.cbo_pump_param_activated)

        self.txt_pump_speed.setValidator(RegExValidators.get_pos_decimals())

        self.cbo_pump_status.clear()
        self.cbo_pump_status.addItem('Closed', Pump.status_closed)  # TODO: softcode
        self.cbo_pump_status.addItem('Open', Pump.status_open)  # TODO: softcode
        self.cbo_pump_status.setCurrentIndex(self.cbo_pump_status.findData(Pump.status_open))

        # Valves -------------------------------------------------------------------------------------------------------
        self.cbo_valve_type.clear()
        for key, value in Valve.types.iteritems():
            self.cbo_valve_type.addItem(value, key)

        QtCore.QObject.connect(self.cbo_valve_type, QtCore.SIGNAL('activated(int)'), self.cbo_valve_type_activated)

        self.cbo_valve_status.clear()
        self.cbo_valve_status.addItem('None', Valve.status_none)  # TODO: softcode
        self.cbo_valve_status.addItem('Closed', Valve.status_closed)  # TODO: softcode
        self.cbo_valve_status.addItem('Open', Valve.status_open)  # TODO: softcode
        self.cbo_valve_status.setCurrentIndex(self.cbo_valve_status.findData(Valve.status_open))

        # Options ------------------------------------------------------------------------------------------------------
        self.btn_options_hydraulics.clicked.connect(self.btn_hydraulics_clicked)
        self.btn_options_quality.clicked.connect(self.btn_quality_clicked)
        self.btn_options_reactions.clicked.connect(self.btn_reactions_clicked)
        self.btn_options_times.clicked.connect(self.btn_times_clicked)
        self.btn_options_energy.clicked.connect(self.btn_energy_clicked)
        self.btn_options_report.clicked.connect(self.btn_report_clicked)

        # Tools
        # self.btn_create_layers.clicked.connect(self.create_layers_clicked)

        self.txt_snap_tolerance.setText(str(params.snap_tolerance))
        self.txt_snap_tolerance.setValidator(RegExValidators.get_pos_decimals())
        self.txt_snap_tolerance.textEdited.connect(self.snap_tolerance_changed)

        self.btn_pattern_editor.clicked.connect(self.pattern_editor)
        self.btn_curve_editor.clicked.connect(self.curve_editor)
        self.btn_tags_editor.clicked.connect(self.tags_editor)

        self.update_tags_combos()

        # EPANET
        self.btn_epanet_run.clicked.connect(self.btn_epanet_run_clicked)

        self.btn_epanet_output.clicked.connect(self.btn_epanet_output_clicked)

        self.btn_epanet_run.setEnabled(True)

        self.txt_prj_file.setText(self.inp_file_path)

        self.read_inp_file()

    # This method needed by Observable
    def update(self, observable):
        # Update components
        self.update_patterns_combo()
        self.update_curves_combo()
        self.update_tags_combos()

    def closeEvent(self, event):
        self.closingPlugin.emit()
        event.accept()

    def count_elements(self):

        jun_count = self.params.junctions_vlay.featureCount()
        res_count = self.params.reservoirs_vlay.featureCount()
        tan_count = self.params.tanks_vlay.featureCount()
        pip_count = self.params.pipes_vlay.featureCount()
        pum_count = self.params.pumps_vlay.featureCount()
        val_count = self.params.valves_vlay.featureCount()

        text = 'Load OK. ' +\
               str(jun_count) + ' junction(s), ' + \
               str(res_count) + ' reservoir(s), ' + \
               str(tan_count) + ' tank(s), ' + \
               str(pip_count) + ' pipe(s), ' + \
               str(pum_count) + ' pump(s) and ' + \
               str(val_count) + ' valve(s) were loaded.'

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(Parameters.plug_in_name)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setText(text)
        msg_box.exec_()

    # def create_layers_clicked(self):
    #     self.create_layers(None, self.params.crs)

    def create_layers(self, new_layers_d, crs):

        if new_layers_d is not None and new_layers_d[Junction.section_name] is not None:
            self.params.junctions_vlay = new_layers_d[Junction.section_name]
        else:
            self.params.junctions_vlay = MemoryDS.create_junctions_lay(crs=crs)
            self.params.junctions_vlay = MemoryDS.create_junctions_lay(crs=crs)
        self.params.junctions_vlay.attributeValueChanged.connect(self.ju_attrib_val_changed)

        if new_layers_d is not None and new_layers_d[Reservoir.section_name] is not None:
            self.params.reservoirs_vlay = new_layers_d[Reservoir.section_name]
        else:
            self.params.reservoirs_vlay = MemoryDS.create_reservoirs_lay(crs=crs)
        self.params.reservoirs_vlay.attributeValueChanged.connect(self.re_attrib_val_changed)

        if new_layers_d is not None and new_layers_d[Tank.section_name] is not None:
            self.params.tanks_vlay = new_layers_d[Tank.section_name]
        else:
            self.params.tanks_vlay = MemoryDS.create_tanks_lay(crs=crs)
        self.params.tanks_vlay.attributeValueChanged.connect(self.ta_attrib_val_changed)

        if new_layers_d is not None and new_layers_d[Pipe.section_name] is not None:
            self.params.pipes_vlay = new_layers_d[Pipe.section_name]
        else:
            self.params.pipes_vlay = MemoryDS.create_pipes_lay(crs=crs)

        if new_layers_d is not None and new_layers_d[Pump.section_name] is not None:
            self.params.pumps_vlay = new_layers_d[Pump.section_name]
        else:
            self.params.pumps_vlay = MemoryDS.create_pumps_lay(crs=crs)

        if new_layers_d is not None and new_layers_d[Valve.section_name] is not None:
            self.params.valves_vlay = new_layers_d[Valve.section_name]
        else:
            self.params.valves_vlay = MemoryDS.create_valves_lay(crs=crs)

        QgsMapLayerRegistry.instance().addMapLayers([self.params.junctions_vlay,
                                                    self.params.reservoirs_vlay,
                                                    self.params.tanks_vlay,
                                                    self.params.pipes_vlay,
                                                    self.params.pumps_vlay,
                                                    self.params.valves_vlay])

        # Apply symbologies
        self.apply_symbologies()

        # Zoom to layer
        extent = self.params.pipes_vlay.extent()

        if not extent.isNull():
            canvas = self.iface.mapCanvas()
            canvas.setExtent(extent)
            canvas.refresh()

    def add_junction(self):

        if type(self.iface.mapCanvas().mapTool()) is AddJunctionTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddJunctionTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_reservoir(self):

        if type(self.iface.mapCanvas().mapTool()) is AddReservoirTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddReservoirTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_tank(self):

        if type(self.iface.mapCanvas().mapTool()) is AddTankTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            tool = AddTankTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(tool)
            self.setCursor()

    def add_pipe(self):

        if type(self.iface.mapCanvas().mapTool()) is AddPipeTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddPipeTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_pump(self):

        if type(self.iface.mapCanvas().mapTool()) is AddPumpTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddPumpTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def add_valve(self):

        if type(self.iface.mapCanvas().mapTool()) is AddValveTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            self.params.detach(self.tool)

        else:
            self.tool = AddValveTool(self, self.params)
            self.params.attach(self.tool)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.setCursor()

    def setCursor(self):
        self.my_cursor_xpm = [
            "16 16 3 1",
            " »     c None",
            ".»     c #000000",
            "+»     c #FFFFFF",
            "                ",
            "       +.+      ",
            "      ++.++     ",
            "     +.....+    ",
            "    +.     .+   ",
            "   +.   .   .+  ",
            "  +.    .    .+ ",
            " ++.    .    .++",
            " ... ...+... ...",
            " ++.    .    .++",
            "  +.    .    .+ ",
            "   +.   .   .+  ",
            "   ++.     .+   ",
            "    ++.....+    ",
            "      ++.++     ",
            "       +.+      "]

        self.my_pixmap = QPixmap(self.my_cursor_xpm)
        self.my_cursor = QCursor(self.my_pixmap, 8, 8)
        self.iface.mapCanvas().setCursor(self.my_cursor)

    def move_element(self):

        if type(self.iface.mapCanvas().mapTool()) is MoveTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            # self.btn_move_element.setChecked(True)

        else:
            self.tool = MoveTool(self, self.params)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def delete_element(self):

        if type(self.iface.mapCanvas().mapTool()) is DeleteTool:
            self.iface.mapCanvas().unsetMapTool(self.tool)
            # self.btn_delete_element.setChecked(True)

        else:
            self.tool = DeleteTool(self, self.params)
            self.iface.mapCanvas().setMapTool(self.tool)
            self.set_cursor(QtCore.Qt.CrossCursor)

    def ju_attrib_val_changed(self, fid, idx, new_val):
        self.node_attrib_val_changed(fid, idx, self.params.junctions_vlay,
                                     [Junction.field_name_elev, Junction.field_name_delta_z])

    def re_attrib_val_changed(self, fid, idx, new_val):
        self.node_attrib_val_changed(fid, idx, self.params.reservoirs_vlay,
                                     [Reservoir.field_name_elev, Reservoir.field_name_delta_z])

    def ta_attrib_val_changed(self, fid, idx, new_val):
        self.node_attrib_val_changed(fid, idx, self.params.tanks_vlay,
                                     [Tank.field_name_elev, Tank.field_name_delta_z])

    def node_attrib_val_changed(self, fid, idx, layer, elev_field_names):

        # If attibute changed is elev or deltaz, update pipe length
        for elev_field_name in elev_field_names:
            if idx == layer.fieldNameIndex(elev_field_name):
                # Get feature
                for feat in layer.getFeatures(QgsFeatureRequest().setFilterFid(fid)):
                    # Get adjacent links and update length
                    adj_links = NetworkUtils.find_adjacent_links(self.params, feat.geometry())
                    for adj_link in adj_links['pipes']:
                        self.update_link_length(adj_link, self.params.pipes_vlay, Pipe.field_name_length)

    def update_link_length(self, link, layer, length_field_name):
        new_3d_length = LinkHandler.calc_3d_length(self.params, link.geometry())

        field_index = layer.dataProvider().fieldNameIndex(length_field_name)

        if not layer.isEditable():
            layer.startEditing()

        layer.changeAttributeValue(link.id(), field_index, new_3d_length)

    def chk_block_logic_clicked(self):
        self.params.block_logic = self.chk_block_logic.isChecked()

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
            setting_label = 'Pressure' + ' [' + self.params.options.units_deltaz[self.params.options.units] + ']' # TODO: softcode
        elif selected_type == Valve.type_fcv:
            setting_label = 'Flow:' + ' [' + self.params.options.flow_units + ']' # TODO: softcode
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

    def btn_hydraulics_clicked(self):
        if self.hydraulics_dialog is None:
            self.hydraulics_dialog = HydraulicsDialog(self, self.params)
        self.hydraulics_dialog.show()

    def btn_quality_clicked(self):
        if self.quality_dialog is None:
            self.quality_dialog = QualityDialog(self, self.params)
        self.quality_dialog.show()

    def btn_reactions_clicked(self):
        if self.reactions_dialog is None:
            self.reactions_dialog = ReactionsDialog(self, self.params)
        self.reactions_dialog.show()

    def btn_times_clicked(self):
        if self.times_dialog is None:
            self.times_dialog = TimesDialog(self, self.params)
        self.times_dialog.show()

    def btn_energy_clicked(self):
        if self.energy_dialog is None:
            self.energy_dialog = EnergyDialog(self, self.params)
        self.energy_dialog.show()

    def btn_report_clicked(self):
        if self.report_dialog is None:
            self.report_dialog = ReportDialog(self, self.params)
        self.report_dialog.show()

    def roughness_slider_changed(self):
        self.lbl_pipe_roughness_val_val.setText(str(self.sli_pipe_roughness.value() / float(10**self.decimals)))

    # TODO: update snappers in all the tools that use snapping
    def cbo_dem_activated(self, index):
        layer_id = self.cbo_dem.itemData(index)
        self.params.dem_rlay = QgsMapLayerRegistry.instance().mapLayer(layer_id)

    def cbo_pipe_roughness_activated(self):
        self.update_roughness_params(self.get_combo_current_data(self.cbo_pipe_roughness)[self.params.options.headloss])

    def snap_tolerance_changed(self):
        if self.txt_snap_tolerance.text():
            self.params.snap_tolerance = (float(self.txt_snap_tolerance.text()))

    def pattern_editor(self):
        pattern_dialog = GraphDialog(self, self.iface.mainWindow(), self.params, edit_type=GraphDialog.edit_patterns)
        pattern_dialog.exec_()

    def curve_editor(self):

        curve_dialog = GraphDialog(self, self.iface.mainWindow(), self.params, edit_type=GraphDialog.edit_curves)
        curve_dialog.exec_()

    def tags_editor(self):

        tags_dialog = TagsDialog(self, self.iface.mainWindow(), self.params)
        tags_dialog.exec_()

    def project_new_clicked(self):

        self.btn_project_new.setChecked(False)

        file_dialog = QFileDialog()
        file_dialog.setWindowTitle('New project')
        file_dialog.setLabelText(QFileDialog.Accept, 'Create')
        file_dialog.setNameFilter('Inp files (*.inp)')
        if file_dialog.exec_():

            inp_file_path = file_dialog.selectedFiles()[0]
            if not inp_file_path.lower().endswith('.inp'):
                inp_file_path += '.inp'

            self.inp_file_path = inp_file_path
            self.params.last_project_dir = os.path.dirname(inp_file_path)

            lay_utils.remove_layers(self.params)

            # Request CRS for layers
            self.crs_selector()
            self.create_layers(None, self.params.crs)

            self.txt_prj_file.setText(self.inp_file_path)

            # Prompt for hydaulic options
            if self.hydraulics_dialog is None:
                self.hydraulics_dialog = HydraulicsDialog(self, self.params, True)
            self.hydraulics_dialog.show()

    def project_load_clicked(self):

        self.btn_project_load.setChecked(False)

        inp_file_path = QFileDialog.getOpenFileName(self, 'Open inp file', self.params.last_project_dir, 'Inp files (*.inp)')

        if inp_file_path is not None and inp_file_path:
            self.inp_file_path = inp_file_path

            self.txt_prj_file.setText(self.inp_file_path)
            self.params.last_project_dir = os.path.dirname(inp_file_path)
            self.read_inp_file(False)

    def read_inp_file(self, hydraulics_dialog=True):

        # Request CRS for layers
        self.crs_selector()

        # Read inp file
        if os.path.isfile(self.inp_file_path):

            try:

                QApplication.setOverrideCursor(Qt.WaitCursor)

                inp_reader = InpReader(self.inp_file_path)
                new_layers_d = inp_reader.read(self.params)

                lay_utils.remove_layers(self.params)

                self.create_layers(new_layers_d, self.params.crs)
                self.count_elements()

                if not new_layers_d:
                    if hydraulics_dialog:
                        # Prompt for hydaulic options
                        if self.hydraulics_dialog is None:
                            self.hydraulics_dialog = HydraulicsDialog(self, self.params, True)
                        self.hydraulics_dialog.show()

            finally:

                QApplication.restoreOverrideCursor()

    def project_save_clicked(self):

        self.btn_project_save.setChecked(False)

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            inp_file = InpFile()
            inp_file.write_inp_file(self.params, self.inp_file_path, '')

            QApplication.restoreOverrideCursor()


            self.iface.messageBar().pushMessage(
                Parameters.plug_in_name,
                'Project saved.',
                QgsMessageBar.INFO,
                5)  # TODO: softcode

        finally:
            QApplication.restoreOverrideCursor()

    def project_saveas_clicked(self):

        self.btn_project_saveas.setChecked(False)

        inp_file_path = QFileDialog.getSaveFileName(
            self, 'Save project as...', self.params.last_project_dir, 'INP files (*.inp)')

        if inp_file_path is not None and inp_file_path:
            self.inp_file_path = inp_file_path
            self.txt_prj_file.setText(self.inp_file_path)

            try:
                QApplication.setOverrideCursor(Qt.WaitCursor)
                inp_file = InpFile()
                inp_file.write_inp_file(self.params, self.inp_file_path, '')
                QApplication.restoreOverrideCursor()

                self.iface.messageBar().pushMessage(
                    Parameters.plug_in_name,
                    'Project saved.',
                    QgsMessageBar.INFO,
                    5)  # TODO: softcode

            finally:
                QApplication.restoreOverrideCursor()

    def btn_epanet_run_clicked(self):

        config_file = ConfigFile(Parameters.config_file_path)
        inp_file_path = QFileDialog.getOpenFileName(
            self,
            'Select INP file',
            config_file.get_last_inp_file(),
            'INP files (*.inp)')

        if inp_file_path is not None and inp_file_path != '':

            # Remove previous output layers
            for out_layer in self.params.out_layers:
                lay_utils.remove_layer(out_layer)

            config_file.set_last_inp_file(inp_file_path)
            runner = ModelRunner(self)

            rpt_file = os.path.splitext(inp_file_path)[0] + '.rpt'
            out_binary_file = os.path.splitext(inp_file_path)[0] + '.out'

            runner.run(inp_file_path, rpt_file, out_binary_file)

            # Open log
            if not os.path.isfile(rpt_file):
                QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    rpt_file + u' not found!',  # TODO: softcode
                    QMessageBox.Warning)
                return

            self.log_dialog = LogDialog(self.iface.mainWindow(), rpt_file)
            self.log_dialog.exec_()

    def btn_epanet_output_clicked(self):
        if self.output_dialog is None:
            self.output_dialog = OutputAnalyserDialog(self.iface, self.iface.mainWindow(), self.params)
        self.output_dialog.setVisible(True)

    def update_layers_combos(self):

        prev_dem_lay_id = self.cbo_dem.itemData(self.cbo_dem.currentIndex())

        self.cbo_dem.clear()
        self.cbo_dem.addItem('', None)

        layers = self.iface.legendInterface().layers()
        raster_count = 0
        for layer in layers:
            if layer is not None:
                if QgsMapLayer is not None:
                    if layer.type() == QgsMapLayer.RasterLayer:
                        raster_count += 1
                        self.cbo_dem.addItem(layer.name(), layer.id())

        self.set_layercombo_index(self.cbo_dem, prev_dem_lay_id)

    def preselect_layers_combos(self):

        for layer_id in QgsMapLayerRegistry.instance().mapLayers():

            layer = QgsMapLayerRegistry.instance().mapLayer(layer_id)

            names = ['dtm', 'dem']
            if any([x.lower() in QgsMapLayerRegistry.instance().mapLayer(layer_id).name().lower() for x in names]):
                self.set_layercombo_index(self.cbo_dem, layer_id)
                self.params.dem_rlay = layer

    def apply_symbologies(self):

        if self.params.junctions_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_simple_node_sym_renderer(2)
            self.params.junctions_vlay.setRendererV2(renderer)

        if self.params.reservoirs_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_svg_node_sym_renderer(self.params.reservoirs_vlay, misc.reservoir_icon_svg_name, 7)
            self.params.reservoirs_vlay.setRendererV2(renderer)

        if self.params.tanks_vlay is not None:
            ns = symbology.NodeSymbology()
            renderer = ns.make_svg_node_sym_renderer(self.params.tanks_vlay, misc.tank_icon_svg_name, 7)
            self.params.tanks_vlay.setRendererV2(renderer)

        if self.params.pipes_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_simple_link_sym_renderer()
            self.params.pipes_vlay.setRendererV2(renderer)

        if self.params.pumps_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_svg_link_sym_renderer(misc.pump_icon_svg_name, 7)
            self.params.pumps_vlay.setRendererV2(renderer)

        if self.params.valves_vlay is not None:
            ls = symbology.LinkSymbology()
            renderer = ls.make_svg_link_sym_renderer(misc.valve_icon_svg_name, 7)
            self.params.valves_vlay.setRendererV2(renderer)

        symbology.refresh_layer(self.iface.mapCanvas(), self.params.junctions_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.reservoirs_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.tanks_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.pipes_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.pumps_vlay)
        symbology.refresh_layer(self.iface.mapCanvas(), self.params.valves_vlay)

    def update_patterns_combo(self):

        ju_data = self.get_combo_current_text(self.cbo_junction_pattern)
        re_data = self.get_combo_current_text(self.cbo_reservoir_pattern)
        pu_data = self.get_combo_current_text(self.cbo_pump_speed_pattern)

        self.cbo_junction_pattern.clear()
        self.cbo_reservoir_pattern.clear()
        self.cbo_pump_speed_pattern.clear()
        self.cbo_junction_pattern.addItem(None, None)
        self.cbo_reservoir_pattern.addItem(None, None)
        self.cbo_pump_speed_pattern.addItem(None, None)
        if self.params.junctions_vlay is not None:
            for pattern_id, pattern in self.params.patterns.iteritems():
                self.cbo_junction_pattern.addItem(pattern_id, pattern)
                self.cbo_reservoir_pattern.addItem(pattern_id, pattern)
                self.cbo_pump_speed_pattern.addItem(pattern_id, pattern)

        # Restore combo values
        self.set_layercombo_index(self.cbo_junction_pattern, ju_data)
        self.set_layercombo_index(self.cbo_reservoir_pattern, re_data)
        self.set_layercombo_index(self.cbo_pump_speed_pattern, pu_data)

    def update_curves_combo(self):
        ta_data = self.get_combo_current_text(self.cbo_tank_curve)
        pu_data = self.get_combo_current_text(self.cbo_pump_head)
        va_data = self.get_combo_current_text(self.cbo_valve_curve)

        self.cbo_tank_curve.clear()
        self.cbo_pump_head.clear()
        self.cbo_valve_curve.clear()
        self.cbo_tank_curve.addItem(None, None)
        self.cbo_pump_head.addItem(None, None)
        self.cbo_valve_curve.addItem(None, None)
        if self.params.curves is not None:
            for curve in self.params.curves.itervalues():
                self.cbo_tank_curve.addItem(curve.id, curve)
                self.cbo_pump_head.addItem(curve.id, curve)
                self.cbo_valve_curve.addItem(curve.id, curve)

        # Restore combo values
        self.set_layercombo_index(self.cbo_tank_curve, ta_data)
        self.set_layercombo_index(self.cbo_pump_head, pu_data)
        self.set_layercombo_index(self.cbo_valve_curve, va_data)

    def update_tags_combos(self):
        ju_data = self.get_combo_current_text(self.cbo_junction_tag)
        re_data = self.get_combo_current_text(self.cbo_reservoir_tag)
        ta_data = self.get_combo_current_text(self.cbo_tank_tag)
        pi_data = self.get_combo_current_text(self.cbo_pipe_tag)
        pu_data = self.get_combo_current_text(self.cbo_pump_tag)
        va_data = self.get_combo_current_text(self.cbo_valve_tag)

        self.cbo_junction_tag.clear()
        self.cbo_reservoir_tag.clear()
        self.cbo_tank_tag.clear()
        self.cbo_pipe_tag.clear()
        self.cbo_pump_tag.clear()
        self.cbo_valve_tag.clear()
        self.cbo_junction_tag.addItem(None, None)
        self.cbo_reservoir_tag.addItem(None, None)
        self.cbo_tank_tag.addItem(None, None)
        self.cbo_pipe_tag.addItem(None, None)
        self.cbo_pump_tag.addItem(None, None)
        self.cbo_valve_tag.addItem(None, None)

        if self.params.tag_names is not None:
            for tag_name in self.params.tag_names:
                self.cbo_junction_tag.addItem(tag_name, tag_name)
                self.cbo_reservoir_tag.addItem(tag_name, tag_name)
                self.cbo_tank_tag.addItem(tag_name, tag_name)
                self.cbo_pipe_tag.addItem(tag_name, tag_name)
                self.cbo_pump_tag.addItem(tag_name, tag_name)
                self.cbo_valve_tag.addItem(tag_name, tag_name)

        # Restore combo values
        self.set_layercombo_index(self.cbo_junction_tag, ju_data)
        self.set_layercombo_index(self.cbo_reservoir_tag, re_data)
        self.set_layercombo_index(self.cbo_tank_tag, ta_data)
        self.set_layercombo_index(self.cbo_pipe_tag, pi_data)
        self.set_layercombo_index(self.cbo_pump_tag, pu_data)
        self.set_layercombo_index(self.cbo_valve_tag, va_data)

    def get_combo_current_data(self, combo):
        index = combo.currentIndex()
        return combo.itemData(index)

    def get_combo_current_text(self, combo):
        return combo.currentText()

    def set_layercombo_index(self, combo, combo_data):
        index = combo.findText(combo_data)
        if index >= 0:
            combo.setCurrentIndex(index)
        else:
            if combo.count() > 0:
                combo.setCurrentIndex(0)

    def pipe_vertex_dist_changed(self, vertex_dist):
        if vertex_dist is not None and vertex_dist:
            self.params.vertex_dist = float(vertex_dist)

    def find_decimals(self, float_string):
        float_string.replace(',', '.')
        if '.' in float_string:
            decimals = len(float_string[float_string.index('.'):])
        else:
            decimals = 1
        return decimals

    def update_roughness_params(self, roughness_range):

        min_roughness = roughness_range[0]
        max_roughness = roughness_range[1]

        min_roughness_mult = min_roughness * 10 ** self.decimals
        max_roughness_mult = max_roughness * 10 ** self.decimals

        # If US units and D-W, convert mm to feet*10-3
        if self.params.options.headloss == Options.headloss_dw and self.params.options.units == Options.unit_sys_us:
            min_roughness = min_roughness / 304.8 * 1000
            max_roughness = max_roughness / 304.8 * 1000

        # To string
        min_roughness = str(min_roughness)
        max_roughness = str(max_roughness)

        self.decimals = max(self.find_decimals(min_roughness), self.find_decimals(max_roughness))

        self.lbl_pipe_roughness_min.setText(min_roughness)
        self.lbl_pipe_roughness_max.setText(max_roughness)
        self.lbl_pipe_roughness_val_val.setText(min_roughness)

        # Multipliers
        self.sli_pipe_roughness.setMinimum(min_roughness_mult)
        self.sli_pipe_roughness.setMaximum(max_roughness_mult)
        self.sli_pipe_roughness.setValue(min_roughness_mult)

    def set_cursor(self, cursor_shape):
        cursor = QtGui.QCursor()
        cursor.setShape(cursor_shape)
        self.iface.mapCanvas().setCursor(cursor)

    def crs_selector(self):

        # Request CRS for layers
        proj_selector = QgsGenericProjectionSelector()
        proj_selector.exec_()
        proj_id = proj_selector.selectedAuthId()
        crs = QgsCoordinateReferenceSystem(proj_id)
        self.params.crs = crs

class NewFileDialog(QFileDialog):
    def __init__(self):
        super(NewFileDialog, self).__init__()

        self.setWindowTitle('Pick a name for your project...')
        self.setFileMode(QFileDialog.AnyFile)
        self.setLabelText(QFileDialog.Accept, 'OK')

    def accept(self):
        try:
            file_path = self.selectedFiles()[0]
            if os.path.isfile(file_path):
                ret = QtGui.QMessageBox.question(
                    self.iface.mainWindow(),
                    Parameters.plug_in_name,
                    u'The file already exists. Overwrite?',
                    # TODO: softcode
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)

                if ret == QtGui.QMessageBox.No:
                    return
            QFileDialog.accept(self)

        except Exception as e:
            print e
            return


class HelpLabel(QLabel):
    def __init__(self, parent=None):
        super(HelpLabel, self).__init__(parent)
        self.setAutoFillBackground(True)
        self.setMouseTracking(True)

    def mouseMoveEvent(self, event):
        QToolTip.showText(event.globalPos(),
                          'Block logic expects pumps and valves to always\n'
                          'have two junctions at their endpoints.\n'
                          'The pump or valve, together with the two junctions,\n'
                          'are then considered as a single block, and they are\n'
                          'moved jointly when using the "Move element tool".',
                          self, self.rect())

    def mousePressEvent(self, event):
        print event


class MyQFileDialog(QFileDialog):
    def __init__(self):
        super(MyQFileDialog, self).__init__()

    def accept(self):

        try:
            file_path = self.selectedFiles()[0]
            if not os.path.isfile(file_path):
                if not file_path.lower().endswith('.inp'):
                    file_path += '.inp'
                f = open(file_path, 'w')
                f.close()
            QFileDialog.accept(self)
        except Exception as e:
            print e
            return