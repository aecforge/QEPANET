from ..tools.parameters import Parameters
from graphs import StaticMplCanvas
from PyQt4 import QtGui, QtCore


class PatternsDialog(QtGui.QDialog):

    def __init__(self, parent):
        QtGui.QDialog.__init__(self, parent)
        main_lay = QtGui.QVBoxLayout(self)

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowTitle('Patterns')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # File
        self.lbl_file = QtGui.QLabel('Pattern file:')
        self.fra_file = QtGui.QFrame()
        self.fra_file.setContentsMargins(0, 0, 0, 0)
        fra_file_lay = QtGui.QHBoxLayout(self.fra_file)
        self.txt_file = QtGui.QLineEdit(Parameters.pattern_file)
        self.txt_file.setReadOnly(True)
        self.txt_file.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.txt_file.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Minimum)
        fra_file_lay.addWidget(self.txt_file)
        self.btn_file = QtGui.QPushButton('Change')  # TODO: softcode
        self.btn_file.clicked.connect(self.select_file)
        fra_file_lay.addWidget(self.btn_file)
        fra_file_lay.setContentsMargins(0, 0, 0, 0)

        # Patterns
        self.lbl_patterns = QtGui.QLabel('Patterns:')
        self.lst_patterns = QtGui.QListWidget()

        # Form
        self.fra_form = QtGui.QFrame()
        fra_form1_lay = QtGui.QFormLayout(self.fra_form)
        fra_form1_lay.setContentsMargins(0, 0, 0, 0)
        fra_form1_lay.addRow(self.lbl_file, self.fra_file)
        fra_form1_lay.addRow(self.lbl_patterns, self.lst_patterns)

        # Buttons
        self.fra_buttons = QtGui.QFrame()
        # self.fra_buttons.setFrameShape(QtGui.QFrame.Box)
        # self.fra_buttons.setContentsMargins(0, 0, 0, 0)
        fra_buttons_lay = QtGui.QHBoxLayout(self.fra_buttons)
        fra_buttons_lay.setContentsMargins(0, 0, 0, 0)
        self.btn_save = QtGui.QPushButton('Save')  # TODO: softcode
        self.btn_save.clicked.connect(self.save_pattern)
        fra_buttons_lay.addWidget(self.btn_save)
        self.btn_del = QtGui.QPushButton('Delete')  # TODO: softcode
        self.btn_del.clicked.connect(self.del_pattern)
        fra_buttons_lay.addWidget(self.btn_del)

        # ID
        self.lbl_id = QtGui.QLabel('ID:')
        self.txt_id = QtGui.QLineEdit()
        self.txt_id.setSizePolicy(QtGui.QSizePolicy.Maximum, QtGui.QSizePolicy.MinimumExpanding);
        self.lbl_desc = QtGui.QLabel('Desc.:')
        self.txt_desc = QtGui.QLineEdit()

        self.fra_id = QtGui.QFrame()
        fra_id_lay = QtGui.QHBoxLayout(self.fra_id)
        fra_id_lay.addWidget(self.lbl_id)
        fra_id_lay.addWidget(self.txt_id)
        fra_id_lay.addWidget(self.lbl_desc)
        fra_id_lay.addWidget(self.txt_desc)

        # Table form
        self.table = QtGui.QTableWidget(self)
        rows_nr = 2
        cols_nr = 24
        self.table.setRowCount(rows_nr)
        self.table.setColumnCount(cols_nr)
        self.table.horizontalHeader().setVisible(False)

        row_height = self.table.rowHeight(0);
        table_height = (rows_nr * row_height) + self.table.horizontalHeader().height() + 2 * self.table.frameWidth()
        self.table.setMinimumHeight(table_height + 10)
        self.table.setMaximumHeight(table_height + 10)

        for col in range(cols_nr):
            item = QtGui.QTableWidgetItem(str(col))
            self.table.setItem(0, col, item)
            item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        self.table.setVerticalHeaderLabels(['Time period', 'Multiplier']) # TODO: softcode

        self.table.itemChanged.connect(self.data_changed)

        self.fra_table = QtGui.QFrame()
        fra_table_lay = QtGui.QVBoxLayout(self.fra_table)
        fra_table_lay.setContentsMargins(0, 0, 0, 0)
        fra_table_lay.addWidget(self.table)

        # Top frame
        self.fra_top = QtGui.QFrame()
        fra_top_lay = QtGui.QVBoxLayout(self.fra_top)
        fra_top_lay.addWidget(self.fra_form)
        fra_top_lay.addWidget(self.fra_buttons)
        fra_top_lay.addWidget(self.fra_id)
        fra_top_lay.addWidget(self.fra_table)

        # Graph canvas
        self.fra_graph = QtGui.QFrame()
        self.static_canvas = StaticMplCanvas(self.fra_graph, width=5, height=4, dpi=100)

        self.values = []

        # self.static_canvas.draw_bars_graph(labels_values)

        # Splitter
        main_lay.addWidget(self.fra_top)
        main_lay.addWidget(self.static_canvas)

    def select_file(self):
        pass

    def new_pattern(self):
        pass

    def save_pattern(self):
        pass

    def del_pattern(self):
        pass

    def data_changed(self):
        self.values[:] = []
        for col in range(self.table.columnCount()):
            item = self.table.item(1, col)
            if item is None:
                value = 0
            else:
                value = item.text()
            try:
                value = float(value)
                value = max(value, 0)
            except:
                value = 0

            self.values.append(float(value))

        self.static_canvas.draw_bars_graph(self.values)