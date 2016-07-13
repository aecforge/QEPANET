import os, codecs, ConfigParser

class Parameters:

    plug_in_name = 'QEPANET 0.01'

    config_file_name = 'config.ini'

    max_node_eid = -1

    junctions_vlay = None
    pipes_vlay = None
    pumps_vlay = None
    reservoirs_vlay = None
    tanks_vlay = None
    valves_vlay = None

    dem_rlay = None

    patterns = {}

    tolerance = 1e-8

    config_file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), config_file_name)

    def __init__(self):
        pass


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
            self.create_config(self.config_file_path)

        config = ConfigParser.ConfigParser()
        config.read(self.config_file_path)
        return config

    def get_patterns_file_path(self):

        self.config.read(self.config_file_path)
        patterns_file_path = self.config.get('EPANET', 'patterns_file') # TODO: softcode
        return patterns_file_path

    def set_patterns_file_path(self, patterns_file_path):
        config = self.get_config()
        config.set('EPANET', 'patterns_file', patterns_file_path) # TODO: softcode

        with codecs.open(self.config_file_path, 'wb') as configfile:
            config.write(configfile)