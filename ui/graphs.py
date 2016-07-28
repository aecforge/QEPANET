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

    # def draw_graph_from_stats(self, stats, graph_type, legend=None):
    #     """
    #     :param stats:
    #     :type stats: FormattedRasterStats
    #     :param graph_type:
    #     :param legend:
    #     :return:
    #     """
    #
    #     intervals = stats.intervals
    #
    #     self.figure.clf()
    #     self.axes = self.figure.add_subplot(1, 1, 1)
    #
    #     if graph_type == GraphType.BARS:
    #
    #         width = intervals.items()[1][0] - intervals.items()[0][0]
    #
    #         self.axes.bar(intervals.keys(), intervals.values(), width, color=(0, 0.5, 1))
    #
    #         if len(intervals.keys()) <= 10:
    #             legend_keys = []
    #             legend_pos = []
    #             for key in intervals.keys():
    #                 if legend is not None:
    #                     legend_keys.append(self.multiline(legend[str(int(key))]))
    #                 else:
    #                     legend_keys.append(key)
    #                 legend_pos.append(key + 0.5 * width)
    #
    #             self.axes.set_xticklabels(legend_keys, fontsize=10, rotation=45)
    #             self.axes.set_xticks(legend_pos)
    #
    #     elif graph_type == GraphType.BARS_DISCRETE:
    #
    #         index = np.arange(len(intervals))
    #         bar_width = 1
    #
    #         self.axes.bar(index, intervals.values(), width=1, color=(0, 0.5, 1))
    #
    #         keys = []
    #         rotation = 0
    #         for key in intervals.keys():
    #             if legend is None:
    #                 keys.append(int(key))
    #             else:
    #                 keys.append(self.multiline(legend[str(int(key))]))
    #                 rotation = 45
    #
    #         self.axes.set_xticks(index + 0.5 * bar_width)
    #         self.axes.set_xticklabels(keys, fontsize=10, rotation=rotation)
    #
    #     elif graph_type == GraphType.SCATTER:
    #
    #         # Bisecting line
    #         bis_xs = (0, 1)
    #         bis_ys = (1, 0)
    #
    #         self.axes.plot(bis_xs, bis_ys, '0.7', stats.intervals.keys(), stats.intervals.values())
    #
    #         # Make the x and y axis proportions 1:1
    #         self.axes.set_aspect('equal', 'box')
    #
    #     elif graph_type == GraphType.SCATTER_AVG:
    #
    #         avg_xs = (stats.min_val, stats.max_val)
    #         avg_ys = (stats.avg_val, stats.avg_val)
    #
    #         self.axes.plot(stats.intervals.keys(), stats.intervals.values(), avg_xs, avg_ys)
    #
    #         # Limits
    #         self.axes.set_xlim(stats.min_val, stats.max_val)
    #
    #         # Comment
    #         x_pos = stats.max_val - (stats.max_val + stats.min_val) / 3
    #         y_pos = stats.avg_val + 10
    #         self.axes.annotate('Media: ' + str(stats.avg_val), xy=(x_pos, y_pos), fontsize=8)
    #
    #     # Common options
    #     self.axes.set_title(stats.caption)
    #     self.axes.set_xlabel(stats.headers[0])
    #     self.axes.set_ylabel(stats.headers[1])
    #     self.axes.tick_params(axis=u'both', which=u'both', bottom=u'off', top=u'off', left=u'off', right=u'off')
    #     self.figure.tight_layout()
    #     self.draw()
    #
    # def draw_idf_curves(self, rainfall_vals):
    #
    #     ys = {}
    #     for ret_per in rainfall.ret_periods:
    #         vals = []
    #         for dur in rainfall.durations:
    #             vals.append(rainfall_vals[(ret_per, dur)])
    #         ys[ret_per] = vals
    #
    #     self.axes.plot(
    #             rainfall.durations, ys[2],
    #             rainfall.durations, ys[5],
    #             rainfall.durations, ys[10],
    #             rainfall.durations, ys[30],
    #             rainfall.durations, ys[100],
    #             rainfall.durations, ys[200],
    #             rainfall.durations, ys[300])
    #     self.axes.set_xlabel("Durate [h]")
    #     self.axes.set_ylabel("Precipitazione [mm]")
    #     self.axes.tick_params(axis=u'both', which=u'major', bottom=u'on', top=u'on', left=u'on', right=u'on')
    #     self.axes.grid(axis=u'both', which=u'major')
    #     self.axes.legend(('2', '5', '10', '25', '50', '100', '200'), loc='lower right', fontsize='xx-small')
    #     self.axes.tick_params(labelsize='small')
    #     self.figure.tight_layout()
    #     self.draw()
    #
    # def draw_hydrograph(self, hyetohydros_cns_rps, ret_pers):
    #
    #     self.figure.clf()
    #
    #     subplots_count = len(ret_pers)
    #     plot_pos = 1
    #
    #     discharge_max_y = 0
    #     rainfall_max_y = 0
    #
    #     all_axes = {}
    #     for ret_per in ret_pers:
    #
    #         axes = self.figure.add_subplot(subplots_count, 1, plot_pos)
    #         """:type : Axes"""
    #
    #         if len(ret_pers) > 1:
    #             axes.set_title('TR = ' + str(ret_per))
    #
    #         hyetohydros_cns = hyetohydros_cns_rps[ret_per]
    #         """:type : HyetoHydrograpsCNs"""
    #         hyetohydro_iii = hyetohydros_cns.hyetohydro_cn_iii
    #         """:type : HyetoHydrograph"""
    #
    #         # Recalculate times for even spacing
    #         delta_sum = 0
    #         for t in xrange(1, len(hyetohydro_iii.times)):
    #             delta_sum += hyetohydro_iii.times[t] - hyetohydro_iii.times[t-1]
    #
    #         even_step = delta_sum / (len(hyetohydro_iii.times) - 1)
    #         even_times = []
    #         for t in xrange(len(hyetohydro_iii.times)):
    #             even_times.append((t+1) * even_step)
    #
    #         axes.plot(even_times, hyetohydro_iii.discharge)
    #         axes.set_ylim(bottom=0)
    #
    #         # Find discharge max y
    #         if axes.get_ylim()[1] > discharge_max_y:
    #             discharge_max_y = axes.get_ylim()[1]
    #
    #         # Crate new axis for rainfall
    #         rainfall_axis = axes.twinx()
    #
    #         bars_width = params.ProjectNames.get_out_step_min() / 60
    #         rainfall_axis.bar([x-0.5*bars_width for x in even_times],
    #                           hyetohydro_iii.tot_rain,
    #                           width=bars_width,
    #                           color=(0, 0.5, 0),
    #                           edgecolor = "none")
    #         rainfall_axis.bar([x-0.5*bars_width for x in even_times],
    #                           hyetohydro_iii.eff_rain,
    #                           width=bars_width,
    #                           color=(0.9, 0, 0),
    #                           edgecolor = "none")
    #
    #         # Format primary axis
    #         axes.tick_params(labelsize='small')
    #         if ret_per != ret_pers[subplots_count-1]:
    #             axes.set_xticklabels([])
    #         else:
    #             axes.set_xlabel("Tempo [h]", size='x-small')
    #         axes.set_ylabel("Portata [m3/s]", size='x-small')
    #
    #         # Format secondary axis
    #         rainfall_axis.tick_params(labelsize='small')
    #         rainfall_axis.set_ylabel("Precipitazione [mm]", size='x-small')
    #
    #         # Find rainfall max y
    #         if rainfall_axis.get_ylim()[1] > rainfall_max_y:
    #             rainfall_max_y = rainfall_axis.get_ylim()[1]
    #
    #         all_axes[ret_per] = (axes, rainfall_axis)
    #
    #         plot_pos += 1
    #
    #     # Set same y ranges
    #     plot_pos = 1
    #     for ret_per in ret_pers:
    #         # axes = self.figure.add_subplot(subplots_count, 1, plot_pos)
    #         # """:type : Axes"""
    #         all_axes[ret_per][0].set_ylim(0, discharge_max_y)
    #
    #         # Setting rainfall axis scale and inverting axis
    #         all_axes[ret_per][1].set_ylim(rainfall_max_y * 2, 0)
    #         plot_pos += 1
    #
    #     self.figure.tight_layout(h_pad=0)
    #     self.draw()
    #
    # def multiline(self, text):
    #     return text.replace(" ", "\n")