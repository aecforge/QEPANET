from builtins import range
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QFrame, QListWidget, QPushButton, QHBoxLayout, QDialogButtonBox, QListWidgetItem, QLineEdit, QLabel
from ..tools.parameters import Parameters, RegExValidators


class TagsDialog(QDialog):

    def __init__(self, dockwidget, parent, params):

        QDialog.__init__(self, parent)
        main_lay = QVBoxLayout(self)
        self.dockwidget = dockwidget
        self.params = params

        self.setWindowTitle('Tags editor')

        # Top frame
        self.fra_top = QFrame()
        fra_top_lay = QVBoxLayout(self.fra_top)

        self.lst_main = QListWidget(self)
        self.btn_add = QPushButton('Add tag')
        self.btn_add.clicked.connect(self.add_tag)
        self.btn_remove = QPushButton('Remove tag')
        self.btn_remove.clicked.connect(self.remove_tag)

        fra_top_lay.addWidget(self.lst_main)
        fra_top_lay.addWidget(self.btn_add)
        fra_top_lay.addWidget(self.btn_remove)

        # Bottom frame
        self.fra_bottom = QFrame()
        fra_bottom_lay = QHBoxLayout(self.fra_bottom)

        btb_main = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btb_main.accepted.connect(self.ok)
        btb_main.rejected.connect(self.reject)

        fra_bottom_lay.addWidget(btb_main)

        # Main
        main_lay.addWidget(self.fra_top)
        main_lay.addWidget(self.fra_bottom)

        self.initialize()

    def initialize(self):
        for tag_name in self.params.tag_names:
            self.lst_main.insertItem(self.lst_main.count(), QListWidgetItem(tag_name, self.lst_main))

    def ok(self):
        tag_names = []
        for r in range(self.lst_main.count()):
            tag_names.append(self.lst_main.item(r).text())

        self.params.tag_names = tag_names

        self.setVisible(False)

    def reject(self):
        self.setVisible(False)

    def add_tag(self):

        tag_name_dialog = TagNameDialog(self.dockwidget, self)
        tag_name_dialog.exec_()
        tag_name = tag_name_dialog.get_tag_name()

        if tag_name is not None:
            current_row = self.lst_main.currentRow()
            if current_row is None:
                current_row = self.lst_main.count()
            self.lst_main.insertItem(current_row, QListWidgetItem(tag_name, self.lst_main))

    def remove_tag(self):
        sel_items = self.lst_main.selectedItems()
        for sel_item in sel_items:
            self.lst_main.takeItem(self.lst_main.row(sel_item))


class TagNameDialog(QDialog):

    def __init__(self, dockwidget, parent):

        QDialog.__init__(self, parent)
        main_lay = QVBoxLayout(self)
        self.dockwidget = dockwidget
        self.tag_name = None

        self.setWindowTitle('Tag name')

        # Top frame
        self.fra_top = QFrame()
        fra_top_lay = QVBoxLayout(self.fra_top)

        self.lbl_explanation = QLabel('Insert a name (no blanks allowed)')
        fra_top_lay.addWidget(self.lbl_explanation)

        self.txt_name = QLineEdit()
        self.txt_name.setValidator(RegExValidators.get_no_blanks())
        fra_top_lay.addWidget(self.txt_name)

        # Button box
        self.btb_main = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.btb_main.accepted.connect(self.ok)
        self.btb_main.rejected.connect(self.reject)

        # Bottom frame
        self.fra_bottom = QFrame()
        fra_bottom_lay = QHBoxLayout(self.fra_bottom)
        fra_bottom_lay.addWidget(self.btb_main)

        # Main
        main_lay.addWidget(self.fra_top)
        main_lay.addWidget(self.fra_bottom)

        self.initialize()

    def initialize(self):
        self.btb_main.button(QDialogButtonBox.Ok).setEnabled(False)
        self.txt_name.textChanged.connect(self.text_changed)

    def ok(self):
        self.tag_name = self.txt_name.text()
        self.setVisible(False)

    def reject(self):
        self.tag_name = None
        self.setVisible(False)

    def text_changed(self):
        self.btb_main.button(QDialogButtonBox.Ok).setEnabled(self.txt_name != '')

    def get_tag_name(self):
        return self.tag_name