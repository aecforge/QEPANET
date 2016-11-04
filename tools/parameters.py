import ConfigParser
import codecs
import os

from collections import OrderedDict
from PyQt4.QtCore import QRegExp
from PyQt4.QtGui import QRegExpValidator
from observable import Observable
from ..model.options_report import Options, Report
from ..model.options_report import Times
from ..model.system_ops import Energy
from ..model.water_quality import Reactions



class Parameters(Observable):

    plug_in_name = 'QEPANET 0.20'
    config_file_name = 'config.ini'

    path = os.path.dirname(os.path.realpath(__file__))
    path = os.path.dirname(path)
    config_file_path = os.path.join(path, config_file_name)
    regex_number_pos_decimals = '^[0-9]\d*(\.\d+)?$'
    regex_number_pos_neg_decimals = '^-?[0-9]\d*(\.\d+)?$'
    regex_number_pos_int = '^[0-9]\d*$'
    regex_number_pos_01 = '^[0-1]\d*$'
    regex_number_pos_int_no_zero = '^[1-9]\d*$'
    regex_time_hh_mm = '^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$'

    def __init__(self):
        super(Parameters, self).__init__()

        self._junctions_vlay = None
        self._pipes_vlay = None
        self._pumps_vlay = None
        self._reservoirs_vlay = None
        self._tanks_vlay = None
        self._valves_vlay = None
        self._dem_rlay = None

        self._patterns = OrderedDict()
        self._patterns_file = None
        self._curves = OrderedDict()
        self._curves_file = None

        self._snap_tolerance = 10
        self._tolerance = 0.01
        self._min_dist = 1  # TODO: check: 1 m? Why?

        self._vertex_dist = 0

        self.options = Options()
        self.reactions = Reactions()
        self.times = Times()
        self.report = Report()
        self.energy = Energy()

        self.new_diameter = None

        # Paths
        self.last_project_dir = None
        self.last_curves_dir = None
        self.last_patterns_dir = None

    # Layers
    @property
    def junctions_vlay(self):
        return self._junctions_vlay

    @junctions_vlay.setter
    def junctions_vlay(self, value):
        self._junctions_vlay = value
        self.notify()

    @property
    def pipes_vlay(self):
        return self._pipes_vlay

    @pipes_vlay.setter
    def pipes_vlay(self, value):
        self._pipes_vlay = value
        self.notify()

    @property
    def pumps_vlay(self):
        return self._pumps_vlay

    @pumps_vlay.setter
    def pumps_vlay(self, value):
        self._pumps_vlay = value
        self.notify()

    @property
    def reservoirs_vlay(self):
        return self._reservoirs_vlay

    @reservoirs_vlay.setter
    def reservoirs_vlay(self, value):
        self._reservoirs_vlay = value
        self.notify()

    @property
    def tanks_vlay(self):
        return self._tanks_vlay

    @tanks_vlay.setter
    def tanks_vlay(self, value):
        self._tanks_vlay = value
        self.notify()

    @property
    def valves_vlay(self):
        return self._valves_vlay

    @valves_vlay.setter
    def valves_vlay(self, value):
        self._valves_vlay = value
        self.notify()

    @property
    def dem_rlay(self):
        return self._dem_rlay

    @dem_rlay.setter
    def dem_rlay(self, value):
        self._dem_rlay = value
        self.notify()

    # Pattern / curves
    @property
    def curves(self):
        return self._curves

    @curves.setter
    def curves(self, value):
        self._curves = value
        self.notify()

    @property
    def curves_file(self):
        return self._curves_file

    @curves_file.setter
    def curves_file(self, value):
        self._curves_file = value
        self.notify()

    @property
    def patterns(self):
        return self._patterns

    @patterns.setter
    def patterns(self, value):
        self._patterns = value
        self.notify()

    @property
    def patterns_file(self):
        return self._patterns_file

    @patterns_file.setter
    def patterns_file(self, value):
        self._patterns_file = value
        self.notify()

    # Tolerances
    @property
    def tolerance(self):
        return self._tolerance

    @tolerance.setter
    def tolerance(self, value):
        self._tolerance = value
        self.notify()

    @property
    def snap_tolerance(self):
        return self._snap_tolerance

    @snap_tolerance.setter
    def snap_tolerance(self, value):
        self._snap_tolerance = value
        self.notify()

    @property
    def min_dist(self):
        return self._min_dist

    @min_dist.setter
    def min_dist(self, value):
        self._min_dist = value
        self.notify()

    @property
    def vertex_dist(self):
        return self._vertex_dist

    @vertex_dist.setter
    def vertex_dist(self, value):
        self._vertex_dist = value
        self.notify()


