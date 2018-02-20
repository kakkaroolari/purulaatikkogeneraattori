import math
import sys
from constantdict import ConstantDict
from transformations import (translation_matrix,
                             rotation_matrix,
                             projection_matrix,
                             angle_between_vectors)
from point import Point3
import numpy as np
#import bpy
from mathutils import Vector
from math import degrees

#import math3d as m3d
from shapely.geometry import (box,
                              MultiLineString,
                              Point,
                              LineString,
                              LinearRing)
from shapely.affinity import rotate
from shapely import speedups
from math import sqrt

# enable Shapely speedups, if possible
if speedups.available:
    speedups.enable()


class Rotation(ConstantDict):
    """Tekla Position.Rotation"""
    FRONT = 0
    TOP = 1
    BACK = 2
    BELOW = 3

    
def direction_to_rotation(direction, invert=False):
    (x, y) = (direction.x, direction.y)
    if invert:
        temp = x
        x = y
        y = temp
    if abs(y) > abs(x):
        if y > 0:
            return Rotation.FRONT
        return Rotation.BACK
    if x > 0:
        return Rotation.TOP
    return Rotation.BELOW


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
        self._x_axis = Point3.Normalize(x_axis)
        self._y_axis = Point3.Normalize(y_axis)

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

class Transformer(object):
    def __init__(self, transformation_plane):

        origo = np.array([0,0,0])
        xp = transformation_plane.x_axis()
        yp = transformation_plane.y_axis()
        zp = Point3.Cross(xp, yp)
        zp = Point3.Normalize(zp)

        # y' projected y on yz (normal=x)
        X1 = np.array([1,0,0]) # XAxisWorld
        X2 = np.array([0,1,0]) # YAxisWorld
        X3 = np.array([0,0,1]) # ZAxisWorld

        # These vectors are the local X,Y,Z of the rotated object
        X1Prime = xp.ToArr()
        X2Prime = yp.ToArr()
        X3Prime = zp.ToArr()

        # This matrix will transform points
        # from the world to the rotated axis
        aWorldToLocalTransform = np.matrix(
            [[np.dot(X1Prime, X1),
              np.dot(X1Prime, X2),
              np.dot(X1Prime, X3),
              0],
             [np.dot(X2Prime, X1),
              np.dot(X2Prime, X2),
              np.dot(X2Prime, X3),
              0],
             [np.dot(X3Prime, X1),
              np.dot(X3Prime, X2),
              np.dot(X3Prime, X3),
              0],
              [0,0,0,1]]
            )
        matrix2 = translation_matrix(-1*transformation_plane.origin())
        self.WorldToLocalTransform = aWorldToLocalTransform * matrix2

        # This matrix will transform points
        # from the rotated axis back to the world
        aLocalToWorldTransform  = np.matrix(
            [[np.dot(X1, X1Prime),
              np.dot(X1, X2Prime),
              np.dot(X1, X3Prime),
              0],
             [np.dot(X2, X1Prime),
              np.dot(X2, X2Prime),
              np.dot(X2, X3Prime),
              0],
             [np.dot(X3, X1Prime),
              np.dot(X3, X2Prime),
              np.dot(X3, X3Prime),
              0],
              [0,0,0,1]]
            )
        matrix4 = translation_matrix(transformation_plane.origin())
        self.LocalToWorldTransform = matrix4 * aLocalToWorldTransform

    def convertToLocal(self, points):
        return self.convert_by_matrix(points, self.WorldToLocalTransform)

    def convertToGlobal(self, points):
        return self.convert_by_matrix(points, self.LocalToWorldTransform)

    def convert_by_matrix(self, points, matrix):
        converted = []
        for point in points:
            data = [point.x, point.y, point.z, 1]
            #trace("dd: ", data)
            data = matrix.dot(data)
            A = np.squeeze(np.asarray(data))
            # TODO: f2 rounds by 1/100 mm, bad if not 90 degree stuff?
            point = Point3(f2(A[0]), f2(A[1]), f2(A[2]))
            converted.append(point)
            #trace("conv: ", point)
        return converted

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
    return Point3(f2(grid[0]), f2(grid[1]), f2(grid[2]))

def f2(num):
    return round(num,2)

