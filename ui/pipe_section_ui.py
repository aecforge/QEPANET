from PyQt4 import QtGui, QtCore
from graphs import MyMplCanvas
from matplotlib.lines import Line2D
from matplotlib.path import Path
import utils
import matplotlib.patches as patches
import numpy as np


class PipeSectionDialog(QtGui.QDialog):

    def __init__(self, parent, iface, parameters):

        QtGui.QDialog.__init__(self, parent)
        main_lay = QtGui.QVBoxLayout(self)

        self.parent = parent
        self.parameters = parameters

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowTitle('Pipe section editor')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Graph canvas
        self.fra_graph = QtGui.QFrame()
        self.static_canvas = SectionCanvas(iface, parameters)

        main_lay.addWidget(self.static_canvas)

        # DEM and pipe
        dem_xy = {'x': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12), 'y': (11, 10, 9, 8, 7, 6, 5, 5, 6, 7, 8, 9, 10)}
        pipe_xy = {'x': (0, 4, 6, 8, 10, 12), 'y': (5, 4, 3, 2, 1, 3)}

        self.static_canvas.draw_pipe_section(dem_xy, pipe_xy)


class SectionCanvas(MyMplCanvas):

    showverts = True

    def __init__(self, iface, parameters):

        super(self.__class__, self).__init__()

        self.iface = iface
        self.parameters = parameters
        self._ind = 0
        self.pipe_patch = None
        self.pipe_line = None
        self.background = None

        self.epsilon = 10

        self.mpl_connect('draw_event', self.draw_callback)
        self.mpl_connect('button_press_event', self.button_press_callback)
        self.mpl_connect('button_release_event', self.button_release_callback)
        self.mpl_connect('motion_notify_event', self.motion_notify_callback)

    def draw_pipe_section(self, dem_xy, pipe_xy):

        self.figure.clf()
        self.axes = self.figure.add_subplot(1, 1, 1)

        # Pipe patch
        maxs = {'x': 0, 'y': 0}
        vertices = []
        codes = []
        for v in range(len(dem_xy['x'])):
            vertices.append((dem_xy['x'][v], dem_xy['y'][v]))
            maxs['x'] = max(maxs['x'], dem_xy['x'][v])
            maxs['y'] = max(maxs['y'], dem_xy['y'][v])
            codes.append(Path.LINETO)
        codes[0] = Path.MOVETO

        path = Path(vertices, codes)
        self.pipe_patch = patches.PathPatch(path, edgecolor='b', facecolor='none')
        # self.pipe_patch.set_animated(True)

        # Pipe line
        x, y = zip(*self.pipe_patch.get_path().vertices)
        self.pipe_line, = self.axes.plot(x, y, color='r', lw=0.5, marker='o', markerfacecolor='r', animated=True)

        self.axes.add_line(self.pipe_line)
        self.axes.add_patch(self.pipe_patch)

        self.axes.set_xlim(0, maxs['x'])
        self.axes.set_ylim(0, maxs['y'])

        self.pipe_line.add_callback(self.pipe_changed)

        self.axes.set_title('Coatuib')
        map_units = self.iface.mapCanvas().mapUnits if self.iface is not None else '?'
        self.axes.set_xlabel('Distance [' + map_units + ']')
        self.axes.set_ylabel('Elevation')
        self.axes.tick_params(axis=u'both', which=u'both', bottom=u'off', top=u'off', left=u'off', right=u'off')
        self.figure.tight_layout()
        self.draw()

    def draw_callback(self, event):
        self.background = self.copy_from_bbox(self.axes.bbox)
        self.axes.draw_artist(self.pipe_patch)
        self.axes.draw_artist(self.pipe_line)
        # self.blit(self.axes.bbox)

    def pipe_changed(self):
        vis = self.pipe_line.get_visible()
        self.Artist.update_from(self.pipe_line, self.pipe_patch)
        self.pipe_line.set_visible(vis)  # don't use the pathpatch visibility state

    def get_ind_under_point(self, event):

        # display coords
        xy = np.asarray(self.pipe_patch.get_path().vertices)
        xyt = self.pipe_patch.get_transform().transform(xy)
        xt, yt = xyt[:, 0], xyt[:, 1]
        d = np.sqrt((xt - event.x)**2 + (yt - event.y)**2)
        ind = d.argmin()

        if d[ind] >= self.epsilon:
            ind = None

        return ind

    def button_press_callback(self, event):

        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        if not self.showverts:
            return
        if event.button == 2:
            return
        if event.button == 3:

            # Find the distance to the closest vertex
            min_dist = 1E10
            min_pos = -1
            xy = np.asarray(self.pipe_patch.get_path().vertices)
            xyt = self.pipe_patch.get_transform().transform(xy)
            for v in range(1, len(xyt)):
                dist = utils.dist(xyt[v-1][0], xyt[v-1][1], xyt[v][0], xyt[v][1], event.x, event.y)
                if dist < min_dist:
                    min_dist = dist
                    min_pos = v

            if min_dist <= self.epsilon:
                # Create new vertex
                xy = np.asarray((event.x, event.y))
                xyt = self.pipe_patch.get_transform().inverted().transform(xy)
                vertices = self.pipe_patch.get_path().vertices
                vertices = np.insert(vertices, min_pos, xyt, 0)

                codes = []
                for v in range(len(vertices)):
                    codes.append(Path.LINETO)
                codes[0] = Path.MOVETO
                path = Path(vertices, codes)

                self.axes.patches.remove(self.pipe_patch)
                self.pipe_patch = patches.PathPatch(path, edgecolor='b', facecolor='none')
                self.axes.add_patch(self.pipe_patch)

                self.pipe_line.set_data(zip(*vertices))

                self.restore_region(self.background)
                self.axes.draw_artist(self.pipe_patch)
                self.axes.draw_artist(self.pipe_line)
                self.blit(self.axes.bbox)

        self._ind = None

    def motion_notify_callback(self, event):
        if not self.showverts:
            return
        if self._ind is None:
            return
        if event.inaxes is None:
            return
        if event.button != 1:
            return
        x, y = event.xdata, event.ydata

        vertices = self.pipe_patch.get_path().vertices
        vertices[self._ind] = x, y
        self.pipe_line.set_data(zip(*vertices))

        self.restore_region(self.background)
        self.axes.draw_artist(self.pipe_patch)
        self.axes.draw_artist(self.pipe_line)
        self.blit(self.axes.bbox)

