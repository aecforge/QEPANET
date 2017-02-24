from ..model.inp_writer import InpFile
from ..model.system_ops import Curve, Pattern
from ..tools.parameters import Parameters, ConfigFile
from graphs import StaticMplCanvas
from PyQt4.QtGui import *
from PyQt4 import QtCore
from PyQt4.QtCore import Qt
import numpy


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

        self.current = None

        self.current_saved = False

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
        self.btn_file.clicked.connect(self.import_file)
        fra_file_lay.addWidget(self.btn_file)
        fra_file_lay.setContentsMargins(0, 0, 0, 0)

        self.lbl_list = QLabel(self.labels[edit_type])
        self.lst_list = QListWidget()
        self.lst_list.currentItemChanged.connect(self.list_item_changed)

        # Form
        self.fra_form = QFrame()
        fra_form1_lay = QFormLayout(self.fra_form)
        fra_form1_lay.setContentsMargins(0, 0, 0, 0)
        # fra_form1_lay.addRow(self.lbl_file, self.fra_file)
        fra_form1_lay.addRow(self.lbl_list, self.lst_list)

        # Buttons
        self.fra_buttons = QFrame()
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        fra_buttons_lay.setContentsMargins(0, 0, 0, 0)

        if self.edit_type == self.edit_patterns:
            ele_name = 'pattern'
        elif self.edit_type == self.edit_curves:
            ele_name = 'curve'

        # Buttons
        self.btn_new = QPushButton('New ' + ele_name)  # TODO: softcode
        self.btn_new.clicked.connect(self.new_element)
        fra_buttons_lay.addWidget(self.btn_new)

        self.btn_import = QPushButton('Import ' + ele_name + 's')  # TODO: softcode
        self.btn_import.clicked.connect(self.import_file)
        fra_buttons_lay.addWidget(self.btn_import)

        self.btn_save = QPushButton('Save current ' + ele_name)  # TODO: softcode
        self.btn_save.clicked.connect(self.save)
        fra_buttons_lay.addWidget(self.btn_save)

        self.btn_del = QPushButton('Delete current ' + ele_name)  # TODO: softcode
        self.btn_del.clicked.connect(self.del_item)
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
        self.rows_nr = 24
        self.cols_nr = 2
        self.table.setRowCount(self.rows_nr)
        self.table.setColumnCount(self.cols_nr)
        self.table.verticalHeader().setVisible(False)

        # row_height = self.table.rowHeight(0)
        # table_height = (rows_nr * row_height) + self.table.horizontalHeader().height() + 2 * self.table.frameWidth()
        # self.table.setMinimumHeight(table_height + 10)
        # self.table.setMaximumHeight(table_height + 10)

        # Initialize empty table
        self.clear_table()

        self.table.itemChanged.connect(self.data_changed)

        self.fra_table = QFrame()
        fra_table_lay = QVBoxLayout(self.fra_table)
        fra_table_lay.setContentsMargins(0, 0, 0, 0)

        if edit_type == self.edit_curves:
            self.fra_pump_type = QFrame()
            fra_pump_type_lay = QFormLayout(self.fra_pump_type)

            self.lbl_pump_type = QLabel('Curve type:')  # TODO: softcode
            self.cbo_pump_type = QComboBox()

            for key, name in Curve.type_names.iteritems():
                self.cbo_pump_type.addItem(name, key)

            fra_pump_type_lay.addRow(self.lbl_pump_type, self.cbo_pump_type)

            fra_table_lay.addWidget(self.fra_pump_type)

            self.cbo_pump_type.activated.connect(self.cbo_pump_type_activated)

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
        fra_top_lay.addWidget(self.fra_id)
        fra_top_lay.addWidget(self.fra_buttons)

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

        # Get existing patterns/curves
        self.need_to_update_graph = False
        if self.edit_type == self.edit_patterns:
            for pattern_id, pattern in self.params.patterns.iteritems():
                self.lst_list.addItem(pattern.id)

        elif self.edit_type == self.edit_curves:
            for curve_id, curve in self.params.curves.iteritems():
                self.lst_list.addItem(curve.id)

        if self.lst_list.count() > 0:
            self.lst_list.setCurrentRow(0)
            self.btn_save.setEnabled(True)
            self.btn_del.setEnabled(True)
            self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        else:
            self.btn_save.setEnabled(False)
            self.btn_del.setEnabled(False)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.need_to_update_graph = True
        self.update_graph()

    def cbo_pump_type_activated(self):
        self.update_graph()

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

        # Clear table
        self.clear_table()

        self.need_to_update_graph = False
        if p_index >= 0:

            if self.edit_type == self.edit_patterns:
                self.current = self.params.patterns[self.lst_list.currentItem().text()]
                for v in range(len(self.current.values)):
                    item = QTableWidgetItem(str(v))
                    item.setFlags(flags)
                    self.table.setItem(v, 0, item)
                    self.table.setItem(v, 1, QTableWidgetItem(str(self.current.values[v])))

            elif self.edit_type == self.edit_curves:
                self.current = self.params.curves[self.lst_list.currentItem().text()]
                for v in range(len(self.current.xs)):
                    self.table.setItem(v, 0, QTableWidgetItem(str(self.current.xs[v])))
                    self.table.setItem(v, 1, QTableWidgetItem(str(self.current.ys[v])))

                curve_type = self.current.type
                self.cbo_pump_type.setCurrentIndex(curve_type)

            # Update GUI
            self.txt_id.setText(self.current.id)
            self.txt_desc.setText(self.current.desc)

            # Update graph
            self.need_to_update_graph = True
            self.update_graph()

        else:

            # No curves
            self.txt_id.setText('')
            self.txt_desc.setText('')

            # Update table and chart
            self.need_to_update_graph = False
            for v in range(self.table.columnCount()):
                self.table.setItem(v, 1, QTableWidgetItem(''))

            self.need_to_update_graph = True
            self.update_graph()

    def import_file(self):

        config_file = ConfigFile(Parameters.config_file_path)

        directory = None
        if self.edit_type == GraphDialog.edit_curves:
            directory = self.params.last_curves_dir
        elif self.edit_type == GraphDialog.edit_patterns:
            directory = self.params.last_patterns_dir

        if directory is None:
            directory = self.params.last_project_dir

        file_path = QFileDialog.getOpenFileName(
            self,
            'Select file',
            directory,
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

        self.read(file_path)

    def read(self, file_path):

        self.lst_list.clear()

        if self.edit_type == self.edit_patterns:
            # InpFile.read_patterns(self.params, file_path)
            for pattern_id, pattern in self.params.patterns.iteritems():
                # desc = ' (' + pattern.desc + ')' if pattern.desc is not None else ''
                self.lst_list.addItem(pattern.id)
                self.params.patterns[pattern.id] = pattern

        elif self.edit_type == self.edit_curves:
            # InpFile.read_curves(self.params, file_path)
            for curve_id, curve in self.params.curves.iteritems():
                # desc = ' (' + curve.desc + ')' if curve.desc is not None else ''
                self.lst_list.addItem(curve.id)
                self.params.curves[curve.id] = curve

        if self.lst_list.count() > 0:
            self.lst_list.setCurrentRow(0)

    def new_element(self):

        old_ids = []
        if self.edit_type == self.edit_patterns:
            for pattern in self.params.patterns.itervalues():
                old_ids.append(pattern.id)
        elif self.edit_type == self.edit_curves:
            for curve in self.params.curves.itervalues():
                old_ids.append(curve.id)
        self.new_dialog = NewIdDialog(self, old_ids)
        self.new_dialog.exec_()

        new_id = self.new_dialog.get_newid()
        if new_id is None:
            return

        if self.edit_type == self.edit_patterns:
            new_pattern = Pattern(new_id)
            self.params.patterns[new_pattern.id] = new_pattern
            self.lst_list.addItem(new_pattern.id)
        elif self.edit_type == self.edit_curves:
            curve_type = self.cbo_pump_type.itemData(self.cbo_pump_type.currentIndex())
            new_curve = Curve(new_id, curve_type)
            self.params.curves[new_curve.id] = new_curve
            self.lst_list.addItem(new_curve.id)

        self.lst_list.setCurrentRow(self.lst_list.count() - 1)

        self.txt_id.setText(new_id)
        self.txt_desc.setText('')

        # Clear table
        self.clear_table()
        self.static_canvas.axes.clear()

        self.btn_save.setEnabled(True)
        self.btn_del.setEnabled(True)
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)

    def save(self):

        self.need_to_update_graph = False

        # Check for ID
        if not self.txt_id.text():
            QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    u'Please specify the ID.', # TODO: softcode
                    QMessageBox.Ok)
            return

        if self.edit_type == GraphDialog.edit_patterns:

            values = []
            for row in range(self.table.rowCount()):
                item = self.table.item(row, 1)
                if item.text() != '':
                    values.append(self.from_item_to_val(item))

            pattern = Pattern(self.txt_id.text(), self.txt_desc.text(), values)

            old_patterns = self.params.patterns
            old_patterns[pattern.id] = pattern
            self.params.patterns = old_patterns

            self.lst_list.currentItem().setText(pattern.id)

        elif self.edit_type == GraphDialog.edit_curves:

            # Check for ID unique
            xs = []
            ys = []
            for row in range(self.table.rowCount()):
                item_x = self.table.item(row, 0)
                item_y = self.table.item(row, 1)

                if item_x.text() != '' and item_y.text() != '':
                    xs.append(self.from_item_to_val(item_x))
                    ys.append(self.from_item_to_val(item_y))

            curve_type = self.cbo_pump_type.itemData(self.cbo_pump_type.currentIndex())
            curve = Curve(self.txt_id.text(), curve_type, self.txt_desc.text())
            for v in range(len(xs)):
                curve.append_xy(xs[v], ys[v])

            old_curves = self.params.curves
            old_curves[curve.id] = curve
            self.params.curves = old_curves

            self.lst_list.currentItem().setText(curve.id)

            # Update GUI
            self.dockwidget.update_curves_combo()

        # self.read()
        self.need_to_update_graph = True

    def clear_table(self):

        self.need_to_update_graph = False
        for r in range(self.table.rowCount()):
            self.table.setItem(r, 0, QTableWidgetItem(None))
            self.table.setItem(r, 1, QTableWidgetItem(None))

        for row in range(self.rows_nr):
            for col in range(self.cols_nr):
                if self.edit_type == self.edit_patterns:
                    if col == 0:
                        item = QTableWidgetItem(str(row))
                        self.table.setItem(row, col, item)
                        item.setFlags(QtCore.Qt.ItemIsSelectable)
                    # elif col == 1 and row == 0:
                    #     item = QTableWidgetItem(str(1))
                    #     self.table.setItem(row, col, item)
                    #     item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)

                elif self.edit_type == self.edit_curves:
                    if row == 0:
                        item = QTableWidgetItem(str(0))
                        self.table.setItem(row, 0, item)
                        item = QTableWidgetItem(str(1))
                        self.table.setItem(row, 1, item)
                        # item.setFlags(QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled)
        self.need_to_update_graph = True

    def del_item(self):
        selected_row = self.lst_list.currentRow()
        name = self.lst_list.currentItem().text()
        if selected_row < 0:
            return

        self.lst_list.takeItem(selected_row)
        if self.lst_list.count() == 0:
            self.btn_save.setEnabled(False)
            self.btn_del.setEnabled(False)
            self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        if self.edit_type == GraphDialog.edit_curves:
            del self.params.curves[name]
            # InpFile.write_curves(self.params, self.params.curves_file)
        elif self.edit_type == GraphDialog.edit_patterns:
            del self.params.patterns[name]
            # InpFile.write_patterns(self.params, self.params.patterns_file)

    def data_changed(self):

        if self.need_to_update_graph:
            self.update_graph()

    def update_graph(self):

        if not self.need_to_update_graph:
            return

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

        if len(self.xs) == 0 or len(self.ys) == 0:
            self.static_canvas.clear()
            return

        if self.edit_type == self.edit_patterns:
            y_axis_label = 'Mult. avg.: ' + '{0:.2f}'.format((numpy.average(self.ys)))
            self.static_canvas.draw_bars_graph(self.ys, y_axes_label=y_axis_label)

        elif self.edit_type == self.edit_curves:

            # Account for different types of curves
            cbo_data = self.cbo_pump_type.itemData(self.cbo_pump_type.currentIndex())

            series_length = min(len(self.xs), len(self.ys))

            if cbo_data == Curve.type_efficiency or cbo_data == Curve.type_headloss or cbo_data == Curve.type_volume:
                self.static_canvas.draw_line_graph(self.xs[:series_length], self.ys[:series_length],
                                                   self.x_label, self.y_label)

            elif cbo_data == Curve.type_pump:
                # Needs to account for different types of curves
                if series_length == 1 or series_length == 3:
                    if series_length == 1:
                        # 3 curve points
                        curve_xs = [0, self.xs[0], self.xs[0] * 2]
                        curve_ys = [self.ys[0] * 1.33, self.ys[0], 0]
                        # y = a * x^2 + b * x + c

                    elif series_length == 3:
                        # 3 curve points
                        curve_xs = [self.xs[0], self.xs[1], self.xs[2]]
                        curve_ys = [self.ys[0], self.ys[1], self.ys[2]]

                    (a, b, c) = numpy.polyfit(curve_xs, curve_ys, 2)

                    # Create a few interpolated values
                    interp_xs = []
                    interp_ys = []
                    n_vals = 30
                    for v in range(n_vals+1):
                        x = (curve_xs[2] - curve_xs[0]) / n_vals * v
                        interp_xs.append(x)
                        y = a * x**2 + b * x + c
                        interp_ys.append(y)

                    self.static_canvas.draw_line_graph(interp_xs, interp_ys, self.x_label, self.y_label)

                else:
                    self.static_canvas.draw_line_graph(self.xs[:series_length], self.ys[:series_length],
                                                       self.x_label, self.y_label)

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


