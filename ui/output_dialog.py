from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
# from qgis.gui import QgsMapTool
from graphs import StaticMplCanvas
from ..tools.parameters import Parameters
from ..model.binary_out_reader import BinaryOutputReader, OutputParamCodes
from ..model.options_report import Options, Quality
import sys

min_width = 600
min_height = 400


class OutputAnalyserDialog(QDialog):

    def __init__(self, parent, params):

        QDialog.__init__(self, parent)

        self.parent = parent
        self.params = params

        self.output_reader = None

        # self.setMinimumWidth(min_width)
        # self.setMinimumHeight(min_height)
        fra_main_lay = QVBoxLayout(self)

        self.tab_widget = QTabWidget()

        # Graphs tab
        self.tab_graphs = QWidget()
        tab_graphs_lay = QHBoxLayout(self.tab_graphs)

        # Left frame
        self.fra_graphs_left = QFrame()
        self.fra_graphs_left.setMaximumWidth(100)
        fra_graphs_left_lay = QVBoxLayout(self.fra_graphs_left)

        self.btn_sel_element = QPushButton('Pick')
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
        self.btn_draw.pressed.connect(self.draw_charts)
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
        # fra_main_lay = QVBoxLayout(self)
        # fra_main_lay.setContentsMargins(0, 0, 0, 0)
        # fra_main_lay.addWidget(self.fra_form)
        # fra_main_lay.addWidget(self.fra_buttons)
        fra_main_lay.addWidget(self.tab_widget)

        self.setup()
        self.initialize()
        self.read_outputs()

        # Set size
        self.setMinimumWidth(self.tab_graphs.width())
        self.setMinimumHeight(self.tab_graphs.height())

    def setup(self):

        self.btn_sel_element.pressed.connect(self.btn_sel_element_pressed)

    def initialize(self):

        self.chk_node_demand.setEnabled(False)
        self.chk_node_head.setEnabled(False)
        self.chk_node_pressure.setEnabled(False)
        self.chk_node_quality.setEnabled(False)

        self.grb_links.setEnabled(False)
        self.chk_link_flow.setEnabled(False)
        self.chk_link_velocity.setEnabled(False)
        self.chk_link_headloss.setEnabled(False)
        self.chk_link_quality.setEnabled(False)

    def read_outputs(self):

        self.output_reader = BinaryOutputReader('D:/Progetti/2015/2015_13_TN_EPANET/04_Implementation/INP_Test/Test_cases/5/5.out')

    def btn_sel_element_pressed(self):

        # Find clicked element (feature and layer)

        # sel_feat = None
        # sel_lay = None
        #
        # is_node = False
        # if sel_lay == Parameters.junctions_vlay or sel_lay == Parameters.reservoirs_vlay or sel_lay == Parameters.tanks_vlay:
        #     is_node = True

        self.element_ids = ['N5', 'N2']

        is_node = True

        self.chk_node_demand.setEnabled(is_node)
        self.chk_node_head.setEnabled(is_node)
        self.chk_node_pressure.setEnabled(is_node)
        self.chk_node_quality.setEnabled(is_node)

        self.chk_link_flow.setEnabled(not is_node)
        self.chk_link_velocity.setEnabled(not is_node)
        self.chk_link_headloss.setEnabled(not is_node)
        self.chk_link_quality.setEnabled(not is_node)

        self.draw_charts()

    def draw_charts(self):

        # Build values dictionaries
        xs = self.output_reader.report_times
        ys_d_d = {}

        # Nodes
        if self.chk_node_demand.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.node_demands_d[element_id],
                    self.params.options.flow_units]
            ys_d_d[OutputParamCodes.NODE_DEMAND] = ys_d

        if self.chk_node_head.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.node_heads_d[element_id],
                    Options.units_diameter_tanks[self.params.options.units]]
            ys_d_d[OutputParamCodes.NODE_HEAD] = ys_d

        if self.chk_node_pressure.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.node_pressures_d[element_id],
                    Options.units_pressure[self.params.options.units]]
            ys_d_d[OutputParamCodes.NODE_PRESSURE] = ys_d

        if self.chk_node_quality.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.node_qualities_d[element_id],
                    Quality.quality_units_text[self.params.options.quality.mass_units]]
            ys_d_d[OutputParamCodes.NODE_QUALITY] = ys_d

        # Links
        if self.chk_link_flow.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.link_flows_d[element_id],
                    self.params.options.flow_units]
            ys_d_d[OutputParamCodes.LINK_FLOW] = ys_d

        if self.chk_link_velocity.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.link_velocities_d[element_id],
                    Options.units_velocity[self.params.units]]
            ys_d_d[OutputParamCodes.LINK_VELOCITY] = ys_d

        if self.chk_link_headloss.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.link_headloss_d[element_id],
                    Options.units_diameter_tanks[self.params.options.units]]
            ys_d_d[OutputParamCodes.LINK_HEADLOSS] = ys_d

        if self.chk_link_quality.isChecked():
            ys_d = {}
            for element_id in self.element_ids:
                ys_d[element_id] = [
                    self.output_reader.link_qualities_d[element_id],
                    '?']
            ys_d_d[OutputParamCodes.LINK_QUALITY] = ys_d

        if ys_d_d:
            self.static_canvas.draw_output_line(xs, ys_d_d)

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