import os
import platform
import subprocess
import tempfile


# Many parts taken from GHydraulics (http://epanet.de/ghydraulics/index.html.en)
class ModelRunner:

    def __init__(self, dockwidget):

        self.bin_folder_name = 'bin'
        self.epanet_binary = None
        self.epanet_file_name = 'epanet2d'
        self.osx_folder_name = 'osx'
        self.dockwidget = dockwidget

    def run(self, inp_file, rpt_file, out_binary_file):

        # self.epanet_binary = 'C:/Program Files (x86)/EPANET2/epanet2d.exe'  # TODO: replace

        self.set_epanet_binary()
        self.dockwidget.txt_epanet_console.clear()

        out = tempfile.mkstemp(suffix='.out')
        err = tempfile.mkstemp(suffix='.err')
        input = tempfile.mkstemp(suffix='.input')

        p = subprocess.Popen(
            [self.epanet_binary, inp_file, rpt_file, out_binary_file],
            cwd=tempfile.gettempdir(), stdin=input[0], stdout=subprocess.PIPE, stderr=err[0])

        while True:
            line = p.stdout.readline()
            if not line:
                break

            self.dockwidget.txt_epanet_console.appendPlainText(line.replace('\b', ''))

        os.close(out[0])
        os.close(err[0])
        os.close(input[0])

    def set_epanet_binary(self):

        plugin_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        bin_path = os.path.join(plugin_path, self.bin_folder_name)

        if platform.mac_ver()[0] != '':
            # Mac
            self.epanet_binary = os.path.join(bin_path, self.osx_folder_name, self.epanet_file_name)
        else:
            arch = platform.architecture()
            self.epanet_binary = os.path.join(bin_path, arch[0], arch[1], self.epanet_file_name)
            if arch[1] == 'WindowsPE':
                self.epanet_binary += '.exe'

        if not os.path.isfile(self.epanet_binary):
            raise Exception('Could not determine system architecture.')

        try:
            os.chmod(self.epanet_binary, 0o755)
        except:
            raise Exception('Failed to set file permissions for ' + self.epanet_file_name)
