# -*- coding: utf-8 -*-

import collections
import csv
import math
import numpy
import ogr
import PyQt4
import subprocess
import sys
from osgeo import gdal
from osgeo.gdalconst import *
from numpy import array
from PyQt4.QtCore import QFileInfo
from qgis.core import QgsMapLayerRegistry, QgsPoint, QgsRasterLayer, QgsRaster
from utils import Utils
import codecs, struct

__author__ = 'deluca'


class IntPoint:

    x = 0
    y = 0

    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class GeoTransform:

    ul_coordinate = None
    x_cell_size = None
    y_cell_size = None

    def __init__(self, gdal_geotransform=None, ur_coordinate=None, x_cell_size=None, y_cell_size=None):
        if gdal_geotransform is not None:
            left_x = gdal_geotransform[0]
            self.x_cell_size = gdal_geotransform[1]
            top_y = gdal_geotransform[3]
            self.y_cell_size = gdal_geotransform[5]
            self.ul_coordinate = QgsPoint(left_x, top_y)
        else:
            self.ul_coordinate = ur_coordinate
            self.x_cell_size = x_cell_size
            self.y_cell_size = y_cell_size

    def get_ll_coordinate(self, rows_count):
        return QgsPoint(self.ul_coordinate.x(), self.ul_coordinate.y - rows_count * self.y_cell_size)

    def gdal(self):
        return self.ul_coordinate.x, self.x_cell_size, 0, self.ul_coordinate.y, 0, -self.y_cell_size


class SimpleRaster:

    data = None
    cols_count = None
    rows_count = None
    no_data = None
    geotransform = None
    stats = None

    def __init__(self, data, no_data, geotransform):
        self.data = data
        self.rows_count = data.shape[0]
        self.cols_count = data.shape[1]
        self.no_data = no_data
        self.geotransform = geotransform

    def get_val_from_cr(self, col, row):
        return self.data[row, col]

    def get_val_from_coord(self, coordinate):
        point_cr = get_col_row_geotrans(coordinate, self.geotransform)
        return self.data[point_cr.y, point_cr.x]

    def cell_is_nodata(self, col, row):
        if self.data[row][col] != self.no_data and not math.isnan(self.data[row][col]):
            return False
        else:
            return True

    def val_is_nodata(self, val):
        if val != self.no_data:
            return False
        else:
            return True

    def from_cr_to_coord(self, col, row):
        return get_coords(col, row, self.geotransform)

    def from_coord_to_cr(self, coordinate):
        return get_col_row_geotrans(coordinate, self.geotransform)

    def get_stats(self):
        if self.stats is None:
            self.calc_stats()
        return self.stats;

    def calc_stats(self):

        min_val = sys.float_info.max
        max_val = -sys.float_info.max
        cells_count = 0
        sum_val = 0

        for row in range(self.rows_count):
            for col in range(self.cols_count):
                val = self.data[row, col]
                if not self.val_is_nodata(val):
                    if val < min_val:
                        min_val = val
                    if val > max_val:
                        max_val = val
                    cells_count += 1
                    sum_val += val

        avg_val = sum_val / cells_count
        self.stats = RasterStats(min_val, max_val, avg_val)


class RasterStats():

    min_val = None
    max_val = None
    avg_val = None

    def __init__(self, min_val, max_val, avg_val):
        self.min_val = min_val
        self.max_val = max_val
        self.avg_val = avg_val


def clip(in_raster, in_shp, out_raster):
    """
    :type in_raster: String
    :type in_shp: String
    :type out_raster: String
    :return: None
    """
    ds = ogr.Open(in_shp)
    layer = ds.GetLayer(0)

    layer.ResetReading()
    ft = layer.GetNextFeature()

    while ft:
        Utils.launch_without_console(
            'gdalwarp',
            [in_raster, out_raster, '-cutline', in_shp, '-crop_to_cutline', '-overwrite', '-dstnodata', '-9999'])
        ft = layer.GetNextFeature()


def write_geotiff_1b(tiff_path, np_data, transform, no_data, projection):
    """
    :type tiff_path: String
    :type np_data: numpy.array
    :type transform: list
    :rtype:
    """

    cols_count = np_data.shape[1]
    rows_count = np_data.shape[0]

    driver = gdal.GetDriverByName("GTiff")
    out_ds = driver.Create(tiff_path, cols_count, rows_count, 1, GDT_Int32)
    if out_ds is None:
        raise NameError('Cannot create raster')

    out_ds.SetGeoTransform(transform)
    out_ds.SetProjection(projection)

    out_band = out_ds.GetRasterBand(1)
    out_band.WriteArray(np_data, 0, 0)

    out_band.SetNoDataValue(no_data)
    out_band.FlushCache()


def get_coords(col, row, geotransform):
    """
    :type col: int
    :type row: int
    :type geotransform: GeoTransform
    :rtype: QgsPoint
    """

    x = geotransform.ul_coordinate.x() + col * geotransform.x_cell_size + row * 0 + geotransform.x_cell_size * 0.5
    y = geotransform.ul_coordinate.y() + col * 0 + row * geotransform.y_cell_size + geotransform.y_cell_size * 0.5

    return QgsPoint(x, y)


