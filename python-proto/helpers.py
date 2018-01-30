import math
import sys
from constantdict import ConstantDict
from transformations import (translation_matrix,
                             rotation_matrix,
                             angle_between_vectors)
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
    vector1 = [0,0,50]
    vector2 = coordinate_system.normal()
    # rotation
    angle = angle_between_vectors(vector1, vector2, True)
    #matrix1 = rotation_matrix(angle, -1*np.cross(vector2, vector1)).T
    matrix1 = rotation_matrix(angle, np.cross(vector1, vector2)).T
    # translate
    matrix2 = translation_matrix(-1*coordinate_system.origin())
    #transform_matrix = projection_matrix([1000,9620,1000], coordinate_system.normal())
    trace("cp: ", coordinate_system.origin(), " n: ", coordinate_system.normal())
    converted = []
    for point in points:
        #data = [point.x, point.y, point.z, 1]
        data = [point.x, point.y, point.z]
        trace("dd: ", data)
        #temp = transform_matrix.dot(data)
        #pp = Point(temp[0], temp[1], temp[2])
        #converted.append(pp)
        data = apply_transforms(matrix1, data)
        data = apply_transforms(matrix2, data)
        converted.append(data)
        trace("conv: ", data)

def apply_transforms(transform_matrix, point):
    """Get vert coords in world space"""
    m = np.array(transform_matrix)    
    mat = m[:3, :3].T # rotates backwards without T
    loc = m[:3, 3]
    return point @ mat + loc
