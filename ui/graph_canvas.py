import numpy as np
from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.axes import Axes

__author__ = 'deluca'


class MyMplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):

        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.set_facecolor((1, 1, 1))
        self.axes = self.figure.add_subplot(1, 1, 1)
        # We want the axes cleared every time plot() is called
        self.axes.set_axis_bgcolor((1, 1, 1))
        self.axes.hold(False)
        self.compute_initial_figure()
        FigureCanvas.__init__(self, self.figure)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QtGui.QSizePolicy.Expanding,
                                   QtGui.QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class StaticMplCanvas(MyMplCanvas):

    def compute_initial_figure(self):
        pass

    def draw_hydrograph(self, hyetohydros_cns_rps, ret_pers):

        self.figure.clf()

        subplots_count = len(ret_pers)
        plot_pos = 1

        discharge_max_y = 0
        rainfall_max_y = 0

        all_axes = {}
        for ret_per in ret_pers:

            axes = self.figure.add_subplot(subplots_count, 1, plot_pos)
            """:type : Axes"""

            if len(ret_pers) > 1:
                axes.set_title('TR = ' + str(ret_per))

            hyetohydros_cns = hyetohydros_cns_rps[ret_per]
            """:type : HyetoHydrograpsCNs"""
            hyetohydro_iii = hyetohydros_cns.hyetohydro_cn_iii
            """:type : HyetoHydrograph"""

            # Recalculate times for even spacing
            delta_sum = 0
            for t in xrange(1, len(hyetohydro_iii.times)):
                delta_sum += hyetohydro_iii.times[t] - hyetohydro_iii.times[t-1]

            even_step = delta_sum / (len(hyetohydro_iii.times) - 1)
            even_times = []
            for t in xrange(len(hyetohydro_iii.times)):
                even_times.append((t+1) * even_step)

            axes.plot(even_times, hyetohydro_iii.discharge)
            axes.set_ylim(bottom=0)

            # Find discharge max y
            if axes.get_ylim()[1] > discharge_max_y:
                discharge_max_y = axes.get_ylim()[1]

            # Crate new axis for rainfall
            rainfall_axis = axes.twinx()

            # Format primary axis
            axes.tick_params(labelsize='small')
            if ret_per != ret_pers[subplots_count-1]:
                axes.set_xticklabels([])
            else:
                axes.set_xlabel("Tempo [h]", size='x-small')
            axes.set_ylabel("Portata [m3/s]", size='x-small')

            # Format secondary axis
            rainfall_axis.tick_params(labelsize='small')
            rainfall_axis.set_ylabel("Precipitazione [mm]", size='x-small')

            # Find rainfall max y
            if rainfall_axis.get_ylim()[1] > rainfall_max_y:
                rainfall_max_y = rainfall_axis.get_ylim()[1]

            all_axes[ret_per] = (axes, rainfall_axis)

            plot_pos += 1

        # Set same y ranges
        plot_pos = 1
        for ret_per in ret_pers:
            # axes = self.figure.add_subplot(subplots_count, 1, plot_pos)
            # """:type : Axes"""
            all_axes[ret_per][0].set_ylim(0, discharge_max_y)

            # Setting rainfall axis scale and inverting axis
            all_axes[ret_per][1].set_ylim(rainfall_max_y * 2, 0)
            plot_pos += 1

        # self.figure.tight_layout(h_pad=0)
        self.draw()

    def multiline(self, text):
        return text.replace(" ", "\n")


def export_png(static_canvas):
    pass
    # file_name = QtGui.QFileDialog.getSaveFileName(None,
    #                                                'Salva',
    #                                                ProjectNames.get_output_path(),
    #                                                'File JPG (*.jpg)')
    #
    # if file_name is not None and file_name != '':
    #     static_canvas.figure.savefig(file_name, format='jpg')
