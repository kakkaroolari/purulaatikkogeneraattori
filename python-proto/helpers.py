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
        self._x_axis = x_axis
        self._y_axis = y_axis

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
    # y' projected y on yz (normal=x)
    xm = projection_matrix(origo, [1,0,0])
    ym = projection_matrix(origo, [0,1,0])
    zm = projection_matrix(origo, [0,0,1])

    xp_ = [xp.x, xp.y, xp.z, 1]
    yp_ = [yp.x, yp.y, yp.z, 1]
    zp_ = [zp.x, zp.y, zp.z, 1]
    # apply projection matrices
    xpp = xm.dot(xp_)#.ToArr())
    ypp = ym.dot(yp_)#.ToArr())
    zpp = zm.dot(zp_)#.ToArr())

    trace("points      x,y,z: ", (xp), (yp), (zp))
    trace("projections x,y,z: ", ff2(xpp), ff2(ypp), ff2(zpp))
    a_x = get_angle([0,1,0], ypp[:3], 'y')
    #trace("angle z z'", ff2([0,0,1]), ff2(ypp[:3]))
    a_y = get_angle([0,0,1], zpp[:3], 'z')
    a_z = get_angle([1,0,0], xpp[:3], 'x')
    trace("Angles x,y,z: ", a_x, a_y, a_z)

    # create a rotation matrix
    mat_rx = rotation_matrix(a_x, [1,0,0])
    mat_ry = rotation_matrix(a_y, [0,1,0])
    mat_rz = rotation_matrix(a_z, [0,0,1])
    mat_rot = mat_rx * mat_ry * mat_rz
    matrix2 = translation_matrix(-1*transformation_plane.origin())
    re_base = mat_rot * matrix2

    converted = []
    for point in points:
        data = [point.x, point.y, point.z, 1]
        #data = [point.x, point.y, point.z]
        trace("dd: ", data)
        #temp = transform_matrix.dot(data)
        #pp = Point(temp[0], temp[1], temp[2])
        #converted.append(pp)
        data = apply_transforms(matrix2, data)
        data = apply_transforms(mat_rot, data)
        point = Point(f2(data[0]), f2(data[1]), f2(data[2]))
        converted.append(point)
        trace("conv: ", point)

def get_angle(v1, v2, pt):
    ng = angle_between_vectors(v1, v2, directed=True)
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