def get_col_row_geotrans(coord, geotransform):
    """
    :type coord: QgsPoint
    :type geotransform: GeoTransform
    :rtype: IntPoint
    """

    int_point = IntPoint()
    int_point.x = int((coord.x() - geotransform.ul_coordinate.x()) / geotransform.x_cell_size)
    int_point.y = int((coord.y() - geotransform.ul_coordinate.y()) / geotransform.y_cell_size)

    # int_point = IntPoint()
    # int_point.x = int((coord.x() - geotransform[0]) / geotransform[1])
    # int_point.y = int((coord.y() - geotransform[3]) / geotransform[5])

    # int_point = IntPoint()
    # int_point.x = int(math.floor((coord.x() - ll_corner.x()) / cell_size))
    # int_point.y = rows_count - int(math.floor((coord.y() - ll_corner.y()) / cell_size) + 1)

    return int_point


def load_simpleraster(raster_path):

    raster_gdal = gdal.Open(raster_path)
    band = raster_gdal.GetRasterBand(1)
    data = numpy.array(band.ReadAsArray())
    band = raster_gdal.GetRasterBand(1)
    no_data = band.GetNoDataValue()

    gdal_trans = raster_gdal.GetGeoTransform()
    rows_count = data.shape[0]
    cols_count = data.shape[1]
    ll_x = gdal_trans[0]
    ul_y = gdal_trans[3]

    cell_size_x = gdal_trans[1]
    cell_size_y = -gdal_trans[5]

    ll_corner = QgsPoint(ll_x, ul_y - rows_count * cell_size_y)

    geotransform = GeoTransform(gdal_trans)
    return SimpleRaster(data, no_data, geotransform)


def load_raster_to_layer(raster_path, layer_name):
    rlayer = QgsRasterLayer(raster_path, layer_name)
    if not rlayer.isValid():
        raise NameError("Layer failed to load!")
    QgsMapLayerRegistry.instance().addMapLayer(rlayer)
    return rlayer


def in_extent(raster, cell_cr):
    """
    :type raster: SimpleRaster
    :type cell_cr: IntPoint
    :param raster:
    :param cell_cr:
    :return:
    """

    return 0 <= cell_cr.x < raster.cols_count and 0 <= cell_cr.y < raster.rows_count


def read_file_val_from_coord(ras_path, coordinate, band=1):

    dataset = gdal.Open(ras_path)
    geotransform = dataset.GetGeoTransform()
    band = dataset.GetRasterBand(1)

    px = int((coordinate.x() - geotransform[0]) / geotransform[1]) #x pixel
    py = int((coordinate.y() - geotransform[3]) / geotransform[5]) #y pixel

    val = band.ReadAsArray(px, py, 1, 1)
    return val[0][0]


def read_layer_val_from_coord(ras_layer, coordinate, band):

    if ras_layer is None:
        return None

    identify_dem = ras_layer.dataProvider().identify(coordinate, QgsRaster.IdentifyFormatValue)
    if identify_dem is not None and identify_dem.isValid() and identify_dem.results().get(1) is not None:
        return identify_dem.results().get(band)
    else:
        return None


class FormattedRasterStats:

    min_val = 0
    max_val = 0
    avg_val = 0
    intervals = None
    total_area_units = 0
    labels = None
    caption = None
    headers = None

    def __init__(self, min_val, max_val, avg_val, intervals, total_area_units, labels=None, caption='-', headers=('-', '-')):
        self.min_val = min_val
        self.max_val = max_val
        self.avg_val = avg_val
        self.intervals = intervals
        self.total_area_units = total_area_units
        self.labels = labels
        self.caption = caption
        self.headers = headers


def calc_area_stats_km2_continuous(raster, interval_width=None, intervals_count=None, caption='-', headers=('-', '-')):
    """
    :type raster: SimpleRaster
    :type intervals_count: int
    :rtype: collections.OrderedDict
    """

    # Find min and max elevation
    min_val = sys.float_info.max
    max_val = -min_val
    sum_val = 0
    num_cells = 0
    for r in range(raster.rows_count):
        for c in range(raster.cols_count):
            if not raster.cell_is_nodata(c, r):
                val = raster.get_val_from_cr(c, r)
                sum_val += val
                num_cells += 1
                if val < min_val:
                    min_val = val
                if val > max_val:
                    max_val = val

    avg_val = sum_val / num_cells

    # Fixed width
    intervals = collections.OrderedDict()
    if interval_width is not None:

        min_intv = (int(min_val / interval_width))*interval_width
        max_intv = (int(max_val / interval_width))*interval_width
        intervals_count = int(max_intv / interval_width+1)

        for i in range(intervals_count):
            intervals[interval_width*i + interval_width * 0.5] = 0

    # Fixed number
    else:
        if intervals_count is None:
            intervals_count = 20

        class_width = (max_val - min_val) / intervals_count
        for i in range(intervals_count):
            intervals[min_val + i*class_width + class_width] = 0

    cell_area_km2 = raster.geotransform.x_cell_size * -raster.geotransform.y_cell_size / 1E6

    for r in range(raster.rows_count):
        for c in range (raster.cols_count):
            if not raster.cell_is_nodata(c, r):
                for lim in intervals:
                    if raster.get_val_from_cr(c, r) <= lim:
                        intervals[lim] += cell_area_km2
                        break

    return FormattedRasterStats(min_val, max_val, avg_val, intervals, num_cells * cell_area_km2, None, caption, headers)


