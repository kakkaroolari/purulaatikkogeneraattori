import math
import sys
from constantdict import ConstantDict
from transformations import (translation_matrix,
                             rotation_matrix,
                             angle_between_vectors)
from point import Point
import numpy as np
#import bpy
from mathutils import Vector
from math import degrees


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
    vector1 = np.array([0,0,50])
    vector2 = coordinate_system.normal()
    v0 = Vector(( vector1[0],vector1[1],vector1[2] ))
    v1 = Vector(( vector2[0],vector2[1],vector2[2] ))
    #vector2 = [50,0,0]
    # rotation
    #angle = angle_between_vectors(vector1, vector2)
    rot = v1.rotation_difference( v0 ).to_euler()
    #matrix1 = rotation_matrix(angle, -1*np.cross(vector2, vector1)).T
    #direction = np.cross(vector1, vector2)
    #direction = [0,50,0]
    #trace("normal_to: ", vector2, "Angle: ", angle, " direction: ", direction)
    trace([ degrees( a ) for a in rot ] )
    matrix1 = rotation_matrix(rot[0], [1,0,0])
    matrix11 = rotation_matrix(rot[1], [0,1,0])
    matrix111 = rotation_matrix(rot[2], [0,0,1])
    #matrix1 = rotation_matrix(angle, [1,0,0], coordinate_system.origin())
    #matrix1 = rotation_matrix(angle, [0,0,-1], coordinate_system.origin())
    #matrix1 = rotation_matrix(angle, [0,-1,0], coordinate_system.origin())
    #matrix1 = rotation_matrix(angle, [-1,0,0], coordinate_system.origin())
    #matrix1 = rotation_matrix(angle, [0,0,0], coordinate_system.origin())
    #matrix1 = rotation_matrix(angle, [0,0,0], coordinate_system.origin())
    #matrix1 = rotation_matrix(angle, [0,0,0], coordinate_system.origin())
    # translate
    matrix2 = translation_matrix(-1*coordinate_system.origin())
    #transform_matrix = projection_matrix([1000,9620,1000], coordinate_system.normal())
    trace("cp: ", coordinate_system.origin(), " n: ", coordinate_system.normal())
    converted = []
    for point in points:
        data = [point.x, point.y, point.z, 1]
        #data = [point.x, point.y, point.z]
        trace("dd: ", data)
        #temp = transform_matrix.dot(data)
        #pp = Point(temp[0], temp[1], temp[2])
        #converted.append(pp)
        data = apply_transforms(matrix2, data)
        data = apply_transforms(matrix1, data)
        data = apply_transforms(matrix11, data)
        data = apply_transforms(matrix111, data)
        point = Point(f2(data[0]), f2(data[1]), f2(data[2]))
        converted.append(point)
        trace("conv: ", point)

def apply_transforms(transform_matrix, point):
    """Get vert coords in world space"""
    #m = np.array(transform_matrix)    
    #mat = m[:3, :3].T # rotates backwards without T
    #loc = m[:3, 3]
    #return np.array(point @ mat + loc)
    return transform_matrix.dot(point)

def f2(num):
    return round(num,2)