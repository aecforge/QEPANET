from PyQt4 import QtGui
from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class MyMplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):

        self.figure = Figure(figsize=(width, height), dpi=dpi)
        self.figure.set_facecolor((1, 1, 1))
        self.axes = self.figure.add_subplot(1, 1, 1)
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

    def draw_bars_graph(self, values, time_period=1):

        self.figure.clf()
        self.axes = self.figure.add_subplot(1, 1, 1)

        width = 1
        lefts = []
        max_val = -1
        for l in range(len(values)):
            lefts.append(l * 1)
            max_val = max(values[l], max_val)

        if max_val == 0:
            max_val = 1

        self.axes.bar(lefts, values, width, color=(0, 0.5, 1))
        self.axes.set_xlim(0, lefts[-1] + width)
        self.axes.set_ylim(0, max_val)

        # Common options
        self.axes.set_xlabel('Time (Time period = ' + str(time_period) + ')') #TODO: softcode
        self.axes.set_ylabel('Multiplier') #TODO: softcode
        self.axes.tick_params(axis=u'both', which=u'both', bottom=u'off', top=u'off', left=u'off', right=u'off')
        self.figure.tight_layout()
        self.draw()


