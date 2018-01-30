import math
import sys
from constantdict import ConstantDict
from transformations import reflection_matrix
from point import Point
import numpy as np


class Rotation(ConstantDict):
    """Tekla Position.Rotation"""
    FRONT = 0
    TOP = 1
    BACK = 2
    BELOW = 3

def get_ceiling(current, start, height, fullwidth, roofangle):
    if not roofangle:
        return height
    dist_to_start = current.distFrom(start)
    coeff = math.tan(math.radians(roofangle))
    inner_width = fullwidth - 100 # todo profile
    if dist_to_start < inner_width/2:
        elevation = dist_to_start * coeff
    else:
        elevation = (inner_width - dist_to_start) * coeff
    return height + elevation

def trace(*args, **kwargs):
    print(*args, file = sys.stderr, **kwargs)

def create_wood_at(point, point2, profile, rotation=None):
    low_point = point.Clone()
    high_point = point2.Clone()
    return get_part_data(profile, rotation, [low_point, high_point], "Timber_Undefined")

def get_part_data(profile, rotation, points, material, ts_class=None):
    return {
        "profile": profile,
        "rotation": rotation,
        "points": points,
        "material": material,
        "klass": ts_class
    }

class CoordinateSystem(object):
    def __init__( self, origin, normal ):
        self._origin = origin
        self._normal = normal

    def origin(self):
        return self._origin.ToArr()

    def normal(self):
        return self._normal.ToArr()

def convert_points(points, coordinate_system):
    transform_matrix = reflection_matrix(coordinate_system.origin(), coordinate_system.normal())
    trace("cp: ", coordinate_system.origin(), " n: ", coordinate_system.normal())
    converted = []
    for point in points:
        data = [point.x, point.y, point.z, 1]
        trace("dd: ", data)
        temp = np.dot(transform_matrix, data)
        pp = Point(temp[0], temp[1], temp[2])
        converted.append(pp)
        trace("conv: ", pp)