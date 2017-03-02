from PyQt4.QtGui import QDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QFrame, QPushButton
from ..tools.parameters import Parameters, RegExValidators


class DiameterDialog(QDialog):

    def __init__(self, parent, params, old_diam=None):

        QDialog.__init__(self, parent)
        self.params = params
        self.new_diameter = None

        self.setWindowTitle(params.plug_in_name)
        self.setModal(True)

        main_lay = QVBoxLayout(self)

        # Frame form
        self.fra_form = QFrame(self)
        fra_form_lay = QFormLayout(self.fra_form)

        # Old diameter
        self.lbl_diam_old = QLabel('Current diameter:')  # TODO: softcode
        self.txt_diam_old = QLineEdit()
        self.txt_diam_old.setEnabled(False)
        if old_diam is None:
            old_diam = '-'
        self.txt_diam_old.setText(str(old_diam))
        # self.txt_diam_old.setReadOnly(True)
        fra_form_lay.addRow(self.lbl_diam_old, self.txt_diam_old)

        # New diameter
        self.lbl_diameter = QLabel('New diameter:')  # TODO: softcode
        self.txt_diameter = QLineEdit()
        self.txt_diameter.setValidator(RegExValidators.get_pos_decimals())
        if self.params.new_diameter:
            self.new_diameter = self.params.new_diameter
            self.txt_diameter.setText(str(self.new_diameter))

        fra_form_lay.addRow(self.lbl_diameter, self.txt_diameter)

        # Buttons
        self.buttons_form = QFrame(self)
        buttons_form_lay = QHBoxLayout(self.buttons_form)

        self.btn_ok = QPushButton('OK')
        self.btn_cancel = QPushButton('Cancel')

        self.btn_cancel.clicked.connect(self.btn_cancel_clicked)
        self.btn_ok.clicked.connect(self.btn_ok_clicked)

        buttons_form_lay.addWidget(self.btn_ok)
        buttons_form_lay.addWidget(self.btn_cancel)

        main_lay.addWidget(self.fra_form)
        main_lay.addWidget(self.buttons_form)

    def btn_cancel_clicked(self):
        self.new_diameter = None
        self.setVisible(False)

    def btn_ok_clicked(self):
        if self.txt_diameter.text() is not None and self.txt_diameter.text() != '':
            self.new_diameter = float(self.txt_diameter.text())
            self.params.new_diameter = self.new_diameter
        self.setVisible(False)

    def get_diameter(self):
        return self.new_diameter