def create_hatch(polygon, interval_wish, first_offset=None, last_offset=None, horizontal=False):
    """ polygon: bounding box
        interval_wish: create i.e. 125mm boards, extend interval for equal spacing (rimalaudoitus)
        first_offset: like 50 mm. from corner (nurkkalaudat mahtuu)
    """
    # todo actual polygon instead of a 2d bounding box? if needed
    min_x = min(p.x for p in polygon)
    min_y = min(p.y for p in polygon)
    max_x = max(p.x for p in polygon)
    max_y = max(p.y for p in polygon)

    ##trace("minsmax1: ", min_x, max_x, " | ", min_y, max_y)
    if first_offset is not None:
        min_x += first_offset
    if last_offset is not None:
        max_x -= last_offset
    ##trace("minsmax2: ", min_x, max_x, " | ", min_y, max_y)


    # round down to nearest fitting millimeter
    width = abs(max_x - min_x)
    spacing_count = int(width / interval_wish)
    actual_interval = width / spacing_count
    board_count = spacing_count + 1

    x_offset = min_x # todo: something wrong with zero here
    coords = []
    for i in range(board_count):
        coords.extend([((x_offset, max_y), (x_offset, min_y))])
        x_offset += actual_interval
    # turn array into Shapely object
    spoints = MultiLineString(coords)
    #trace_multiline(spoints)
    #trace("msl: ", spoints)

    wall_polygon = LinearRing([(p.x,p.y) for p in polygon])
    #cladding_hatch = wall_polygon.intersection(spoints)
    trace("interval actual: ", actual_interval, max_x, min_x)


    pps = []
    # convert back to 3d points
    for linestr in spoints.geoms:
    #for linestr in cladding_hatch.geoms:
        source = linestr.coords
        # check isect
        coll = linestr.intersection(wall_polygon)
        #trace("col: ", coll, source)
        #try:
        if 2 == len(coll):
            source = LineString(coll).coords
        #except:
        #    pass
        #trace("intersect: ", coll)
        linepts = []
        for x,y in source:
            #trace("begin: ", x, " end: ", y)
            #pps.append(Point3(*begin[0], *begin[1], 0))#, Point3(*end[0], *end[1], 0))
            linepts.append(Point3(x, y, 0))
            #trace(begin, end)
        #pps.push([Point3(x, y, 0), Point
        pps.append(linepts)
    # sort pairs by rising x coord, to get e.g. rimalaudoitus in between
    pps.sort(key=lambda tup: tup[1].x)  # sorts in place

    #trace("pps: ", pps[0][0])
    return pps

def trace_multiline(mls):
    linepps = []
    for linestr in mls.geoms:
        linepts = []
        for x,y in linestr.coords:
            linepts.append(Point3(x, y, 0))
        linepps.append(linepts)
    #linepps.sort(key=lambda tup: tup[1].x)  # sorts in place
    trace("mls: ", linepps)

# https://gis.stackexchange.com/questions/91362/looking-for-a-simple-hatching-algorithm
def hatchbox(rect, angle, spacing):
    """
    returns a Shapely geometry (MULTILINESTRING, or more rarely,
    GEOMETRYCOLLECTION) for a simple hatched rectangle.

    args:
    rect - a Shapely geometry for the outer boundary of the hatch
           Likely most useful if it really is a rectangle

    angle - angle of hatch lines, conventional anticlockwise -ve

    spacing - spacing between hatch lines

    GEOMETRYCOLLECTION case occurs when a hatch line intersects with
    the corner of the clipping rectangle, which produces a point
    along with the usual lines.
    """

    (llx, lly, urx, ury) = rect.bounds
    centre_x = (urx + llx) / 2
    centre_y = (ury + lly) / 2
    diagonal_length = sqrt((urx - llx) ** 2 + (ury - lly) ** 2)
    number_of_lines = 2 + int(diagonal_length / spacing)
    hatch_length = spacing * (number_of_lines - 1)

    # build a square (of side hatch_length) horizontal lines
    # centred on centroid of the bounding box, 'spacing' units apart
    coords = []
    for i in range(number_of_lines):
        # alternate lines l2r and r2l to keep HP-7470A plotter happy ☺
        if i % 2:
            coords.extend([((centre_x - hatch_length / 2, centre_y
                          - hatch_length / 2 + i * spacing), (centre_x
                          + hatch_length / 2, centre_y - hatch_length
                          / 2 + i * spacing))])
        else:
            coords.extend([((centre_x + hatch_length / 2, centre_y
                          - hatch_length / 2 + i * spacing), (centre_x
                          - hatch_length / 2, centre_y - hatch_length
                          / 2 + i * spacing))])
    # turn array into Shapely object
    lines = MultiLineString(coords)
    # Rotate by angle around box centre
    lines = rotate(lines, angle, origin='centroid', use_radians=False)
    # return clipped array
    return rect.intersection(lines)
