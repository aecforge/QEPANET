from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
# from qgis.gui import QgsMapTool
from graphs import StaticMplCanvas
from ..tools.parameters import Parameters, ConfigFile
from ..model.network import Junction, Reservoir, Tank, Pipe, Pump, Valve
from ..model.binary_out_reader import BinaryOutputReader, OutputParamCodes
from ..model.options_report import Options, Quality
from ..tools.select_tool import SelectTool
import sys

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
        self.btn_out_file.pressed.connect(self.btn_out_file_pressed)
        fra_out_file_lay.addWidget(self.lbl_out_file)
        fra_out_file_lay.addWidget(self.txt_out_file)
        fra_out_file_lay.addWidget(self.btn_out_file)

        self.tab_widget = QTabWidget(self)

        # Graphs tab
        self.tab_graphs = QWidget()
        tab_graphs_lay = QHBoxLayout(self.tab_graphs)

        # Left frame
        self.fra_graphs_left = QFrame()
        self.fra_graphs_left.setMaximumWidth(100)
        fra_graphs_left_lay = QVBoxLayout(self.fra_graphs_left)

        self.btn_sel_element = QPushButton('Pick')
        self.btn_sel_element.pressed.connect(self.btn_sel_element_pressed)
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

        self.btn_draw = QPushButton('Draw')
        self.btn_draw.pressed.connect(self.draw_graphs)
        fra_graphs_left_lay.addWidget(self.btn_draw)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        fra_graphs_left_lay.addItem(self.spacer)

        tab_graphs_lay.addWidget(self.fra_graphs_left)

        # Right frame
        self.fra_graphs_right = QFrame()
        # self.fra_graphs_right.setPalette(QPalette(Qt.black))
        # self.fra_graphs_right.setAutoFillBackground(True)
        fra_graphs_right_lay = QVBoxLayout(self.fra_graphs_right)
        fra_graphs_right_lay.setContentsMargins(0, 0, 0, 0)

        self.static_canvas = StaticMplCanvas(self.fra_graphs_right, width=5, height=4, dpi=100)
        fra_graphs_right_lay.addWidget(self.static_canvas)

        tab_graphs_lay.addWidget(self.fra_graphs_right)

        # lay.addWidget(self.button)
        self.tab_widget.addTab(self.tab_graphs, 'Graphs')

        # Maps tab
        self.tab_maps = QWidget()
        # lay = QVBoxLayout(self.tab_graphs)
        # lay.addWidget(self.button)
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

    def btn_out_file_pressed(self):
        config_file = ConfigFile(Parameters.config_file_path)
        out_file = QFileDialog.getOpenFileName(
            self,
            'Select out file',
            config_file.get_last_out_file(),
            'Out files (*.out)')

        if out_file is None:
            return

        config_file.set_last_out_file(out_file)
        self.txt_out_file.setText(out_file)
        self.read_outputs()

    def initialize(self):

        self.grb_nodes.setEnabled(False)
        self.grb_links.setEnabled(False)

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

        # self.output_reader = BinaryOutputReader('D:/Progetti/2015/2015_13_TN_EPANET/04_Implementation/INP_Test/Test_cases/5/5.out')
        try:
            self.output_reader = BinaryOutputReader(self.txt_out_file.text())
        except:
            self.iface.messageBar().pushWarning(
                Parameters.plug_in_name,
                'Error while reading output file.')  # TODO: softcode
            self.output_reader = None
            self.txt_out_file.setText('')

    def btn_sel_element_pressed(self):

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
                        self.output_reader.link_headloss_d[element_id],
                        Options.units_diameter_tanks[self.params.options.units]]
                ys_d_d[OutputParamCodes.LINK_HEADLOSS] = ys_d

            if self.chk_link_quality.isChecked():
                params_count += 1
                ys_d = {}
                for element_id in self.element_ids_links:
                    ys_d[element_id] = [
                        self.output_reader.link_qualities_d[element_id],
                        '?']
                ys_d_d[OutputParamCodes.LINK_QUALITY] = ys_d

        if ys_d_d:
            self.static_canvas.draw_output_line(xs, ys_d_d, params_count)

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):
        pass


# class PickTool(QgsMapTool):
#
#     def __init__(self, data_dock, params):
#         QgsMapTool.__init__(self, data_dock.iface.mapCanvas())

# app = QApplication(sys.argv)
# o = OutputAnalyserDialog(None, None)
# o.show()
# sys.exit(app.exec_())