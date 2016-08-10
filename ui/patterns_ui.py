from ..model.inp_file import InpFile
from ..model.system_ops import Pattern
from ..tools.parameters import Parameters, ConfigFile
from graphs import StaticMplCanvas
from PyQt4 import QtGui, QtCore


class PatternsDialog(QtGui.QDialog):

    def __init__(self, parent, parameters):
        QtGui.QDialog.__init__(self, parent)
        main_lay = QtGui.QVBoxLayout(self)
        self.parameters = parameters

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowTitle('Pattern editor')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # File
        self.lbl_file = QtGui.QLabel('Pattern file:')
        self.fra_file = QtGui.QFrame()
        self.fra_file.setContentsMargins(0, 0, 0, 0)
        fra_file_lay = QtGui.QHBoxLayout(self.fra_file)
        self.txt_file = QtGui.QLineEdit(self.parameters.patterns_file)
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
        self.lst_patterns.currentItemChanged.connect(self.list_item_changed)

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

        # Main
        main_lay.addWidget(self.fra_top)
        main_lay.addWidget(self.static_canvas)

        # Read existing patterns
        self.update_graph = False
        self.read_patterns()
        self.update_graph = True

    def list_item_changed(self):
        p_index = self.lst_patterns.currentRow()

        if p_index >= 0:
            current_pattern = self.parameters.patterns[p_index]

            # Update GUI
            self.txt_id.setText(current_pattern.id)
            self.txt_desc.setText(current_pattern.desc)

            # Update table and chart
            self.update_graph = False
            for v in range(len(current_pattern.values)):
                self.table.setItem(1, v, QtGui.QTableWidgetItem(str(current_pattern.values[v])))
            self.update_graph = True

            self.static_canvas.draw_bars_graph(current_pattern.values)

        else:

            self.txt_id.setText('')
            self.txt_desc.setText('')

            # Update table and chart
            self.update_graph = False
            for v in range(self.table.columnCount()):
                self.table.setItem(1, v, QtGui.QTableWidgetItem(''))
            self.update_graph = True

            self.static_canvas.draw_bars_graph([0] * 24)

    def select_file(self):

        config_file = ConfigFile(Parameters.config_file_path)
        patterns_file_path = QtGui.QFileDialog.getOpenFileName(
            self,
            'Select patterns file',
            self.txt_file.text(),
            'Patterns files (*.txt *.inp)')

        if patterns_file_path is None or patterns_file_path == '':
            return
        else:
            # Save patterns file path in configuration file
            config_file.set_patterns_file_path(patterns_file_path)

        Parameters.patterns_file = patterns_file_path
        self.read_patterns()

    def read_patterns(self):
        InpFile.read_patterns(self.parameters, self.parameters.patterns_file)

        self.lst_patterns.clear()
        for pattern in self.parameters.patterns:
            desc = ' (' + pattern.desc + ')' if pattern.desc is not None else ''
            self.lst_patterns.addItem(pattern.id + desc)

        if self.lst_patterns.count() > 0:
            self.lst_patterns.setCurrentRow(0)

    def save_pattern(self):

        # Check for ID
        if not self.txt_id.text():
            QtGui.QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    u'Please specify the pattern ID.', # TODO: softcode
                    QtGui.QMessageBox.Ok)
            return

        # Check for ID unique
        overwrite_p_index = -1
        for p in range(len(self.parameters.patterns)):
            if self.parameters.patterns[p].id == self.txt_id.text():
                ret = QtGui.QMessageBox.question(
                    self,
                    Parameters.plug_in_name,
                    u'A pattern with ID ' + self.txt_id.text() + ' already exists. Overwrite?',  # TODO: softcode
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
                if ret == QtGui.QMessageBox.No:
                    return
                else:
                    overwrite_p_index = p
                break

        values = []
        for col in range(self.table.columnCount()):
            item = self.table.item(1, col)
            values.append(self.from_item_to_val(item))

        # Update
        new_pattern = Pattern(self.txt_id.text(), self.txt_desc.text(), values)
        if overwrite_p_index >= 0:
            self.parameters.patterns[overwrite_p_index] = new_pattern
            InpFile.write_patterns(self.parameters, self.parameters.patterns_file)
            self.read_patterns()
            self.lst_patterns.setCurrentRow(overwrite_p_index)

        # Save new
        else:
            self.parameters.patterns.append(new_pattern)
            InpFile.write_patterns(self.parameters, self.parameters.patterns_file)
            self.read_patterns()

    def del_pattern(self):
        selected_row = self.lst_patterns.currentRow()
        self.lst_patterns.takeItem(selected_row)
        del self.parameters.patterns[selected_row]
        InpFile.write_patterns(self.parameters, self.parameters.patterns_file)

    def data_changed(self):
        self.values[:] = []
        for col in range(self.table.columnCount()):
            item = self.table.item(1, col)
            value = self.from_item_to_val(item)

            self.values.append(float(value))

        if self.update_graph:
            self.static_canvas.draw_bars_graph(self.values)

    def from_item_to_val(self, item):
        if item is None:
            value = 0
        else:
            value = item.text()
        try:
            value = float(value)
            value = max(value, 0)
        except:
            value = 0
        return value