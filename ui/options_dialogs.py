from PyQt4.QtGui import QDialog, QFormLayout, QLabel, QComboBox, QLineEdit, QCheckBox, QPushButton, QFrame, QHBoxLayout,\
    QMessageBox, QFileDialog, QVBoxLayout
from PyQt4 import QtCore
from ..tools.parameters import Parameters, RegExValidators
from ..model.times import Hour
from utils import prepare_label as pre_l
import os

min_width = 200
min_height = 400


class HydraulicsDialog(QDialog):
    def __init__(self, parent, parameters):
        QDialog.__init__(self, parent)

        self.parent = parent
        self.params = parameters

        self.setMinimumWidth(min_width)
        # self.setMinimumHeight(min_height)

        # Build dialog
        self.setWindowTitle('Options - Hydraulics')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.fra_form = QFrame(self)
        fra_form_lay = QFormLayout(self.fra_form)
        fra_form_lay.setContentsMargins(10, 10, 10, 10)

        self.lbl_units = QLabel('Units system:') # TODO: softocode
        self.cbo_units = QComboBox()
        fra_form_lay.addRow(self.lbl_units, self.cbo_units)

        self.lbl_flow_units = QLabel('Flow units:')  # TODO: softocode
        self.cbo_flow_units = QComboBox()
        fra_form_lay.addRow(self.lbl_flow_units, self.cbo_flow_units)

        self.lbl_headloss = QLabel('Head loss:')  # TODO: softocode
        self.cbo_headloss = QComboBox()
        fra_form_lay.addRow(self.lbl_headloss, self.cbo_headloss)

        self.chk_hydraulics = QCheckBox('Hydraulics:') # TODO: softcode
        self.cbo_hydraulics = QComboBox()
        fra_form_lay.addRow(self.chk_hydraulics, self.cbo_hydraulics)

        self.txt_hydraulics_file = QLineEdit()
        fra_form_lay.addRow(None, self.txt_hydraulics_file)

        self.btn_hydraulics_file = QPushButton('File...')  # TODO: softcode
        fra_form_lay.addRow(None, self.btn_hydraulics_file)

        self.lbl_viscosity = QLabel('Viscosity:')  # TODO: softocode
        self.txt_viscosity = QLineEdit()
        fra_form_lay.addRow(self.lbl_viscosity, self.txt_viscosity)

        self.lbl_diffusivity = QLabel('Diffusivity:')  # TODO: softocode
        self.txt_diffusivity = QLineEdit()
        fra_form_lay.addRow(self.lbl_diffusivity, self.txt_diffusivity)

        self.lbl_spec_gravity = QLabel('Specific gravity:')  # TODO: softocode
        self.txt_spec_gravity = QLineEdit()
        fra_form_lay.addRow(self.lbl_spec_gravity, self.txt_spec_gravity)

        self.lbl_max_trials = QLabel('Max trials:')  # TODO: softocode
        self.txt_max_trials = QLineEdit()
        fra_form_lay.addRow(self.lbl_max_trials, self.txt_max_trials)

        self.lbl_accuracy = QLabel('Accuracy:')  # TODO: softocode
        self.txt_accuracy = QLineEdit()
        fra_form_lay.addRow(self.lbl_accuracy, self.txt_accuracy)

        self.lbl_unbalanced = QLabel('Unbalanced:') # TODO: softcode
        self.fra_unbalanced = QFrame(self)
        fra_unbalanced_lay = QHBoxLayout(self.fra_unbalanced)
        fra_unbalanced_lay.setContentsMargins(0, 0, 0, 0)
        self.cbo_unbalanced = QComboBox()
        self.txt_unbalanced = QLineEdit()
        fra_unbalanced_lay.addWidget(self.cbo_unbalanced)
        fra_unbalanced_lay.addWidget(self.txt_unbalanced)
        fra_form_lay.addRow(self.lbl_unbalanced, self.fra_unbalanced)

        self.lbl_pattern = QLabel('Pattern:')  # TODO: softocode
        self.txt_pattern = QLineEdit()
        fra_form_lay.addRow(self.lbl_pattern, self.txt_pattern)

        self.lbl_demand_mult = QLabel('Demand multiplier:')  # TODO: softocode
        self.txt_demand_mult = QLineEdit()
        fra_form_lay.addRow(self.lbl_demand_mult, self.txt_demand_mult)

        self.lbl_emitter_exp = QLabel('Emitter exponent:')  # TODO: softocode
        self.txt_emitter_exp = QLineEdit()
        fra_form_lay.addRow(self.lbl_emitter_exp, self.txt_emitter_exp)

        self.lbl_tolerance = QLabel('Tolerance:')  # TODO: softocode
        self.txt_tolerance = QLineEdit()
        fra_form_lay.addRow(self.lbl_tolerance, self.txt_tolerance)

        # Buttons
        self.fra_buttons = QFrame(self)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        self.btn_Cancel = QPushButton('Cancel')
        self.btn_Ok = QPushButton('OK')
        fra_buttons_lay.addWidget(self.btn_Cancel)
        fra_buttons_lay.addWidget(self.btn_Ok)

        # Add to main
        fra_main_lay = QVBoxLayout(self)
        fra_main_lay.setContentsMargins(0, 0, 0, 0)
        fra_main_lay.addWidget(self.fra_form)
        fra_main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):

        for unit in self.params.options.units_sys:
            self.cbo_units.addItem(self.params.options.units_sys_text[unit], unit)
        for fu in range(len(self.params.options.units_flow[self.params.options.units])):
            self.cbo_flow_units.addItem(self.params.options.units_flow_text[self.params.options.units][fu],
                                        self.params.options.units_flow[self.params.options.units][fu])

        self.cbo_units.activated.connect(self.cbo_units_activated)
        # self.cbo_flow_units.activated.connect(self.cbo_flow_units_activated)

        for key, value in self.params.options.headlosses_text.iteritems():
            self.cbo_headloss.addItem(value, key)

        self.cbo_headloss.activated.connect(self.cbo_headloss_activated)

        self.chk_hydraulics.stateChanged.connect(self.chk_hydraulics_changed)
        self.btn_hydraulics_file.pressed.connect(self.btn_hydraulics_pressed)
        self.cbo_hydraulics.addItem('Use', self.params.options.hydraulics.action_use)
        self.cbo_hydraulics.addItem('Save', self.params.options.hydraulics.action_save)
        self.txt_hydraulics_file.setReadOnly(True)

        # - Unbalanced
        for id, text in self.params.options.unbalanced.unb_text.iteritems():
            self.cbo_unbalanced.addItem(text, id)

        self.cbo_unbalanced.activated.connect(self.cbo_unbalanced_changed)
        self.txt_unbalanced.setValidator(RegExValidators.get_pos_int_no_zero())
        self.txt_unbalanced.setText('1')

        # Buttons
        self.btn_Cancel.pressed.connect(self.btn_cancel_pressed)
        self.btn_Ok.pressed.connect(self.btn_ok_pressed)

        # Validators
        self.txt_viscosity.setValidator(RegExValidators.get_pos_decimals())
        self.txt_diffusivity.setValidator(RegExValidators.get_pos_decimals())
        self.txt_spec_gravity.setValidator(RegExValidators.get_pos_decimals())
        self.txt_max_trials.setValidator(RegExValidators.get_pos_int_no_zero())
        self.txt_accuracy.setValidator(RegExValidators.get_pos_decimals())
        self.txt_pattern.setValidator(RegExValidators.get_pos_decimals())
        self.txt_demand_mult.setValidator(RegExValidators.get_pos_decimals())
        self.txt_emitter_exp.setValidator(RegExValidators.get_pos_decimals())
        self.txt_tolerance.setValidator(RegExValidators.get_pos_decimals())

    def initialize(self):
        
        self.cbo_units.setCurrentIndex(self.cbo_units.findData(self.params.options.units))
        self.cbo_flow_units.setCurrentIndex(self.cbo_flow_units.findData(self.params.options.flow_units))
        self.cbo_headloss.setCurrentIndex(self.cbo_headloss.findData(self.params.options.headloss))

        self.chk_hydraulics.setChecked(not self.params.options.hydraulics.use_hydraulics)
        if self.params.options.hydraulics.action is not None:
            self.cbo_hydraulics.setCurrentIndex(self.cbo_hydraulics.findData(self.params.options.hydraulics.action))
        if self.params.options.hydraulics.file is not None:
            self.txt_hydraulics_file.setText(self.params.options.hydraulics.file)

        self.txt_viscosity.setText(str(self.params.options.viscosity))
        self.txt_diffusivity.setText(str(self.params.options.diffusivity))
        self.txt_spec_gravity.setText(str(self.params.options.spec_gravity))
        self.txt_max_trials.setText(str(self.params.options.trials))
        self.txt_accuracy.setText(str(self.params.options.accuracy))

        self.cbo_unbalanced.setCurrentIndex(self.cbo_unbalanced.findData(self.params.options.unbalanced.unbalanced))
        self.txt_unbalanced.setEnabled(self.cbo_unbalanced.currentIndex() != 0)
        self.txt_unbalanced.setText(str(self.params.options.unbalanced.trials))

        self.txt_pattern.setText(str(self.params.options.pattern))
        self.txt_demand_mult.setText(str(self.params.options.demand_mult))
        self.txt_emitter_exp.setText(str(self.params.options.emitter_exp))
        self.txt_tolerance.setText(str(self.params.options.tolerance))

    def cbo_units_activated(self):

        # Parameters combo box
        self.cbo_flow_units.clear()
        for fu in range(len(self.params.options.units_flow[self.params.options.units])):
            self.cbo_flow_units.addItem(self.params.options.units_flow_text[self.params.options.units][fu],
                                               self.params.options.units_flow[self.params.options.units][fu])

    def cbo_headloss_activated(self):

        # Warning
        QMessageBox.warning(
            self,
            Parameters.plug_in_name,
            u'Head loss units changed: the head loss values already present might need to be reviewed.',
            QMessageBox.Ok)

    def chk_hydraulics_changed(self):

        self.btn_hydraulics_file.setEnabled(self.chk_hydraulics.isChecked())
        self.cbo_hydraulics.setEnabled(self.chk_hydraulics.isChecked())
        self.txt_hydraulics_file.setEnabled(self.chk_hydraulics.isChecked())

    def btn_hydraulics_pressed(self):
        file_dialog = QFileDialog(self, 'Select hydraulics file')
        file_dialog.setLabelText(QFileDialog.Accept, 'Select')
        file_dialog.setLabelText(QFileDialog.Reject, 'Cancel')
        file_dialog.setFileMode(QFileDialog.AnyFile)

        file_dialog.exec_()

        hydraulics_file_path = file_dialog.selectedFiles()

        if not hydraulics_file_path or hydraulics_file_path[0] is None or hydraulics_file_path[0] == '':
            return

        self.txt_hydraulics_file.setText(hydraulics_file_path[0])

    def cbo_unbalanced_changed(self):
        self.txt_unbalanced.setEnabled(
            self.cbo_unbalanced.itemData(
                self.cbo_unbalanced.currentIndex()) == self.params.options.unbalanced.unb_continue)

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):

        if not self.check_params():
            return

        # Update parameters and options
        self.params.units = self.cbo_units.itemData(self.cbo_units.currentIndex())
        self.params.flow_units = self.cbo_flow_units.itemData(self.cbo_flow_units.currentIndex())
        self.params.options.headloss = self.cbo_headloss.itemData(self.cbo_headloss.currentIndex())
        self.params.options.hydraulics.use_hydraulics = self.chk_hydraulics.setChecked

        if self.params.options.hydraulics.action is not None:
            self.params.options.hydraulics.action = self.cbo_hydraulics.itemData(self.cbo_hydraulics.currentIndex())
            self.params.options.hydraulics.file = self.txt_hydraulics_file.text()

        self.params.options.viscosity = float(self.txt_viscosity.text())
        self.params.options.diffusivity = float(self.txt_diffusivity.text())
        self.params.options.spec_gravity = float(self.txt_spec_gravity.text())
        self.params.options.trials = float(self.txt_max_trials.text())
        self.params.options.accuracy = float(self.txt_accuracy.text())

        self.params.options.unbalanced.unbalanced = self.cbo_unbalanced.itemData(self.cbo_unbalanced.currentIndex())
        self.params.options.unbalanced.trials = int(self.txt_unbalanced.text())

        self.params.options.pattern = self.txt_pattern.text()
        self.params.options.demand_mult = float(self.txt_demand_mult.text())
        self.params.options.emitter_exp = float(self.txt_emitter_exp.text())
        self.params.options.tolerance = float(self.txt_tolerance.text())

        # Junctions
        self.parent.lbl_junction_demand.setText(pre_l('Demand', self.params.options.units_flow[self.params.options.units][0]))  # TODO: softcode
        self.parent.lbl_junction_depth.setText(pre_l('Delta Z', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode

        # Reservoirs
        self.parent.lbl_reservoir_head.setText(pre_l('Head', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_reservoir_elev_corr.setText(pre_l('Delta Z', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode

        # Tanks
        self.parent.lbl_tank_elev_corr.setText(pre_l('Delta Z', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_tank_level_init.setText(pre_l('Level init.', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_tank_level_min.setText(pre_l('Level min', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_tank_level_max.setText(pre_l('Level max', self.params.options.units_depth[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_tank_diameter.setText(pre_l('Diameter', self.params.options.units_diameter_tanks[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_tank_vol_min.setText(pre_l('Volume min', self.params.options.units_volume[self.params.options.units]))  # TODO: softcode

        # Pipes
        self.parent.lbl_pipe_demand.setText(pre_l('Demand', self.params.options.units_flow[self.params.options.units][0]))  # TODO: softcode
        self.parent.lbl_pipe_diameter.setText(pre_l('Diameter', self.params.options.units_diameter_pipes[self.params.options.units]))  # TODO: softcode
        self.parent.lbl_pipe_roughness.setText(pre_l('Roughness', self.params.options.units_roughness[self.params.options.units][self.params.options.headloss]))  # TODO: softcode

        # Pumps
        self.parent.lbl_pump_head.setText(pre_l('Head', self.params.options.units_depth[self.params.options.units]))
        self.parent.lbl_pump_power.setText(pre_l('Power', self.params.options.units_power[self.params.options.units]))

        # Valves
        self.parent.lbl_valve_setting.setText(pre_l('Pressure', self.params.options.units_pressure[self.params.options.units]))
        self.parent.lbl_valve_diameter.setText(pre_l('Pressure', self.params.options.units_diameter_pipes[self.params.options.units]))

        # Flow units
        units = self.cbo_flow_units.itemData(self.cbo_flow_units.currentIndex())
        self.parent.lbl_junction_demand.setText(pre_l('Demand', units))  # TODO: softcode
        self.parent.lbl_pipe_demand.setText(pre_l('Demand', units))  # TODO: softcode

        # Headloss units
        self.params.options.headloss_units = self.cbo_headloss.itemData(self.cbo_headloss.currentIndex())
        self.parent.lbl_pipe_roughness.setText(
            pre_l(
                'Roughness',
                self.params.options.units_roughness[self.params.options.units][self.params.options.headloss_units]))

        self.setVisible(False)

    def check_params(self):

        if self.chk_hydraulics.isChecked():
            if not os.path.isfile(self.txt_hydraulics_file.text()):
                QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    u'Hydraulics option slected, but no valid file specified.',
                    QMessageBox.Ok)
                return False

        return True


class QualityDialog(QDialog):

    def __init__(self, parent, parameters):

        QDialog.__init__(self, parent)

        self.parent = parent
        self.params = parameters

        self.setMinimumWidth(min_width)
        # self.setMinimumHeight(min_height)

        # Build dialog
        self.setWindowTitle('Options - Quality')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.fra_form = QFrame(self)
        fra_form_lay = QFormLayout(self.fra_form)
        fra_form_lay.setContentsMargins(10, 10, 10, 10)

        self.lbl_parameter = QLabel('Parameter:')  # TODO: softocode
        self.cbo_parameter = QComboBox()
        fra_form_lay.addRow(self.lbl_parameter, self.cbo_parameter)

        self.lbl_mass_units = QLabel('Mass units:')  # TODO: softocode
        self.cbo_mass_units = QComboBox()
        fra_form_lay.addRow(self.lbl_mass_units, self.cbo_mass_units)

        self.lbl_rel_diff = QLabel('Relative diffusivity:')  # TODO: softocode
        self.txt_rel_diff = QLineEdit()
        fra_form_lay.addRow(self.lbl_rel_diff, self.txt_rel_diff)

        self.lbl_trace_node = QLabel('Trace node:')  # TODO: softocode
        self.txt_trace_node = QLineEdit()
        fra_form_lay.addRow(self.lbl_trace_node, self.txt_trace_node)

        self.lbl_quality_tol = QLabel('Quality tolerance:')  # TODO: softocode
        self.txt_quality_tol = QLineEdit()
        fra_form_lay.addRow(self.lbl_quality_tol, self.txt_quality_tol)

        # Buttons
        self.fra_buttons = QFrame(self)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        self.btn_Cancel = QPushButton('Cancel')
        self.btn_Ok = QPushButton('OK')
        fra_buttons_lay.addWidget(self.btn_Cancel)
        fra_buttons_lay.addWidget(self.btn_Ok)

        # Add to main
        fra_main_lay = QVBoxLayout(self)
        fra_main_lay.setContentsMargins(0, 0, 0, 0)
        fra_main_lay.addWidget(self.fra_form)
        fra_main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):
        for key, value in self.params.options.quality.quality_text.iteritems():
            self.cbo_parameter.addItem(value, key)

        for key, value in self.params.options.quality.quality_units_text.iteritems():
            self.cbo_mass_units.addItem(value, key)

        # Buttons
        self.btn_Cancel.pressed.connect(self.btn_cancel_pressed)
        self.btn_Ok.pressed.connect(self.btn_ok_pressed)

        # Validators
        self.txt_rel_diff.setValidator(RegExValidators.get_pos_decimals())
        self.txt_quality_tol.setValidator(RegExValidators.get_pos_decimals())

    def initialize(self):
        self.cbo_parameter.setCurrentIndex(self.cbo_parameter.findData(self.params.options.quality.parameter))
        self.cbo_mass_units.setCurrentIndex(self.cbo_mass_units.findData(self.params.options.quality.mass_units))
        self.txt_rel_diff.setText(str(self.params.options.quality.relative_diff))
        self.txt_trace_node.setText(str(self.params.options.quality.trace_junction_id))
        self.txt_quality_tol.setText(str(self.params.options.quality.quality_tol))

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):

        # Update parameters and options
        self.params.options.quality.parameter = self.cbo_parameter.itemData(self.cbo_parameter.currentIndex())
        self.params.options.quality.mass_units = self.cbo_mass_units.itemData(self.cbo_mass_units.currentIndex())

        self.params.options.quality.relative_diff = float(self.txt_rel_diff.text())
        self.params.options.quality.trace_junction_id = self.txt_trace_node.text()
        self.params.options.quality.quality_tol = float(self.txt_quality_tol.text())

        self.setVisible(False)


class TimesDialog(QDialog):

    def __init__(self, parent, parameters):

        QDialog.__init__(self, parent)

        self.parent = parent
        self.params = parameters

        self.setMinimumWidth(min_width)

        # Build dialog
        self.setWindowTitle('Options - Times')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.fra_form = QFrame(self)
        fra_form_lay = QFormLayout(self.fra_form)
        fra_form_lay.setContentsMargins(10, 10, 10, 10)

        self.lbl_units = QLabel('Units:')  # TODO: softocode
        self.cbo_units = QComboBox()
        fra_form_lay.addRow(self.lbl_units, self.cbo_units)

        self.lbl_duration = QLabel('Duration:')  # TODO: softocode
        self.txt_duration = QLineEdit()
        fra_form_lay.addRow(self.lbl_duration, self.txt_duration)

        self.lbl_hydraulic_timestamp = QLabel('Hydraulic timestamp:')  # TODO: softocode
        self.txt_hydraulic_timestamp = QLineEdit()
        fra_form_lay.addRow(self.lbl_hydraulic_timestamp, self.txt_hydraulic_timestamp)

        self.lbl_quality_timestamp = QLabel('Quality timestamp:')  # TODO: softocode
        self.txt_quality_timestamp = QLineEdit()
        fra_form_lay.addRow(self.lbl_quality_timestamp, self.txt_quality_timestamp)

        self.lbl_rule_timestamp = QLabel('Rule timestamp:')  # TODO: softocode
        self.txt_rule_timestamp = QLineEdit()
        fra_form_lay.addRow(self.lbl_rule_timestamp, self.txt_rule_timestamp)

        self.lbl_pattern_timestamp = QLabel('Pattern timestamp:')  # TODO: softocode
        self.txt_pattern_timestamp = QLineEdit()
        fra_form_lay.addRow(self.lbl_pattern_timestamp, self.txt_pattern_timestamp)

        self.lbl_pattern_start = QLabel('Pattern start:')  # TODO: softocode
        self.txt_pattern_start = QLineEdit()
        fra_form_lay.addRow(self.lbl_pattern_start, self.txt_pattern_start)

        self.lbl_report_timestamp = QLabel('Report timestamp:')  # TODO: softocode
        self.txt_report_timestamp = QLineEdit()
        fra_form_lay.addRow(self.lbl_report_timestamp, self.txt_report_timestamp)

        self.lbl_report_start = QLabel('Report start:')  # TODO: softocode
        self.txt_report_start = QLineEdit()
        fra_form_lay.addRow(self.lbl_report_start, self.txt_report_start)

        self.lbl_clock_time_start = QLabel('Clock start time:')  # TODO: softocode
        self.txt_clock_time_start = QLineEdit()
        fra_form_lay.addRow(self.lbl_clock_time_start, self.txt_clock_time_start)

        self.lbl_statistic = QLabel('Statistic:')  # TODO: softocode
        self.cbo_statistic = QComboBox()
        fra_form_lay.addRow(self.lbl_statistic, self.cbo_statistic)

        # Buttons
        self.fra_buttons = QFrame(self)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        self.btn_Cancel = QPushButton('Cancel')
        self.btn_Ok = QPushButton('OK')
        fra_buttons_lay.addWidget(self.btn_Cancel)
        fra_buttons_lay.addWidget(self.btn_Ok)

        # Add to main
        fra_main_lay = QVBoxLayout(self)
        fra_main_lay.setContentsMargins(0, 0, 0, 0)
        fra_main_lay.addWidget(self.fra_form)
        fra_main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):

        for key, text in self.params.times.unit_text.iteritems():
            self.cbo_units.addItem(text, key)

        for key, text in self.params.times.stats_text.iteritems():
            self.cbo_statistic.addItem(text, key)

        # Buttons
        self.btn_Cancel.pressed.connect(self.btn_cancel_pressed)
        self.btn_Ok.pressed.connect(self.btn_ok_pressed)

        # Validators
        self.txt_duration.setValidator(RegExValidators.get_pos_int())

        self.txt_hydraulic_timestamp.setInputMask('09:99')
        self.txt_hydraulic_timestamp.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_quality_timestamp.setInputMask('09:99')
        self.txt_quality_timestamp.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_rule_timestamp.setInputMask('09:99')
        self.txt_rule_timestamp.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_pattern_timestamp.setInputMask('09:99')
        self.txt_pattern_timestamp.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_pattern_start.setInputMask('09:99')
        self.txt_pattern_start.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_report_timestamp.setInputMask('09:99')
        self.txt_report_timestamp.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_report_start.setInputMask('09:99')
        self.txt_report_start.setValidator(RegExValidators.get_time_hh_mm())

        self.txt_clock_time_start.setInputMask('09:99')
        self.txt_clock_time_start.setValidator(RegExValidators.get_time_hh_mm())

        for key, text in self.params.times.stats_text.iteritems():
            self.cbo_statistic.addItem(text, key)

    def initialize(self):
        self.cbo_units.setCurrentIndex(self.cbo_units.findData(self.params.times.units))
        self.txt_duration.setText(str(self.params.times.duration))
        self.txt_hydraulic_timestamp.setText(self.params.times.hydraulic_timestamp.get_as_text())
        self.txt_quality_timestamp.setText(self.params.times.quality_timestamp.get_as_text())
        self.txt_rule_timestamp.setText(self.params.times.rule_timestamp.get_as_text())
        self.txt_pattern_timestamp.setText(self.params.times.pattern_timestamp.get_as_text())
        self.txt_pattern_start.setText(self.params.times.pattern_start.get_as_text())
        self.txt_report_timestamp.setText(self.params.times.report_timestamp.get_as_text())
        self.txt_report_start.setText(self.params.times.report_start.get_as_text())
        self.txt_clock_time_start.setText(self.params.times.clocktime_start.get_as_text())
        self.cbo_statistic.setCurrentIndex(self.cbo_statistic.findData(self.params.times.statistics))

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):

        # Update parameters and options
        self.params.times.units = self.cbo_units.itemData(self.cbo_units.currentIndex())
        self.params.times.duration = Hour.from_string(self.txt_duration.text())
        self.params.times.hydraulic_timestamp = Hour.from_string(self.txt_hydraulic_timestamp.text())
        self.params.times.quality_timestamp = Hour.from_string(self.txt_quality_timestamp.text())
        self.params.times.rule_timestamp = Hour.from_string(self.txt_rule_timestamp.text())
        self.params.times.pattern_timestamp = Hour.from_string(self.txt_pattern_timestamp.text())
        self.params.times.pattern_start = Hour.from_string(self.txt_pattern_start.text())
        self.params.times.report_timestamp = Hour.from_string(self.txt_report_timestamp.text())
        self.params.times.report_start= Hour.from_string(self.txt_report_start.text())
        self.params.times.clocktime_start = Hour.from_string(self.txt_clock_time_start.text())
        self.params.times.statistics = self.cbo_statistic.itemData(self.cbo_statistic.currentIndex())

        self.setVisible(False)


class EnergyDialog(QDialog):

    def __init__(self, parent, parameters):

        QDialog.__init__(self, parent)

        self.parent = parent
        self.params = parameters

        self.setMinimumWidth(min_width)
        # self.setMinimumHeight(min_height)

        # Build dialog
        self.setWindowTitle('Options - Energy')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        self.fra_form = QFrame(self)
        fra_form_lay = QFormLayout(self.fra_form)
        fra_form_lay.setContentsMargins(10, 10, 10, 10)

        self.lbl_pump_efficiency = QLabel('Pump efficiency [%]:')  # TODO: softocode
        self.txt_pump_efficiency = QLineEdit()
        fra_form_lay.addRow(self.lbl_pump_efficiency, self.txt_pump_efficiency)

        self.lbl_energy_price = QLabel('Energi price/kwh:')  # TODO: softocode
        self.txt_energy_price = QLineEdit()
        fra_form_lay.addRow(self.lbl_energy_price, self.txt_energy_price)

        self.lbl_price_pattern = QLabel('Price pattern:')  # TODO: softocode
        self.txt_price_pattern = QLineEdit() # TODO: replace with dropdown
        fra_form_lay.addRow(self.lbl_price_pattern, self.txt_price_pattern)

        self.lbl_demand_charge = QLabel('Demand charge:')  # TODO: softocode
        self.txt_demand_charge = QLineEdit()
        fra_form_lay.addRow(self.lbl_demand_charge, self.txt_demand_charge)

        # Buttons
        self.fra_buttons = QFrame(self)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        self.btn_Cancel = QPushButton('Cancel')
        self.btn_Ok = QPushButton('OK')
        fra_buttons_lay.addWidget(self.btn_Cancel)
        fra_buttons_lay.addWidget(self.btn_Ok)

        # Add to main
        fra_main_lay = QVBoxLayout(self)
        fra_main_lay.setContentsMargins(0, 0, 0, 0)
        fra_main_lay.addWidget(self.fra_form)
        fra_main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):

        # Buttons
        self.btn_Cancel.pressed.connect(self.btn_cancel_pressed)
        self.btn_Ok.pressed.connect(self.btn_ok_pressed)

        # Validators
        self.txt_pump_efficiency.setValidator(RegExValidators.get_pos_decimals())
        self.txt_energy_price.setValidator(RegExValidators.get_pos_decimals())
        self.txt_price_pattern.setValidator(RegExValidators.get_pos_int())
        self.txt_demand_charge.setValidator(RegExValidators.get_pos_decimals())

    def initialize(self):
        self.txt_pump_efficiency.setText(str(self.params.energy.pump_efficiency))
        self.txt_energy_price.setText(str(self.params.energy.energy_price))
        self.txt_price_pattern.setText(str(self.params.energy.price_pattern) if self.params.energy.price_pattern is not None else '')
        self.txt_demand_charge.setText(str(self.params.energy.demand_charge))

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):

        self.params.energy.pump_efficiency =  float(self.txt_pump_efficiency.text())
        self.params.energy.energy_price = float(self.txt_energy_price.text())
        self.params.energy.price_pattern = int(self.txt_price_pattern.text())
        self.params.energy.demand_charge = float(self.txt_demand_charge.text())

        self.setVisible(False)