class ConfigFile:

    # http://www.blog.pythonlibrary.org/2013/10/25/python-101-an-intro-to-configparser/

    def __init__(self, config_file_path):
        self.config = ConfigParser.ConfigParser()
        self.config_file_path = config_file_path

    def create_config(self):
        """
        Create a config file
        """
        self.config.add_section('EPANET')
        self.config.set("patterns_file", '')

        with codecs.open(self.config_file_path, "wb",  'utf-8') as config_file:
            self.config.write(self.config_file_path)

    def get_config(self):
        """
        Returns the config object
        """
        if not os.path.exists(self.config_file_path):
            self.create_config()

        config = ConfigParser.ConfigParser()
        config.read(self.config_file_path)
        return config

    def get_patterns_file_path(self):

        self.config.read(self.config_file_path)
        try:
            patterns_file_path = self.config.get('EPANET', 'patterns_file') # TODO: softcode
        except ConfigParser.NoOptionError as e:
            return None

        return patterns_file_path

    def set_patterns_file_path(self, patterns_file_path):
        config = self.get_config()
        config.set('EPANET', 'patterns_file', patterns_file_path) # TODO: softcode
        with codecs.open(self.config_file_path, 'wb') as configfile:
            config.write(configfile)

    def get_curves_file_path(self):
        self.config.read(self.config_file_path)
        try:
            curves_file_path = self.config.get('EPANET', 'curves_file')  # TODO: softcode
        except ConfigParser.NoOptionError as e:
            return None
        return curves_file_path

    def set_curves_file_path(self, curves_file_path):
        config = self.get_config()
        config.set('EPANET', 'curves_file', curves_file_path)  # TODO: softcode

        with codecs.open(self.config_file_path, 'wb') as configfile:
            config.write(configfile)

    def get_last_inp_file(self):
        self.config.read(self.config_file_path)
        try:
            last_inp_file = self.config.get('EPANET', 'inp_file_path')  # TODO: softcode
        except ConfigParser.NoOptionError as e:
            return None
        return last_inp_file

    def set_last_inp_file(self, last_inp_file):
        config = self.get_config()
        config.set('EPANET', 'inp_file_path', last_inp_file)  # TODO: softcode

        with codecs.open(self.config_file_path, 'wb') as configfile:
            config.write(configfile)

    # Out file
    def get_last_out_file(self):
        self.config.read(self.config_file_path)
        try:
            last_out_file = self.config.get('EPANET', 'out_file_path')  # TODO: softcode
        except ConfigParser.NoOptionError as e:
            return None
        return last_out_file

    def set_last_out_file(self, last_out_file):
        config = self.get_config()
        config.set('EPANET', 'out_file_path', last_out_file)  # TODO: softcode

        with codecs.open(self.config_file_path, 'wb') as configfile:
            config.write(configfile)


class RegExValidators:

    def __init__(self):
        pass

    @staticmethod
    def get_pos_decimals():
        reg_ex = QRegExp(Parameters.regex_number_pos_decimals)
        validator = QRegExpValidator(reg_ex)
        return validator

    @staticmethod
    def get_pos_neg_decimals():

        reg_ex = QRegExp(Parameters.regex_number_pos_neg_decimals)
        validator = QRegExpValidator(reg_ex)
        return validator

    @staticmethod
    def get_pos_int():

        reg_ex = QRegExp(Parameters.regex_number_pos_int)
        validator = QRegExpValidator(reg_ex)
        return validator

    @staticmethod
    def get_pos_01():
        reg_ex = QRegExp(Parameters.regex_number_pos_01)
        validator = QRegExpValidator(reg_ex)
        return validator

    @staticmethod
    def get_pos_int_no_zero():

        reg_ex = QRegExp(Parameters.regex_number_pos_int_no_zero)
        validator = QRegExpValidator(reg_ex)
        return validator

    @staticmethod
    def get_time_hh_mm():

        reg_ex = QRegExp(Parameters.regex_time_hh_mm)
        validator = QRegExpValidator(reg_ex)
        return validator