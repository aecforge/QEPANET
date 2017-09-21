from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
# from qgis.gui import QgsMapTool
from graphs import StaticMplCanvas
from ..geo_utils.renderer import *
from ..geo_utils.utils import *
from ..tools.parameters import Parameters, ConfigFile
from ..model.network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from ..model.binary_out_reader import BinaryOutputReader, OutputParamCodes
from ..model.options_report import Options, Quality
from ..tools.select_tool import SelectTool
from ..tools.data_stores import *
import codecs
import math

min_width = 600
min_height = 400


class OutputAnalyserDialog(QDialog):

    def __init__(self, iface, parent, params):

        QDialog.__init__(self, parent)

        self.iface = iface
        self.parent = parent
        self.params = params

        self.output_reader = None
        self.tool = None
        self.element_ids_nodes = None
        self.element_ids_links = None

        self.nodes_lay = None
        self.links_lay = None

        self.setWindowTitle(Parameters.plug_in_name)

        # Selection changed listeners
        self.params.junctions_vlay.selectionChanged.connect(self.feature_sel_changed)
        self.params.reservoirs_vlay.selectionChanged.connect(self.feature_sel_changed)
        self.params.tanks_vlay.selectionChanged.connect(self.feature_sel_changed)
        self.params.pipes_vlay.selectionChanged.connect(self.feature_sel_changed)
        self.params.pumps_vlay.selectionChanged.connect(self.feature_sel_changed)
        self.params.valves_vlay.selectionChanged.connect(self.feature_sel_changed)

        # self.setMinimumWidth(min_width)
        # self.setMinimumHeight(min_height)
        fra_main_lay = QVBoxLayout(self)

        self.fra_out_file = QFrame(self)
        fra_out_file_lay = QHBoxLayout(self.fra_out_file)
        self.lbl_out_file = QLabel('Simulation output file:')
        self.txt_out_file = QLineEdit('')
        self.txt_out_file.setReadOnly(True)
        self.btn_out_file = QToolButton()
        self.btn_out_file.setText('...')
        self.btn_out_file.clicked.connect(self.btn_out_file_clicked)
        fra_out_file_lay.addWidget(self.lbl_out_file)
        fra_out_file_lay.addWidget(self.txt_out_file)
        fra_out_file_lay.addWidget(self.btn_out_file)

        self.tab_widget = QTabWidget(self)

        # Graphs tab ---------------------------------------------------------------------------------------------------
        self.tab_graphs = QWidget()
        tab_graphs_lay = QHBoxLayout(self.tab_graphs)

        # Left frame
        self.fra_graphs_left = QFrame()
        self.fra_graphs_left.setMaximumWidth(100)
        fra_graphs_left_lay = QVBoxLayout(self.fra_graphs_left)

        self.btn_sel_element = QPushButton('Pick')
        self.btn_sel_element.clicked.connect(self.btn_sel_element_clicked)
        fra_graphs_left_lay.addWidget(self.btn_sel_element)

        # Nodes
        self.grb_nodes = QGroupBox(u'Nodes')
        lay_grb_nodes = QVBoxLayout(self.grb_nodes)

        self.chk_node_demand = QCheckBox('Demand')
        lay_grb_nodes.addWidget(self.chk_node_demand)

        self.chk_node_head =  QCheckBox('Head')
        lay_grb_nodes.addWidget(self.chk_node_head)

        self.chk_node_pressure = QCheckBox('Pressure')
        lay_grb_nodes.addWidget(self.chk_node_pressure)

        self.chk_node_quality = QCheckBox('Quality')
        lay_grb_nodes.addWidget(self.chk_node_quality)

        fra_graphs_left_lay.addWidget(self.grb_nodes)

        # Links
        self.grb_links = QGroupBox(u'Links')
        lay_grb_links = QVBoxLayout(self.grb_links)

        self.chk_link_flow = QCheckBox('Flow')
        lay_grb_links.addWidget(self.chk_link_flow)

        self.chk_link_velocity = QCheckBox('Velocity')
        lay_grb_links.addWidget(self.chk_link_velocity)

        self.chk_link_headloss = QCheckBox('Headloss')
        lay_grb_links.addWidget(self.chk_link_headloss)

        self.chk_link_quality = QCheckBox('Quality')
        lay_grb_links.addWidget(self.chk_link_quality)

        fra_graphs_left_lay.addWidget(self.grb_links)

        self.btn_draw_graph = QPushButton('Draw')
        self.btn_draw_graph.clicked.connect(self.draw_graphs)
        fra_graphs_left_lay.addWidget(self.btn_draw_graph)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        fra_graphs_left_lay.addItem(self.spacer)

        tab_graphs_lay.addWidget(self.fra_graphs_left)

        # Right frame
        self.fra_graphs_right = QFrame()
        fra_graphs_right_lay = QVBoxLayout(self.fra_graphs_right)
        fra_graphs_right_lay.setContentsMargins(0, 0, 0, 0)

        self.static_canvas = StaticMplCanvas(self.fra_graphs_right, width=5, height=4, dpi=100)
        fra_graphs_right_lay.addWidget(self.static_canvas)

        tab_graphs_lay.addWidget(self.fra_graphs_right)

        # lay.addWidget(self.button)
        self.tab_widget.addTab(self.tab_graphs, 'Graphs')

        # Maps tab -----------------------------------------------------------------------------------------------------
        self.tab_maps = QWidget()
        tab_maps_lay = QHBoxLayout(self.tab_maps)

        # Left frame
        self.fra_maps_left = QFrame()
        self.fra_maps_left.setMaximumWidth(200)
        fra_maps_left_lay = QVBoxLayout(self.fra_maps_left)

        self.grb_maps = QGroupBox(u'Variable')
        grb_maps_lay = QVBoxLayout(self.grb_maps)

        self.rad_maps_node_demand = QRadioButton(u'Node demand')
        grb_maps_lay.addWidget(self.rad_maps_node_demand)

        self.rad_maps_node_head = QRadioButton(u'Node head')
        grb_maps_lay.addWidget(self.rad_maps_node_head)

        self.rad_maps_node_pressure = QRadioButton(u'Node pressure')
        grb_maps_lay.addWidget(self.rad_maps_node_pressure)

        self.rad_maps_node_quality = QRadioButton(u'Node quality')
        grb_maps_lay.addWidget(self.rad_maps_node_quality)

        self.rad_maps_link_flow = QRadioButton(u'Link flow')
        grb_maps_lay.addWidget(self.rad_maps_link_flow)

        self.rad_maps_link_velocity = QRadioButton(u'Link velocity')
        grb_maps_lay.addWidget(self.rad_maps_link_velocity)

        self.rad_maps_link_headloss = QRadioButton(u'Link headloss')
        grb_maps_lay.addWidget(self.rad_maps_link_headloss)

        self.rad_maps_link_quality = QRadioButton(u'Link quality')
        grb_maps_lay.addWidget(self.rad_maps_link_quality)

        fra_maps_left_lay.addWidget(self.grb_maps)
        fra_maps_left_lay.addItem(self.spacer)

        tab_maps_lay.addWidget(self.fra_maps_left)

        # Right maps frame
        self.fra_maps_right = QFrame()
        fra_maps_right_lay = QVBoxLayout(self.fra_maps_right)

        self.fra_maps_right_time = QFrame()
        fra_maps_right_time_lay = QFormLayout(self.fra_maps_right_time)

        self.lbl_map_times = QLabel(u'Period [h]:')
        self.cbo_map_times = QComboBox()
        fra_maps_right_time_lay.addRow(self.lbl_map_times, self.cbo_map_times)
        fra_maps_right_lay.addWidget(self.fra_maps_right_time)

        self.btn_draw_map = QPushButton(u'Draw map')
        self.btn_draw_map.clicked.connect(self.draw_maps)
        fra_maps_right_lay.addWidget(self.btn_draw_map)

        fra_maps_right_lay.addItem(self.spacer)

        tab_maps_lay.addWidget(self.fra_maps_right)

        self.tab_widget.addTab(self.tab_maps, 'Maps')

        # # Add to main
        fra_main_lay.addWidget(self.fra_out_file)
        fra_main_lay.addWidget(self.tab_widget)

        self.setup()
        self.initialize()
        # self.read_outputs()

        # Set size
        self.setMinimumWidth(self.tab_graphs.width())
        self.setMinimumHeight(self.tab_graphs.height())

    def setup(self):
        pass

    def btn_out_file_clicked(self):
        config_file = ConfigFile(Parameters.config_file_path)
        out_file = QFileDialog.getOpenFileName(
            self,
            'Select out file',
            config_file.get_last_out_file(),
            'Out files (*.out)')

        if out_file is None or out_file == '':
            return

        config_file.set_last_out_file(out_file)
        self.txt_out_file.setText(out_file)
        self.read_outputs()
        if self.output_reader is None:
            return

        # Fill times combo
        self.cbo_map_times.clear()
        for period_s in self.output_reader.period_results.iterkeys():

            text = self.seconds_to_string(
                period_s,
                self.output_reader.sim_duration_secs,
                self.output_reader.report_time_step_secs)
            self.cbo_map_times.addItem(text, period_s)

    def initialize(self):

        # Graphs
        self.grb_nodes.setEnabled(False)
        self.grb_links.setEnabled(False)

        # Maps
        self.rad_maps_node_demand.setChecked(True)

    def feature_sel_changed(self):

        is_nodes = False
        sel_junctions = self.params.junctions_vlay.selectedFeatureCount()
        sel_reservoirs = self.params.reservoirs_vlay.selectedFeatureCount()
        sel_tanks = self.params.tanks_vlay.selectedFeatureCount()
        if sel_junctions > 0 or sel_reservoirs > 0 or sel_tanks > 0:
            is_nodes = True
        self.grb_nodes.setEnabled(is_nodes)

        is_links = False
        sel_pipes = self.params.pipes_vlay.selectedFeatureCount()
        sel_pumps = self.params.pumps_vlay.selectedFeatureCount()
        sel_valves = self.params.valves_vlay.selectedFeatureCount()
        if sel_pipes > 0 or sel_pumps > 0 or sel_valves > 0:
            is_links = True
        self.grb_links.setEnabled(is_links)

    def read_outputs(self):

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.output_reader = BinaryOutputReader()
            self.output_reader.read(self.txt_out_file.text())
            QApplication.restoreOverrideCursor()

            # Check if output compatible with loaded project
            compatible = True
            out_nodes_nr = self.output_reader.nodes_nr
            out_tanks_reservs_nr = self.output_reader.tanks_reservs_nr
            out_juncts_nr = out_nodes_nr - out_tanks_reservs_nr

            out_links_nr = self.output_reader.links_nr
            out_pumps_nr = self.output_reader.pumps_nr
            out_valves_nr = self.output_reader.valves_nr
            out_pipes_nr = out_links_nr - out_pumps_nr - out_valves_nr

            if out_juncts_nr != self.params.junctions_vlay.featureCount():
                compatible = False
            if out_tanks_reservs_nr != (self.params.reservoirs_vlay.featureCount() + self.params.tanks_vlay.featureCount()):
                compatible = False
            if out_pipes_nr != self.params.pipes_vlay.featureCount():
                compatible = False
            if out_valves_nr != self.params.valves_vlay.featureCount():
                compatible = False
            if out_pumps_nr != self.params.pumps_vlay.featureCount():
                compatible = False

            if not compatible:
                message = 'The out file appears to incompatible with the actual project layers.'
                QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    message,
                    QMessageBox.Ok)

                self.output_reader = None
                self.txt_out_file.setText('')

            else:
                # Message after reading completed
                message = 'Out file loaded: ' + str(out_nodes_nr) + ' nodes, ' + str(out_links_nr) + ' links found.'

                # Clear refs to output layer
                self.params.out_lay_node_demand = None
                self.params.out_lay_node_head = None
                self.params.out_lay_node_pressure = None
                self.params.out_lay_node_quality = None
                self.params.out_lay_link_flow = None
                self.params.out_lay_link_velocity = None
                self.params.out_lay_link_headloss = None
                self.params.out_lay_link_quality = None

                QMessageBox.information(
                    self,
                    Parameters.plug_in_name,
                    message,
                    QMessageBox.Ok)

        finally:
            # self.iface.messageBar().pushWarning(
            #     Parameters.plug_in_name,
            #     'Error while reading output file.')  # TODO: softcode
            self.output_reader = None
            self.txt_out_file.setText('')
            QApplication.restoreOverrideCursor()

    def btn_sel_element_clicked(self):

        if self.output_reader is None:
            self.iface.messageBar().pushWarning(
                Parameters.plug_in_name,
                'Please select the simulation out file.')  # TODO: softcode
            return

        self.tool = SelectTool(self, self.params)
        self.iface.mapCanvas().setMapTool(self.tool)

        cursor = QCursor()
        cursor.setShape(Qt.ArrowCursor)
        self.iface.mapCanvas().setCursor(cursor)

    def draw_graphs(self):

        # Get selected features
        self.element_ids_nodes = []
        for junction_feat in self.params.junctions_vlay.selectedFeatures():
            self.element_ids_nodes.append(junction_feat.attribute(Junction.field_name_eid))
        for reservoir_feat in self.params.reservoirs_vlay.selectedFeatures():
            self.element_ids_nodes.append(reservoir_feat.attribute(Reservoir.field_name_eid))
        for tank_feat in self.params.tanks_vlay.selectedFeatures():
            self.element_ids_nodes.append(tank_feat.attribute(Tank.field_name_eid))

        self.element_ids_links = []
        for pipe_feat in self.params.pipes_vlay.selectedFeatures():
            self.element_ids_links.append(pipe_feat.attribute(Pipe.field_name_eid))
        for pump_feat in self.params.pumps_vlay.selectedFeatures():
            self.element_ids_links.append(pump_feat.attribute(Pump.field_name_eid))
        for valve_feat in self.params.valves_vlay.selectedFeatures():
            self.element_ids_links.append(valve_feat.attribute(Valve.field_name_eid))

        # Build values dictionaries
        xs = self.output_reader.report_times
        ys_d_d = {}
        params_count = 0

        # Nodes
        if self.grb_nodes.isEnabled():
            if self.chk_node_demand.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_nodes:
                    ys_d[element_id] = [
                        self.output_reader.node_demands_d[element_id],
                        self.params.options.flow_units]
                ys_d_d[OutputParamCodes.NODE_DEMAND] = ys_d

            if self.chk_node_head.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_nodes:
                    ys_d[element_id] = [
                        self.output_reader.node_heads_d[element_id],
                        Options.units_diameter_tanks[self.params.options.units]]
                ys_d_d[OutputParamCodes.NODE_HEAD] = ys_d

            if self.chk_node_pressure.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_nodes:
                    ys_d[element_id] = [
                        self.output_reader.node_pressures_d[element_id],
                        Options.units_pressure[self.params.options.units]]
                ys_d_d[OutputParamCodes.NODE_PRESSURE] = ys_d

            if self.chk_node_quality.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_nodes:
                    ys_d[element_id] = [
                        self.output_reader.node_qualities_d[element_id],
                        Quality.quality_units_text[self.params.options.quality.mass_units]]
                ys_d_d[OutputParamCodes.NODE_QUALITY] = ys_d

        # Links
        if self.grb_links.isEnabled():
            if self.chk_link_flow.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_links:
                    ys_d[element_id] = [
                        self.output_reader.link_flows_d[element_id],
                        self.params.options.flow_units]
                ys_d_d[OutputParamCodes.LINK_FLOW] = ys_d

            if self.chk_link_velocity.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_links:
                    ys_d[element_id] = [
                        self.output_reader.link_velocities_d[element_id],
                        Options.units_velocity[self.params.options.units]]
                ys_d_d[OutputParamCodes.LINK_VELOCITY] = ys_d

            if self.chk_link_headloss.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_links:
                    ys_d[element_id] = [
                        self.output_reader.link_headlosses_d[element_id],
                        Options.units_diameter_tanks[self.params.options.units]]
                ys_d_d[OutputParamCodes.LINK_HEADLOSS] = ys_d

            if self.chk_link_quality.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_links:
                    ys_d[element_id] = [
                        self.output_reader.link_qualities_d[element_id],
                        Quality.quality_units_text[self.params.options.quality.mass_units]]
                ys_d_d[OutputParamCodes.LINK_QUALITY] = ys_d

        if ys_d_d:
            self.static_canvas.draw_output_line(xs, ys_d_d, params_count)

    def draw_maps(self):
        """
        Draws layers with all the attributes
        :return:
        """

        report_time = self.cbo_map_times.itemText(self.cbo_map_times.currentIndex())

        if self.rad_maps_node_demand.isChecked():  # -------------------------------------------------------------------
            lay_name = 'Node demand'
            lay_id = self.draw_map(LayerType.NODE, self.params.out_lay_node_demand_id, lay_name,
                                   self.output_reader.node_demands_d, report_time)
            self.params.out_lay_node_demand_id = lay_id

        elif self.rad_maps_node_head.isChecked():
            lay_name = 'Node head'
            lay_id = self.draw_map(LayerType.NODE, self.params.out_lay_node_head_id, lay_name,
                                   self.output_reader.node_heads_d, report_time)
            self.params.out_lay_node_head_id = lay_id

        elif self.rad_maps_node_pressure.isChecked():
            lay_name = 'Node pressure'
            lay_id = self.draw_map(LayerType.NODE, self.params.out_lay_node_pressure_id, lay_name,
                                   self.output_reader.node_pressures_d, report_time)
            self.params.out_lay_node_pressure_id = lay_id

        elif self.rad_maps_node_quality.isChecked():
            lay_name = 'Node quality'
            lay_id = self.draw_map(LayerType.NODE, self.params.out_lay_node_quality_id, lay_name,
                                   self.output_reader.node_qualities_d, report_time)
            self.params.out_lay_node_quality_id = lay_id

        elif self.rad_maps_link_flow.isChecked():  # -------------------------------------------------------------------
            lay_name = 'Link flow'
            lay_id = self.draw_map(LayerType.LINK, self.params.out_lay_link_flow_id, lay_name,
                                   self.output_reader.link_flows_d, report_time)
            self.params.out_lay_link_flow_id = lay_id

        elif self.rad_maps_link_velocity.isChecked():
            lay_name = 'Link velocity'
            lay_id = self.draw_map(LayerType.LINK, self.params.out_lay_link_velocity_id, lay_name,
                                   self.output_reader.link_velocities_d, report_time)
            self.params.out_lay_link_velocity_id = lay_id

        elif self.rad_maps_link_headloss.isChecked():
            lay_name = 'Link headloss'
            lay_id = self.draw_map(LayerType.LINK, self.params.out_lay_link_headloss_id, lay_name,
                                   self.output_reader.link_headlosses_d, report_time)
            self.params.out_lay_link_headloss_id = lay_id

        elif self.rad_maps_link_quality.isChecked():
            lay_name = 'Link quality'
            lay_id = self.draw_map(LayerType.LINK, self.params.out_lay_link_quality_id, lay_name,
                                   self.output_reader.link_qualities_d, report_time)
            self.params.out_lay_link_quality_id = lay_id

    def draw_map(self, lay_type, lay_id, lay_name, dataset, report_time):

        try:
            QApplication.setOverrideCursor(Qt.WaitCursor)

            lay_name += ' ' + report_time

            lay = LayerUtils.get_lay_from_id(lay_id)
            if lay is None:
                if lay_type == LayerType.NODE:
                    lay = self.create_out_node_layer(lay_name, dataset)
                elif lay_type == LayerType.LINK:
                    lay = self.create_out_link_layer(lay_name, dataset)
                lay_id = lay.id()
                QgsMapLayerRegistry.instance().addMapLayer(lay)
                self.params.out_layers.append(lay)
            else:
                lay.setLayerName(lay_name)

            # text = self.seconds_to_string(
            #     report_time,
            #     self.output_reader.sim_duration_secs,
            #     self.output_reader.report_time_step_secs)

            lay.setRendererV2(RampRenderer.get_renderer(lay, report_time))
            lay.triggerRepaint()

            QApplication.restoreOverrideCursor()

        finally:
            QApplication.restoreOverrideCursor()

        return lay_id

    def btn_cancel_clicked(self):
        self.setVisible(False)

    def btn_ok_clicked(self):
        pass

    def create_out_node_layer(self, lay_name, values_d):
        return self.create_out_layer(lay_name, values_d, LayerType.NODE)

    def create_out_link_layer(self, lay_name, values_d):
        return self.create_out_layer(lay_name, values_d, LayerType.LINK)

    def create_out_layer(self, lay_name, values_d, lay_type):
        field_name_vars = []
        periods = self.output_reader.period_results.keys()
        for period_s in periods:
            text = self.seconds_to_string(
                period_s,
                self.output_reader.sim_duration_secs,
                self.output_reader.report_time_step_secs)
            field_name_vars.append(text)

        if lay_type == LayerType.NODE:
            new_lay = MemoryDS.create_nodes_lay(self.params, field_name_vars, lay_name, self.params.crs)
        elif lay_type == LayerType.LINK:
            new_lay = MemoryDS.create_links_lay(self.params, field_name_vars, lay_name, self.params.crs)

        # Add attributes
        for feat in new_lay.getFeatures():
            new_lay.startEditing()
            eid = feat.attribute(Node.field_name_eid)
            values = values_d[eid]

            for p in range(len(periods)):
                text = self.seconds_to_string(
                    periods[p],
                    self.output_reader.sim_duration_secs,
                    self.output_reader.report_time_step_secs)
                feat.setAttribute(text, values[p])
                new_lay.updateFeature(feat)

            new_lay.commitChanges()

        return new_lay

    def seconds_to_string(self, period_s, duration_s, interval_s):

        day = int(math.floor(period_s / 86400))
        hour = period_s / 3600 - day * 24
        minute = period_s / 60 - day * 24 * 60 - hour * 60
        second = period_s - day * 86400 - hour * 3600 - minute * 60

        text = ''
        if duration_s >= 86400:
            # We need days
            text += str(day) + 'd'

        if duration_s >= 3600:
            # We need hours
            text += '{:02}'.format(hour) + 'H'

        text += '{:02}'.format(minute) + 'm'

        if second > 0:
            text += '{:02}'.format(second) + 's'

        return text


class LayerType:
    def __init__(self):
        pass

    NODE = 0
    LINK = 1


class LogDialog(QDialog):

    def __init__(self, parent, rpt_file_path):
        self.rpt_file_path = rpt_file_path

        QDialog.__init__(self, parent)

        self.setWindowTitle('Log: ' + self.rpt_file_path)

        main_lay = QVBoxLayout(self)

        self.txt_log = QPlainTextEdit(self)
        self.txt_log.setMinimumWidth(500)
        self.txt_log.setMinimumHeight(300)
        main_lay.addWidget(self.txt_log)

        self.btn_close = QPushButton('Close')
        self.btn_close.clicked.connect(self.close_dialog)
        main_lay.addWidget(self.btn_close)

        self.fill_txt()

    def close_dialog(self):
        self.close()

    def fill_txt(self):
        with codecs.open(self.rpt_file_path, 'r', encoding='UTF-8') as inp_f:
            lines = inp_f.read().splitlines()

        for line in lines:
            self.txt_log.appendPlainText(line.replace('\b', ''))

        # Scroll up
        self.txt_log.moveCursor(QTextCursor.Start)
        self.txt_log.ensureCursorVisible()