def calc_area_stats_km2_discrete(raster, caption='-', headers=['-','-']):
    """
    :type raster: SimpleRaster
    :rtype: collections.OrderedDict
    """

    min_val = sys.float_info.max
    max_val = -min_val
    sum_val = 0
    num_cells = 0
    intervals = collections.OrderedDict()
    for row in range(raster.rows_count):
        for col in range(raster.cols_count):
            val = raster.get_val_from_cr(col, row)
            if not raster.val_is_nodata(val):
                if val not in intervals:
                    intervals[val] = 1
                else:
                    intervals[val] += 1
                num_cells += 1
                if val < min_val:
                    min_val = val
                if val > max_val:
                    max_val = val

    avg_val = sum_val / num_cells

    cell_area_km2 = math.fabs(raster.geotransform.x_cell_size * raster.geotransform.y_cell_size) / 1E6
    area_units = num_cells * cell_area_km2

    for key, value in intervals.iteritems():
        intervals[key] = value * cell_area_km2

    return FormattedRasterStats(min_val, max_val, avg_val, collections.OrderedDict(sorted(intervals.items())), area_units, None, caption, headers)


def write_stats(txt_file_path, raster_stats, x_dec_places=3, y_dec_places=4, legend=None):
    """
    :type txt_file_path: str
    :type raster_stats: FormattedRasterStats
    :type x_dec_places: int
    :type y_dec_places: int
    :rtype: None
    """

    x_form = '{0:.' + str(x_dec_places) + 'f}'
    y_form = '{0:.' + str(y_dec_places) + 'f}'

    with codecs.open(txt_file_path, 'w', encoding='utf-8') as tfile:
        tfile.write(raster_stats.caption + "\n")
        tfile.write('Min,' + y_form.format(raster_stats.min_val) + '\n')
        tfile.write('Max,' + y_form.format(raster_stats.max_val) + '\n')
        tfile.write('Avg,' + y_form.format(raster_stats.avg_val) + '\n')
        tfile.write('Area,' + y_form.format(raster_stats.total_area_units) + '\n')

        tfile.write(",".join(raster_stats.headers) + "\n")

        for key, value in raster_stats.intervals.iteritems():
            legend_val = ''
            if legend is not None and str(int(key)) in legend:
                legend_val = ',' + legend[str(int(key))]
            tfile.write(x_form.format(key) + "," + y_form.format(value) + legend_val + '\n')


def read_stats(txt_file_path):

    with codecs.open(txt_file_path, 'r', encoding='UTF-8') as tfile:
        lines = tfile.read().splitlines()

        caption = lines[0]
        min_val = float(lines[1].split(',', 2)[1])
        max_val = float(lines[2].split(',', 2)[1])
        avg = float(lines[3].split(',', 2)[1])
        area = float(lines[4].split(',', 2)[1])

        headers = lines[5].split(',', 2)

        intervals = collections.OrderedDict()
        legend = {}
        for line in lines[6:]:
            words = line.split(",", 2)
            key = float(words[0])
            val = float(words[1])
            if len(words) > 2:
                legend[key] = words[2]
            intervals[key] = val

        if not legend:
            legend = None

    return FormattedRasterStats(min_val, max_val, avg, collections.OrderedDict(sorted(intervals.items())), area, legend, caption, headers)


class Cn123:
    cnII = 0
    cnI = 0
    cnIII = 0

    def __init__(self, cnII, cnI, cnIII):
        self.cnII = cnII
        self.cnI = cnI
        self.cnIII = cnIII


def calc_avg_cn(ras_cn):
    """
    :type ras_cn: SimpleRaster
    :rtype: Cn123
    """

    cnII_sum = 0
    cnI_sum = 0
    cnIII_sum = 0
    cells_count = 0

    for r in range(ras_cn.rows_count):
        for c in range(ras_cn.cols_count):
            if not ras_cn.cell_is_nodata(c, r):
                cn = ras_cn.get_val_from_cr(c, r)
                cnII_sum += cn
                cnI_sum += (4.2 * cn) / (10 - 0.058 * cn)
                cnIII_sum += (23.0 * cn) / (10 + 0.13 * cn)
                cells_count += 1

    return Cn123(cnII_sum/cells_count, cnI_sum/cells_count, cnIII_sum/cells_count)


def read_legend(legend_txt_path):

    with open(legend_txt_path, 'r') as lfile:
        lines = lfile.read().splitlines()

        legend = dict()
        for line in csv.reader(lines, quotechar='"', delimiter=",",quoting=csv.QUOTE_ALL, skipinitialspace=True):
            legend[line[0]] = line[1]

    return legend


