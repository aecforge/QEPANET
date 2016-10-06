from ..model.inp_file import InpFile
from ..model.system_ops import Curve, Pattern
from ..tools.parameters import Parameters, ConfigFile
from graphs import StaticMplCanvas
from PyQt4.QtGui import QDialog, QVBoxLayout, QLabel, QFrame, QMessageBox, QPushButton, QSizePolicy, QHBoxLayout,\
    QLineEdit, QListWidget, QTableWidget, QFormLayout, QTableWidgetItem, QFileDialog
from PyQt4 import QtCore
from PyQt4.QtCore import Qt


class GraphDialog(QDialog):

    edit_patterns = 0
    edit_curves = 1

    titles = {edit_patterns: 'Pattern editor',
              edit_curves: 'Curve editor'}

    labels = {edit_patterns: 'Patterns',
              edit_curves: 'Curves'}

    def __init__(self, dockwidget, parent, params, edit_type):

        QDialog.__init__(self, parent)
        main_lay = QVBoxLayout(self)
        self.dockwidget = dockwidget
        self.params = params
        self.edit_type = edit_type

        self.x_label = ''
        self.y_label = ''

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        self.setWindowTitle(self.titles[edit_type])  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # File
        self.lbl_file = QLabel('File:')
        self.fra_file = QFrame()
        self.fra_file.setContentsMargins(0, 0, 0, 0)
        fra_file_lay = QHBoxLayout(self.fra_file)

        if edit_type == self.edit_patterns:
            self.txt_file = QLineEdit(self.params.patterns_file)
        elif edit_type == self.edit_curves:
            self.txt_file = QLineEdit(self.params.curves_file)

        self.txt_file.setReadOnly(True)
        self.txt_file.setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.txt_file.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Minimum)
        fra_file_lay.addWidget(self.txt_file)
        self.btn_file = QPushButton('Change')  # TODO: softcode
        self.btn_file.clicked.connect(self.select_file)
        fra_file_lay.addWidget(self.btn_file)
        fra_file_lay.setContentsMargins(0, 0, 0, 0)

        self.lbl_list = QLabel(self.labels[edit_type])
        self.lst_list = QListWidget()
        self.lst_list.currentItemChanged.connect(self.list_item_changed)

        # Form
        self.fra_form = QFrame()
        fra_form1_lay = QFormLayout(self.fra_form)
        fra_form1_lay.setContentsMargins(0, 0, 0, 0)
        fra_form1_lay.addRow(self.lbl_file, self.fra_file)
        fra_form1_lay.addRow(self.lbl_list, self.lst_list)

        # Buttons
        self.fra_buttons = QFrame()
        # self.fra_buttons.setFrameShape(QFrame.Box)
        # self.fra_buttons.setContentsMargins(0, 0, 0, 0)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        fra_buttons_lay.setContentsMargins(0, 0, 0, 0)
        self.btn_save = QPushButton('Save')  # TODO: softcode
        self.btn_save.clicked.connect(self.save)
        fra_buttons_lay.addWidget(self.btn_save)
        self.btn_del = QPushButton('Delete')  # TODO: softcode
        self.btn_del.clicked.connect(self.del_pattern)
        fra_buttons_lay.addWidget(self.btn_del)

        # ID
        self.lbl_id = QLabel('ID:')
        self.txt_id = QLineEdit()
        self.txt_id.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.MinimumExpanding);
        self.lbl_desc = QLabel('Desc.:')
        self.txt_desc = QLineEdit()

        self.fra_id = QFrame()
        fra_id_lay = QHBoxLayout(self.fra_id)
        fra_id_lay.addWidget(self.lbl_id)
        fra_id_lay.addWidget(self.txt_id)
        fra_id_lay.addWidget(self.lbl_desc)
        fra_id_lay.addWidget(self.txt_desc)

        # Table form
        self.table = QTableWidget(self)
        rows_nr = 24
        cols_nr = 2
        self.table.setRowCount(rows_nr)
        self.table.setColumnCount(cols_nr)
        self.table.verticalHeader().setVisible(False)

        # row_height = self.table.rowHeight(0)
        # table_height = (rows_nr * row_height) + self.table.horizontalHeader().height() + 2 * self.table.frameWidth()
        # self.table.setMinimumHeight(table_height + 10)
        # self.table.setMaximumHeight(table_height + 10)

        # Initialize empty table
        for row in range(rows_nr):
            for col in range(cols_nr):
                if edit_type == self.edit_patterns:
                    if col == 0:
                        item = QTableWidgetItem(str(row))
                        self.table.setItem(row, col, item)
                        item.setFlags(QtCore.Qt.ItemIsSelectable)
                    elif col == 1 and row == 0:
                        item = QTableWidgetItem(str(1))
                        self.table.setItem(row, col, item)
                        item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
                else:
                    if row == 0:
                        item = QTableWidgetItem(str(0))
                        self.table.setItem(row, 0, item)
                        item = QTableWidgetItem(str(1))
                        self.table.setItem(row, 1, item)
                        # item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

        self.table.itemChanged.connect(self.data_changed)

        self.fra_table = QFrame()
        fra_table_lay = QVBoxLayout(self.fra_table)
        fra_table_lay.setContentsMargins(0, 0, 0, 0)
        fra_table_lay.addWidget(self.table)

        # Graph canvas
        self.fra_graph = QFrame()
        self.static_canvas = StaticMplCanvas(self.fra_graph, width=5, height=4, dpi=100)
        fra_graph_lay = QVBoxLayout(self.fra_graph)
        fra_graph_lay.addWidget(self.static_canvas)

        # Top frame
        self.fra_top = QFrame()
        fra_top_lay = QVBoxLayout(self.fra_top)
        fra_top_lay.addWidget(self.fra_form)
        fra_top_lay.addWidget(self.fra_buttons)
        fra_top_lay.addWidget(self.fra_id)
        fra_top_lay.addWidget(self.fra_table)

        # Bottom frame
        self.fra_bottom = QFrame()
        fra_bottom_lay = QHBoxLayout(self.fra_bottom)
        fra_bottom_lay.addWidget(self.fra_table)
        fra_bottom_lay.addWidget(self.fra_graph)

        self.xs = []
        self.ys = []

        # Main
        main_lay.addWidget(self.fra_top)
        main_lay.addWidget(self.fra_bottom)

        # Read existing patterns/curves
        self.update_graph = False
        self.read()
        self.update_graph = True

    def setVisible(self, bool):
        QDialog.setVisible(self, bool)

        if self.edit_type == self.edit_patterns:
            self.x_label = 'Time period'
            self.y_label = 'Multiplier'
        elif self.edit_type == self.edit_curves:
            self.x_label = 'Flow ' + '[' + self.params.options.flow_units + ']'
            self.y_label = 'Head ' + '[' + self.params.options.units_depth[self.params.options.units] + ']'

        self.table.setHorizontalHeaderLabels([self.x_label, self.y_label])  # TODO: softcode

    def list_item_changed(self):

        p_index = self.lst_list.currentRow()

        flags = Qt.ItemFlags()
        flags != Qt.ItemIsEnabled

        if p_index >= 0:

            self.update_graph = False
            if self.edit_type == self.edit_patterns:
                current = self.params.patterns[p_index]
                for v in range(len(current.values)):
                    item = QTableWidgetItem(str(v))
                    item.setFlags(flags)
                    self.table.setItem(v, 0, item)
                    self.table.setItem(v, 1, QTableWidgetItem(str(current.values[v])))
            elif self.edit_type == self.edit_curves:
                current = self.params.curves[p_index]
                for v in range(len(current.xs)):
                    self.table.setItem(v, 0, QTableWidgetItem(str(current.xs[v])))
                    self.table.setItem(v, 1, QTableWidgetItem(str(current.ys[v])))

            # Update GUI
            self.txt_id.setText(current.id)
            self.txt_desc.setText(current.desc)

            # Update graph
            self.update_graph = True

            if self.edit_type == self.edit_patterns:
                self.static_canvas.draw_bars_graph(current.values)
            elif self.edit_type == self.edit_curves:
                self.static_canvas.draw_line_graph(current.xs, current.ys, self.x_label, self.y_label)

        else:

            self.txt_id.setText('')
            self.txt_desc.setText('')

            # Update table and chart
            self.update_graph = False
            for v in range(self.table.columnCount()):
                self.table.setItem(v, 1, QTableWidgetItem(''))
            self.update_graph = True

            if self.edit_type == self.edit_patterns:
                self.static_canvas.draw_bars_graph([0] * 24)
            elif self.edit_type == self.edit_curves:
                self.static_canvas.draw_line_graph([0, 1], [0, 0], self.x_label, self.y_label)

    def select_file(self):

        config_file = ConfigFile(Parameters.config_file_path)

        file_path = QFileDialog.getOpenFileName(
            self,
            'Select file',
            self.txt_file.text(),
            'Files (*.txt *.inp)')

        if file_path is None or file_path == '':
            return
        else:
            if self.edit_type == GraphDialog.edit_patterns:
                # Save patterns file path in configuration file
                config_file.set_patterns_file_path(file_path)
                Parameters.patterns_file = file_path
            elif self.edit_type == GraphDialog.edit_curves:
                # Save curve file path in configuration file
                config_file.set_curves_file_path(file_path)
                Parameters.curves_file = file_path

        self.read()

    def read(self):

        self.lst_list.clear()

        if self.edit_type == self.edit_patterns:
            InpFile.read_patterns(self.params)
            for pattern in self.params.patterns:
                desc = ' (' + pattern.desc + ')' if pattern.desc is not None else ''
                self.lst_list.addItem(pattern.id + desc)

        elif self.edit_type == self.edit_curves:
            InpFile.read_curves(self.params)
            for curve in self.params.curves:
                desc = ' (' + curve.desc + ')' if curve.desc is not None else ''
                self.lst_list.addItem(curve.id + desc)

        if self.lst_list.count() > 0:
            self.lst_list.setCurrentRow(0)

    def save(self):

        # Check for ID
        if not self.txt_id.text():
            QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    u'Please specify the ID.', # TODO: softcode
                    QMessageBox.Ok)
            return

        if self.edit_type == GraphDialog.edit_patterns:
            # Check for ID unique
            overwrite_p_index = -1
            for p in range(len(self.params.patterns)):
                if self.params.patterns[p].id == self.txt_id.text():
                    ret = QMessageBox.question(
                        self,
                        Parameters.plug_in_name,
                        u'The ID ' + self.txt_id.text() + u' already exists. Overwrite?',  # TODO: softcode
                        QMessageBox.Yes | QMessageBox.No)
                    if ret == QMessageBox.No:
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
                self.params.patterns[overwrite_p_index] = new_pattern
                InpFile.write_patterns(self.params, self.params.patterns_file)
                self.read()
                self.lst_list.setCurrentRow(overwrite_p_index)

            # Save new
            else:
                self.params.patterns.append(new_pattern)
                InpFile.write_patterns(self.params, self.params.patterns_file)
                self.read()

            self.dockwidget.update_patterns_combo()

        elif self.edit_type == GraphDialog.edit_curves:
            # Check for ID unique
            overwrite_c_index = -1
            for c in range(len(self.params.curves)):
                if self.params.curves[c].id == self.txt_id.text():
                    ret = QMessageBox.question(
                        self,
                        Parameters.plug_in_name,
                        u'The ID ' + self.txt_id.text() + u' already exists. Overwrite?',  # TODO: softcode
                        QMessageBox.Yes | QMessageBox.No)
                    if ret == QMessageBox.No:
                        return
                    else:
                        overwrite_c_index = c
                    break

            xs = []
            ys = []
            for row in range(self.table.rowCount()):
                item_x = self.table.item(row, 0)
                item_y = self.table.item(row, 1)

                if item_x is not None and item_y is not None:
                    xs.append(self.from_item_to_val(item_x))
                    ys.append(self.from_item_to_val(item_y))

            # Update
            new_curve = Curve(self.txt_id.text(), self.txt_desc.text())
            for v in range(len(xs)):
                new_curve.append_xy(xs[v], ys[v])

            if overwrite_c_index >= 0:
                self.params.curves[overwrite_c_index] = new_curve
                InpFile.write_curves(self.params, self.params.curves_file)
                self.read()
                self.lst_list.setCurrentRow(overwrite_c_index)

            # Save new
            else:
                self.params.patterns.append(new_curve)
                InpFile.write_curves(self.params, self.params.curves_file)
                self.read()

            # Update GUI
            self.dockwidget.update_curves_combo()

    def del_pattern(self):
        selected_row = self.lst_list.currentRow()
        self.lst_list.takeItem(selected_row)

        if self.edit_type == GraphDialog.edit_curves:
            del self.params.curves[selected_row]
            InpFile.write_curves(self.params, self.params.curves_file)
        elif self.edit_type == GraphDialog.edit_patterns:
            del self.params.patterns[selected_row]
            InpFile.write_patterns(self.params, self.params.patterns_file)

    def data_changed(self):

        self.xs = []
        self.ys = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            x = self.from_item_to_val(item)
            item = self.table.item(row, 1)
            y = self.from_item_to_val(item)

            if x is not None:
                self.xs.append(float(x))
            if y is not None:
                self.ys.append(float(y))

        if self.update_graph:
            if self.edit_type == self.edit_patterns:
                self.static_canvas.draw_bars_graph(self.ys)
            elif self.edit_type == self.edit_curves:
                series_length = min(len(self.xs), len(self.ys))
                self.static_canvas.draw_line_graph(self.xs[:series_length], self.ys[:series_length], self.x_label, self.y_label)

    def from_item_to_val(self, item):

        if item is None:
            value = None
        else:
            value = item.text()
        try:
            value = float(value)
            value = max(value, 0)

        except:
            value = None

        return value