import math
from collections import OrderedDict


class PointsAlongLineGenerator:

    def __init__(self, line_geom):
        self.line_geom = line_geom

    def get_points_coords(self, interval, exclude_ends=False):

        # TODO: account for start_node / end_node for direction?

        points = OrderedDict()
        length = self.line_geom.length()
        points_nr = int(math.ceil(length / interval) + 1)
        start = 0
        end = points_nr
        if exclude_ends:
            start += 1
            end -= 1
            if start < 0:
                start = 0
            if end < 1:
                end = 1
            if end > points_nr:
                end = points_nr
        for pt in range(start, end):
            position = pt * interval
            if position > length:
                position = length
            points[position] = self.line_geom.interpolate(position)

        return points
