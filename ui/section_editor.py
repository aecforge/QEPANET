from qgis.core import QgsPoint, QgsGeometry, QgsPointV2, QgsLineStringV2, QgsWKBTypes, QgsVertexId
from PyQt4 import QtCore
from PyQt4.QtGui import QDialog, QVBoxLayout, QFrame, QHBoxLayout, QPushButton, QIcon
from graphs import MyMplCanvas
from ..geo_utils import bresenham, raster_utils
from ..model.network_handling import LinkHandler
from matplotlib.lines import Line2D
from matplotlib.path import Path
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QT
from collections import OrderedDict
import utils
import matplotlib.patches as patches
import numpy as np
import math
import os
from utils import set_up_button


class PipeSectionDialog(QDialog):

    def __init__(self, parent, iface, params, pipe_ft):

        QDialog.__init__(self, parent)
        main_lay = QVBoxLayout(self)

        self.parent = parent
        self.params = params
        self.pipe_ft = pipe_ft

        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setWindowTitle('Pipe section editor')  # TODO: softcode
        self.setWindowModality(QtCore.Qt.ApplicationModal)

        curr_dir = os.path.dirname(os.path.abspath(__file__))

        self.fra_toolbar = QFrame(self)
        fra_toolbar_lay = QHBoxLayout(self.fra_toolbar)
        self.btn_zoom = QPushButton('Zoom')
        self.btn_zoom.clicked.connect(self.btn_zoom_clicked)
        set_up_button(self.btn_zoom, os.path.join(curr_dir, 'i_zoom.png'), 13, 13,
                      'Zoom')  # TODO: softcode

        self.btn_pan = QPushButton('Pan')
        self.btn_pan.clicked.connect(self.btn_pan_clicked)
        set_up_button(self.btn_pan, os.path.join(curr_dir, 'i_pan.png'), 15, 15,
                      'Pan')  # TODO: softcode

        self.btn_home = QPushButton('Full extent')
        self.btn_home.clicked.connect(self.btn_home_clicked)

        self.btn_back = QPushButton('Back')
        self.btn_back.clicked.connect(self.btn_back_clicked)
        set_up_button(self.btn_back, os.path.join(curr_dir, 'i_back.png'), 7, 13,
                      'Back')  # TODO: softcode

        self.btn_forth = QPushButton('Forth')
        self.btn_forth.clicked.connect(self.btn_forth_clicked)
        set_up_button(self.btn_forth, os.path.join(curr_dir, 'i_forth.png'), 7, 13,
                      'Forward')  # TODO: softcode

        self.btn_edit = QPushButton('Edit')
        self.btn_edit.clicked.connect(self.btn_edit_clicked)

        fra_toolbar_lay.addWidget(self.btn_zoom)
        fra_toolbar_lay.addWidget(self.btn_pan)
        fra_toolbar_lay.addWidget(self.btn_home)
        fra_toolbar_lay.addWidget(self.btn_back)
        fra_toolbar_lay.addWidget(self.btn_forth)
        fra_toolbar_lay.addWidget(self.btn_edit)

        # Graph canvas
        self.fra_graph = QFrame(self)
        self.static_canvas = SectionCanvas(iface, parameters, self)

        # Toolbar
        self.toolbar = NavigationToolbar2QT(self.static_canvas, self)
        self.toolbar.hide()

        # OK/Cancel buttons
        self.fra_buttons = QFrame(self)
        fra_buttons_lay = QHBoxLayout(self.fra_buttons)
        self.btn_Cancel = QPushButton('Cancel')
        self.btn_Ok = QPushButton('OK')
        fra_buttons_lay.addWidget(self.btn_Cancel)
        fra_buttons_lay.addWidget(self.btn_Ok)

        main_lay.addWidget(self.fra_toolbar)
        main_lay.addWidget(self.static_canvas)
        main_lay.addWidget(self.fra_buttons)

        self.setup()
        self.initialize()

    def setup(self):

        # Buttons
        self.btn_Cancel.pressed.connect(self.btn_cancel_pressed)
        self.btn_Ok.pressed.connect(self.btn_ok_pressed)

    def initialize(self):

        dem_xz = self.find_raster_distz()
        pipe_xz = self.find_line_distz()
        self.static_canvas.draw_pipe_section(dem_xz, pipe_xz)

    def btn_home_clicked(self):
        self.toolbar.home()

    def btn_zoom_clicked(self):
        self.toolbar.zoom()

    def btn_pan_clicked(self):
        self.toolbar.pan()

    def btn_back_clicked(self):
        self.toolbar.back()

    def btn_forth_clicked(self):
        self.toolbar.forward()

    def btn_edit_clicked(self):
        # Deactivate tools
        if self.toolbar._active == "PAN":
            self.toolbar.pan()
        elif self.toolbar._active == "ZOOM":
            self.toolbar.zoom()

    def btn_cancel_pressed(self):
        self.setVisible(False)

    def btn_ok_pressed(self):
        new_zs = self.static_canvas.pipe_line.get_ydata()
        pipe_geom_v2 = self.pipe_ft.geometry().geometry()
        for p in range(pipe_geom_v2.vertexCount(0, 0)):
            vertex_id = QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex)
            vertex = pipe_geom_v2.vertexAt(vertex_id)
            new_pos_pt = QgsPointV2(vertex.x(), vertex.y())
            new_pos_pt.addZValue(new_zs[p])

            LinkHandler.move_pipe_vertex(self.params, self.pipe_ft, new_pos_pt, p)

        self.setVisible(False)

    def find_line_distz(self):

        pipe_geom_v2 = self.pipe_ft.geometry().geometry()
        total_dist = 0
        dist_z = OrderedDict()
        dist_z[total_dist] = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, 0, QgsVertexId.SegmentVertex)).z()
        for p in range(1, pipe_geom_v2.vertexCount(0, 0)):
            vertex = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p, QgsVertexId.SegmentVertex))
            vertex_prev = pipe_geom_v2.vertexAt(QgsVertexId(0, 0, p-1, QgsVertexId.SegmentVertex))
            total_dist += math.sqrt((vertex.x() - vertex_prev.x())**2 + (vertex.y() - vertex_prev.y())**2)
            dist_z[total_dist] = vertex.z()

        return dist_z

    def find_raster_distz(self):

        dem_extent = self.params.dem_rlay.extent()
        ul_coord = QgsPoint(dem_extent.xMinimum(), dem_extent.yMaximum())
        x_cell_size = self.params.dem_rlay.rasterUnitsPerPixelX()
        y_cell_size = -self.params.dem_rlay.rasterUnitsPerPixelY()

        points = []

        pipe_pts = self.pipe_ft.geometry().asPolyline()
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

    def __init__(self, iface, params, parent):

        super(self.__class__, self).__init__()

        self.iface = iface
        self.params = params
        self.parent = parent

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

        if self.parent.toolbar._active is not None:
            return

        if not self.showverts:
            return
        if event.inaxes is None:
            return
        if event.button != 1 and event.button != 3:
            return
        self._ind = self.get_ind_under_point(event)

    def button_release_callback(self, event):

        if self.parent.toolbar._active is not None:
            return

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

        if self.parent.toolbar._active is not None:
            return

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
