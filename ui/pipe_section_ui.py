from qgis.core import QgsPoint
from PyQt4 import QtGui, QtCore
from graphs import MyMplCanvas
from ..geo_utils import bresenham, raster_utils
from matplotlib.lines import Line2D
from matplotlib.path import Path
from collections import OrderedDict
import utils
import matplotlib.patches as patches
import numpy as np
import math


class PipeSectionDialog(QtGui.QDialog):

    def __init__(self, parent, iface, parameters, pipe_ft):

        QtGui.QDialog.__init__(self, parent)
        main_lay = QtGui.QVBoxLayout(self)

        self.parent = parent
        self.params = parameters

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowTitle('Pipe section editor')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        # Graph canvas
        self.fra_graph = QtGui.QFrame()
        self.static_canvas = SectionCanvas(iface, parameters)

        main_lay.addWidget(self.static_canvas)

        # DEM and pipe
        # dem_xy = {'x': (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12),'y': (11, 10, 9, 8, 7, 6, 5, 5, 6, 7, 8, 9, 10)}
        # pipe_xy = {'x': (0, 4, 6, 8, 10, 12), 'y': (5, 4, 3, 2, 1, 3)}

        dem_xz = self.find_raster_distz(pipe_ft)
        pipe_xz = self.find_line_distz(pipe_ft)

        self.static_canvas.draw_pipe_section(dem_xz, pipe_xz)

    def find_line_distz(self, pipe_ft):

        pipe_pts = pipe_ft.geometry().asPolyline()
        total_dist = 0
        dist_z = OrderedDict()
        dist_z[total_dist] = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, pipe_pts[0])
        for p in range(1, len(pipe_pts)):
            total_dist += math.sqrt((pipe_pts[p].x() - pipe_pts[p-1].x())**2 + (pipe_pts[p].y() - pipe_pts[p-1].y())**2)
            dist_z[total_dist] = raster_utils.read_layer_val_from_coord(self.params.dem_rlay, pipe_pts[p])

        return dist_z

    def find_raster_distz(self, pipe_ft):

        dem_extent = self.params.dem_rlay.extent()
        ul_coord = QgsPoint(dem_extent.xMinimum(), dem_extent.yMaximum())
        x_cell_size = self.params.dem_rlay.rasterUnitsPerPixelX()
        y_cell_size = -self.params.dem_rlay.rasterUnitsPerPixelY()

        points = []

        pipe_pts = pipe_ft.geometry().asPolyline()
        for p in range(1, len(pipe_pts)):
            start_col_row = raster_utils.get_col_row(pipe_pts[p-1], ul_coord, x_cell_size, y_cell_size)
            end_col_row = raster_utils.get_col_row(pipe_pts[p], ul_coord, x_cell_size, y_cell_size)

            points.extend(bresenham.get_line((start_col_row.x, start_col_row.y), (end_col_row.x, end_col_row.y)))

        total_dist = 0
        dist_z = OrderedDict()
        dist_z[total_dist] = raster_utils.read_layer_val_from_coord(
            self.params.dem_rlay,
            raster_utils.get_coords(points[0][0], points[0][1], ul_coord, x_cell_size, y_cell_size))

        for p in range(1, len(points)):
            total_dist += math.sqrt((points[p][0] - points[p - 1][0]) ** 2 + (points[p][1] - points[p - 1][1]) ** 2)
            dist_z[total_dist] = raster_utils.read_layer_val_from_coord(
                self.params.dem_rlay,
                raster_utils.get_coords(points[p][0], points[p][1], ul_coord, x_cell_size, y_cell_size))

        return dist_z


class SectionCanvas(MyMplCanvas):

    showverts = True

    def __init__(self, iface, parameters):

        super(self.__class__, self).__init__()

        self.iface = iface
        self.parameters = parameters
        self._ind = 0
        self.dem_line = None
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

        # DEM line
        self.dem_line, = self.axes.plot(dem_xy.keys(), dem_xy.values(), color='brown', lw=1)

        # Pipe patch
        path, maxs = self.build_path(pipe_xy.keys(), pipe_xy.values())
        self.pipe_patch = patches.PathPatch(path, edgecolor='b', facecolor='none')
        # self.pipe_patch.set_animated(True)

        # Pipe line
        x, y = zip(*self.pipe_patch.get_path().vertices)
        self.pipe_line, = self.axes.plot(x, y, color='r', lw=0.5, marker='o', markerfacecolor='r', animated=True)

        self.axes.add_line(self.dem_line)
        self.axes.add_line(self.pipe_line)
        self.axes.add_patch(self.pipe_patch)

        self.axes.set_xlim(0, maxs['x'])
        self.axes.set_ylim(0, maxs['y'])

        self.pipe_line.add_callback(self.pipe_changed)

        # self.axes.set_title('Coatuib')
        map_units = self.iface.mapCanvas().mapUnits() if self.iface is not None else '?'
        self.axes.set_xlabel('Distance [' + str(map_units) + ']')
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
        if event.button != 1 and event.button != 3:
            return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):
        if not self.showverts:
            return
        if event.button == 2:
            return
        if event.button == 3:

            if self._ind is None:
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
            else:
                # Delete vertex
                vertices = self.pipe_patch.get_path().vertices
                vertices = np.delete(vertices, self._ind, axis=0)
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

    def build_path(self, xs, ys):

        maxs = {'x': 0, 'y': 0}
        vertices = []
        codes = []
        for v in range(len(xs)):
            vertices.append((xs[v], ys[v]))
            maxs['x'] = max(maxs['x'], xs[v])
            maxs['y'] = max(maxs['y'], ys[v])
            codes.append(Path.LINETO)
        codes[0] = Path.MOVETO

        path = Path(vertices, codes)
        return path, maxs
