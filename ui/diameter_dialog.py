from PyQt4.QtGui import QDialog, QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QFrame, QPushButton
from ..tools.parameters import Parameters, RegExValidators


class DiameterDialog(QDialog):

    def __init__(self, parent, params):

        QDialog.__init__(self, parent)
        self.params = params
        self.new_diameter = None

        self.setWindowTitle(params.plug_in_name)
        self.setModal(True)

        main_lay = QVBoxLayout(self)

        # Form
        self.fra_form = QFrame(self)
        fra_form_lay = QFormLayout(self.fra_form)

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

        self.btn_cancel = QPushButton('Cancel')
        self.btn_ok = QPushButton('OK')

        self.btn_cancel.pressed.connect(self.btn_cancel_pressed)
        self.btn_ok.pressed.connect(self.btn_ok_pressed)

        buttons_form_lay.addWidget(self.btn_ok)
        buttons_form_lay.addWidget(self.btn_cancel)

        main_lay.addWidget(self.fra_form)
        main_lay.addWidget(self.buttons_form)

    def btn_cancel_pressed(self):
        self.new_diameter = None
        self.setVisible(False)

    def btn_ok_pressed(self):
        if self.txt_diameter.text() is not None and self.txt_diameter.text() != '':
            self.new_diameter = float(self.txt_diameter.text())
            self.params.new_diameter = self.new_diameter
        self.setVisible(False)

    def get_diameter(self):
        return self.new_diameter
