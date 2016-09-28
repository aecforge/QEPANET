from PyQt4.QtGui import QDialog, QFrame, QTabWidget, QPushButton, QHBoxLayout, QVBoxLayout, QWidget, QApplication,\
    QFrame, QSizePolicy, QCheckBox, QGroupBox, QSpacerItem
from PyQt4.QtCore import Qt
from graph_canvas import StaticMplCanvas
import sys

min_width = 600
min_height = 600


class OutputAnalyserDialog(QTabWidget):

    def __init__(self, parent, params):

        QTabWidget.__init__(self, parent)

        # QDialog.__init__(self, parent)

        self.parent = parent
        self.params = params

        self.setMinimumWidth(min_width)
        self.setMinimumHeight(min_height)

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

        self.chk_node_flow = QCheckBox('Flow')
        lay_grb_links.addWidget(self.chk_node_flow)

        self.chk_link_velocity = QCheckBox('Velocity')
        lay_grb_links.addWidget(self.chk_link_velocity)

        self.chk_link_headloss = QCheckBox('Headloss')
        lay_grb_links.addWidget(self.chk_link_headloss)

        self.chk_link_quality = QCheckBox('Quality')
        lay_grb_links.addWidget(self.chk_link_quality)

        fra_graphs_left_lay.addWidget(self.grb_links)

        self.spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        fra_graphs_left_lay.addItem(self.spacer)

        tab_graphs_lay.addWidget(self.fra_graphs_left)

        # Right frame
        self.fra_graphs_right = QFrame()
        self.fra_graphs_right.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        fra_graphs_right_lay = QVBoxLayout(self.fra_graphs_right)

        self.static_canvas = StaticMplCanvas(self.fra_graphs_right, width=5, height=4, dpi=100)

        tab_graphs_lay.addWidget(self.fra_graphs_right)

        # lay.addWidget(self.button)
        self.addTab(self.tab_graphs, 'Graphs')

        # Maps tab
        self.tab_maps = QWidget()
        # lay = QVBoxLayout(self.tab_graphs)
        # lay.addWidget(self.button)
        self.addTab(self.tab_maps, 'Maps')

        # # Add to main
        # fra_main_lay = QVBoxLayout(self)
        # fra_main_lay.setContentsMargins(0, 0, 0, 0)
        # fra_main_lay.addWidget(self.fra_form)
        # fra_main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):
        pass

    def initialize(self):

        self.chk_node_demand.setEnabled(False)
        self.chk_node_head.setEnabled(False)
        self.chk_node_pressure.setEnabled(False)
        self.chk_node_quality.setEnabled(False)

        self.grb_links.setEnabled(False)
        self.chk_node_flow.setEnabled(False)
        self.chk_link_velocity.setEnabled(False)
        self.chk_link_headloss.setEnabled(False)
        self.chk_link_quality.setEnabled(False)

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):
        pass
        # self.params.report.status = self.cbo_status.itemData(self.cbo_status.currentIndex())
        # self.params.report.summary = self.cbo_summary.itemData(self.cbo_summary.currentIndex())
        # self.params.report.energy = self.cbo_energy.itemData(self.cbo_energy.currentIndex())
        # self.params.report.nodes = self.cbo_nodes.itemData(self.cbo_nodes.currentIndex())
        # self.params.report.links = self.cbo_links.itemData(self.cbo_links.currentIndex())
        #
        # self.setVisible(False)

app = QApplication(sys.argv)
o = OutputAnalyserDialog(None, None)
o.show()
sys.exit(app.exec_())