class NewIdDialog(QDialog):

    def __init__(self, parent, old_ids):

        QDialog.__init__(self, parent)

        self.old_ids = old_ids

        main_lay = QVBoxLayout(self)

        self.fra_id = QFrame(self)
        fra_id_lay = QFormLayout(self.fra_id)
        self.lbl_id = QLabel('New ID:')
        self.txt_id = QLineEdit('')
        fra_id_lay.addRow(self.lbl_id, self.txt_id)

        self.fra_buttons = QFrame()
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)

        self.btn_ok = QPushButton('OK')
        self.btn_ok.pressed.connect(self.btn_ok_pressed)
        self.btn_cancel = QPushButton('Cancel')
        self.btn_cancel.pressed.connect(self.btn_cancel_pressed)
        fra_buttons_lay.addWidget(self.btn_ok)
        fra_buttons_lay.addWidget(self.btn_cancel)

        main_lay.addWidget(self.fra_id)
        main_lay.addWidget(self.fra_buttons)

        self.new_id = None

    def btn_ok_pressed(self):
        if not self.check():
            return
        self.new_id = self.txt_id.text()
        self.setVisible(False)

    def btn_cancel_pressed(self):
        self.new_id = None
        self.setVisible(False)

    def get_newid(self):
        return self.new_id

    def check(self):
        if self.txt_id.text() == '':
            QMessageBox.warning(
                self,
                Parameters.plug_in_name,
                u'Please specify the new ID.',  # TODO: softcode
                QMessageBox.Ok)
            return False

        for old_id in self.old_ids:
            if old_id.lower() == self.txt_id.text().lower():
                QMessageBox.warning(
                    self,
                    Parameters.plug_in_name,
                    u'The ID already exists.',  # TODO: softcode
                    QMessageBox.Ok)
                return False

        return True

