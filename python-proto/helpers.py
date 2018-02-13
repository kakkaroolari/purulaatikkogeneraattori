import math
import sys
from constantdict import ConstantDict
from transformations import (translation_matrix,
                             rotation_matrix,
                             projection_matrix,
                             angle_between_vectors)
from point import Point
import numpy as np
#import bpy
from mathutils import Vector
from math import degrees

import math3d as m3d


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

class TransformationPlane(object):
    def __init__( self, origin, x_axis, y_axis ):
        self._origin = origin
        self._x_axis = Point.Normalize(x_axis)
        self._y_axis = Point.Normalize(y_axis)

    def origin(self):
        return self._origin.ToArr()

    def x_axis(self):
        return self._x_axis

    def y_axis(self):
        return self._y_axis

def rotated_vector_mat(axisFrom, axisTo):
    v0 = Vector(( axisFrom[0],axisFrom[1],axisFrom[2] ))
    v1 = Vector(( axisTo[0],axisTo[1],axisTo[2] ))
    # rotation
    rot = v1.rotation_difference( v0 ).to_euler()
    trace([ degrees( a ) for a in rot ] )
    matrix1 = rotation_matrix(rot[0], [1,0,0])
    matrix11 = rotation_matrix(rot[1], [0,1,0])
    matrix111 = rotation_matrix(rot[2], [0,0,1])
    # combine transformations
    mat_out = matrix1 * matrix11 * matrix111
    print(mat_out)
    return mat_out

def convert_points(points, transformation_plane):
    origo = np.array([0,0,0])
    xp = transformation_plane.x_axis()
    yp = transformation_plane.y_axis()
    zp = Point.Cross(xp, yp)
    zp = Point.Normalize(zp)

    # y' projected y on yz (normal=x)
    X1 = np.array([1,0,0]) # XAxisWorld
    X2 = np.array([0,1,0]) # YAxisWorld
    X3 = np.array([0,0,1]) # ZAxisWorld

    # These vectors are the local X,Y,Z of the rotated object
    X1Prime = xp.ToArr()
    X2Prime = yp.ToArr()
    X3Prime = zp.ToArr()

    # This matrix will transform points
    # from the world back to the rotated axis
    WorldToLocalTransform = np.matrix(
        [[np.dot(X1Prime, X1),
          np.dot(X1Prime, X2),
          np.dot(X1Prime, X3)],
         [np.dot(X2Prime, X1),
          np.dot(X2Prime, X2),
          np.dot(X2Prime, X3)],
         [np.dot(X3Prime, X1),
          np.dot(X3Prime, X2),
          np.dot(X3Prime, X3)]]
        )
    matrix2 = translation_matrix(-1*transformation_plane.origin())

    converted = []
    for point in points:
        data = [point.x, point.y, point.z, 1]
        #data = [point.x, point.y, point.z]
        trace("dd: ", data)
        temp = matrix2.dot(data)
        data = WorldToLocalTransform.dot(temp[:3])
        trace("dot: ", data)
        A = np.squeeze(np.asarray(data))
        point = Point(f2(A[0]), f2(A[1]), f2(A[2]))
        converted.append(point)
        trace("conv: ", point)

def get_angle(v1, v2, pt, index=None):
    ng = angle_between_vectors(v1, v2, directed=True)
    trace("angle " + pt + " " + pt + "' "+ str(ff2(v1)) + " -> " + str(ff2(v2)))
    # devel 
    v11 = Vector(( v1[0],v1[1],v1[2] ))
    v22 = Vector(( v2[0],v2[1],v2[2] ))
    rot = v22.rotation_difference( v11 ).to_euler()
    if index is not None:
        trace("TEST: " + str(rot))
        return rot[index]

    trace("angle " + pt + " " + pt + "' "+ str(ff2(v1)) + " -> " + str(ff2(v2))      +" is:" + str(ng))
    return ng


def apply_transforms(transform_matrix, point):
    """Get vert coords in world space"""
    #m = np.array(transform_matrix)    
    #mat = m[:3, :3].T # rotates backwards without T
    #loc = m[:3, 3]
    #return np.array(point @ mat + loc)
    return transform_matrix.dot(point)

def ff2(grid):
    return Point(f2(grid[0]), f2(grid[1]), f2(grid[2]))

def f2(num):
    return round(num,2)