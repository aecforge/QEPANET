import os.path
import subprocess

from qgis.core import QgsMapLayerRegistry

__author__ = 'deluca'


class Utils:

    def __init__(self):
        pass

    @staticmethod
    def launch_without_console(command, args):
        """Launches 'command' windowless and waits until finished"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen([command] + args, startupinfo=startupinfo).wait()


class FileUtils:

    def __init__(self):
        pass

    @staticmethod
    def paths_are_equal(path1, path2):
        return os.path.normpath(os.path.normcase(path1)) == os.path.normpath(os.path.normcase(path2))


class LayerUtils:

    def __init__(self):
        pass

    @staticmethod
    def get_lay_id(layer_name):
        layers = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layers.iteritems():
            if layer_name in layer.name() and layer.name().startswith(layer_name):
                return layer.id()

    @staticmethod
    def get_lay_from_id(lay_id):
        return QgsMapLayerRegistry.instance().mapLayer(lay_id)

    @staticmethod
    def remove_layer(layer_name):
        layers = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layers.iteritems():
            if layer_name in name:
                try:
                    QgsMapLayerRegistry.instance().removeMapLayers([name])
                except Exception:
                    raise NameError('Cannot remove ' + layer_name + ' layer.')