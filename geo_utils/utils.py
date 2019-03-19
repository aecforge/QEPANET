from builtins import object
import os.path
import subprocess

from qgis.core import QgsProject
from ..tools.parameters import Parameters

__author__ = 'deluca'


class Utils(object):

    def __init__(self):
        pass

    @staticmethod
    def launch_without_console(command, args):
        """Launches 'command' windowless and waits until finished"""
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        return subprocess.Popen([command] + args, startupinfo=startupinfo).wait()


class FileUtils(object):

    def __init__(self):
        pass

    @staticmethod
    def paths_are_equal(path1, path2):
        return os.path.normpath(os.path.normcase(path1)) == os.path.normpath(os.path.normcase(path2))


class LayerUtils(object):

    def __init__(self):
        pass

    @staticmethod
    def get_lay_id(layer_name):
        layers = QgsProject.instance().mapLayers()
        for name, layer in layers.items():
            if layer_name in layer.name() and layer.name().startswith(layer_name):
                return layer.id()

    @staticmethod
    def get_lay_from_id(lay_id):
        return QgsProject.instance().mapLayer(lay_id)

    @staticmethod
    def remove_layer_by_name(layer_name):

        layers = QgsProject.instance().mapLayers()
        for name, layer in layers.items():
            if layer_name in name:
                try:
                    QgsProject.instance().removeMapLayers([name])
                except Exception:
                    raise NameError('Cannot remove ' + layer_name + ' layer.')

    @staticmethod
    def remove_layer(layer):
        QgsProject.instance().removeMapLayer(layer.id())

    @staticmethod
    def remove_layers(params):

        # Delete referenced layers
        deleted = {Parameters.dem_rlay: False,
                Parameters.junctions_vlay_name: False,
                Parameters.reservoirs_vlay_name: False,
                Parameters.tanks_vlay_name: False,
                Parameters.pipes_vlay_name: False,
                Parameters.pumps_vlay_name: False,
                Parameters.valves_vlay_name: False}

        if params.junctions_vlay:
            LayerUtils.remove_layer(params.junctions_vlay)
            params.junctions_vlay = None
        if params.reservoirs_vlay:
            LayerUtils.remove_layer(params.reservoirs_vlay)
            params.reservoirs_vlay = None
        if params.tanks_vlay:
            LayerUtils.remove_layer(params.tanks_vlay)
            params.tanks_vlay = None
        if params.pipes_vlay:
            LayerUtils.remove_layer(params.pipes_vlay)
            params.pipes_vlay = None
        if params.pumps_vlay:
            LayerUtils.remove_layer(params.pumps_vlay)
            params.pumps_vlay = None
        if params.valves_vlay:
            LayerUtils.remove_layer(params.valves_vlay)
            params.valves_vlay = None

        # Now delete unreferenced layers
        if not deleted[Parameters.junctions_vlay_name]:
            LayerUtils.remove_layer_by_name(params.junctions_vlay_name)
        if not deleted[Parameters.reservoirs_vlay_name]:
            LayerUtils.remove_layer_by_name(params.reservoirs_vlay_name)
        if not deleted[Parameters.tanks_vlay_name]:
            LayerUtils.remove_layer_by_name(params.tanks_vlay_name)
        if not deleted[Parameters.pipes_vlay_name]:
            LayerUtils.remove_layer_by_name(params.pipes_vlay_name)
        if not deleted[Parameters.pumps_vlay_name]:
            LayerUtils.remove_layer_by_name(params.pumps_vlay_name)
        if not deleted[Parameters.valves_vlay_name]:
            LayerUtils.remove_layer_by_name(params.valves_vlay_name)