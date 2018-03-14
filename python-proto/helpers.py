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
#from mathutils import Vector
from math import degrees

#import math3d as m3d
from shapely.geometry import (box,
                              MultiLineString,
                              Point,
                              LineString,
                              LinearRing,
                              MultiPoint,
                              Polygon)
from shapely.affinity import rotate
from shapely import speedups
from math import sqrt
import re

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


def create_vertical_stdplane(line):
    # create 2d coord sys
    Z = line[0].CopyLinear(0,0,2000) # wall height irrelevant
    A = line[0].GetVectorTo(line[1])
    B = line[0].GetVectorTo(Z)
    rotation = direction_to_rotation(Point3.Cross(A, B))
    coordinate_system = TransformationPlane(line[0], A, B)
    transform = Transformer(coordinate_system)
    return transform, rotation


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

def parse_profile(profile):
    p = re.compile('(\d*\.\d+|\d+)\*(\d*\.\d+|\d+)')
    m = p.match(profile)
    return m

def parse_height(profile):
    m = parse_profile(profile)
    height = m.group(1)
    #trace("profile height: " + height)
    return float(height)

def parse_width(profile):
    m = parse_profile(profile)
    width = m.group(2)
    #trace("profile width: " + width)
    return float(width)

def create_wood_at(point, point2, profile, rotation=None, klass=None):
    low_point = point.Clone()
    high_point = point2.Clone()
    return get_part_data(profile, rotation, [low_point, high_point], "Timber_Undefined", ts_class=klass)

def get_part_data(profile, rotation, points, material, ts_class=None):
    return {
        "profile": profile,
        "rotation": rotation,
        "points": points,
        "material": material,
        "klass": ts_class
    }

def remove_none_elements_from_list(list_in):
    if not list_in:
        return None
    shortened = [e for e in list_in if e is not None]
    if 0 == len(shortened):
        return None
    return shortened

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
        return Transformer.convert_by_matrix(points, self.WorldToLocalTransform)

    def convertToGlobal(self, points):
        return Transformer.convert_by_matrix(points, self.LocalToWorldTransform)

    def convert_by_matrix(points, matrix):
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

def create_cut_aabb(point_pair):
    xs = [p.x for p in point_pair]
    ys = [p.y for p in point_pair]
    zs = [p.z for p in point_pair]
    return {
        "min_point": Point3(min(xs), min(ys), min(zs)),
        "max_point": Point3(max(xs), max(ys), max(zs))
    }

def create_cut_plane(point1, point2, normal):
    
    aa = point1.GetVectorTo(point2)
    bb = Point3.Cross(aa, normal)
    point3 = point1.CopyLinear(bb)
    #trace("xyzabc: ", point1, point2, point3)
    return to_planedef(point1, point2, point3)

def to_planedef(point1, point2=None, point3=None):
    try:
       p1, p2, p3 = point1[0], point1[1], point1[2]
       trace("p1p2n: ", p1, p2, p3)
    except TypeError:
       p1, p2, p3 = point1, point2, point3
       pass
    return {
        "point1": p1.Clone(),
        "point2": p2.Clone(),
        "point3": p3.Clone(),
    }

def get_differences(polygon):
    min_x, min_y, max_x, max_y = bounding_box(polygon)
    page = box(min_x, min_y, max_x, max_y)
    #trace("page: ", page)
    ring = LinearRing([(p.x,p.y) for p in polygon])
    #trace("ring: ", ring)
    wall_polygon = Polygon(ring.coords)
    #trace("polugon: ", wall_polygon)
    diffs = page.difference(wall_polygon)
    #trace("diffs: ", diffs)
    aabbs = []
    if isinstance(diffs, Polygon):
        diffs.geoms = [diffs]
    for polygons in diffs.geoms:
        bound_box = polygons.bounds
        minx, miny, maxx, maxy = bound_box
        aabbs.append([Point3(minx, miny, -200), Point3(maxx, maxy, 200)])
    return aabbs

def bounding_box(polygon):
    min_x = min(p.x for p in polygon)
    min_y = min(p.y for p in polygon)
    max_x = max(p.x for p in polygon)
    max_y = max(p.y for p in polygon)
    return min_x, min_y, max_x, max_y

def create_hatch(polygon, interval_wish, first_offset=None, last_offset=None, horizontal=False, exact=False, holes=None):
    """ polygon: bounding box
        interval_wish: create i.e. 125mm boards, extend interval for equal spacing (rimalaudoitus)
        first_offset: like 50 mm. from corner (nurkkalaudat mahtuu)
    """
    # todo actual polygon instead of a 2d bounding box? if needed
    trace("polpol: ", polygon)
    min_x, min_y, max_x, max_y = bounding_box(polygon)

    coords = []
    actual_interval = interval_wish

    # horizontal battens is completely different
    if horizontal:
        if first_offset is not None:
            min_y += first_offset
        height = abs(max_y - min_y)
        spacing_count = int(height / interval_wish)
        board_count = spacing_count + 1

        y_offset = min_y # todo: something wrong with zero here
        for i in range(board_count):
            coords.extend([((min_x, y_offset ), (max_x, y_offset ))])
            y_offset += interval_wish
        # last ninja
        last_y = max_y
        coords.extend([((min_x, last_y), (max_x, last_y))])
        #trace("crds: ", coords)
    else:
        # vertical boards, e.g. cladding
        if first_offset is not None:
            min_x += first_offset
        if last_offset is not None:
            max_x -= last_offset

        # round down to nearest fitting millimeter
        width = abs(max_x - min_x)
        spacing_count = int(width / interval_wish)
        actual_interval = width / spacing_count
        board_count = spacing_count + 1
        if exact:
            actual_interval = interval_wish

        x_offset = min_x # todo: something wrong with zero here
        for i in range(board_count):
            coords.extend([((x_offset, max_y), (x_offset, min_y))])
            x_offset += actual_interval

    # turn array into Shapely object
    spoints = MultiLineString(coords)
    #trace_multiline(spoints)
    #trace("msl: ", spoints)

    wall_polygon = LinearRing([(p.x,p.y) for p in polygon])
    #cladding_hatch = wall_polygon.intersection(spoints)
    trace("interval actual: ", actual_interval, max_x, min_x, max_y, min_y)

    windows = []
    if holes is not None:
        #alt_poly = LinearRing([(p.x,p.y) for p in polygon])
        for windef in holes:
            x0, y0, dx, dy = windef.minmax_coords()
            rect = box(x0, y0, x0+dx, y0+dy)
            #alt_poly = alt_poly.difference(rect)
            windows.append(rect)
        #trace("alt_poly: ", alt_poly)
            #wall_polygon = wall_polygon.difference(rect)
    #spoints = wall_polygon.intersection(spoints)
        #alt_poly = Polygon(wall_polygon, [LinearRing(r) for r in windows])
        #wall_polygon = Polygon([(p.x,p.y) for p in polygon], [r.exterior.coords for r in windows])
        #trace("alt_poly: ", wall_polygon)

    pps = []
    # convert back to 3d points
    for linestr in spoints.geoms:
    #for linestr in cladding_hatch.geoms:
        source = linestr.coords
        # check isect
        coll = linestr.intersection(wall_polygon)
        #trace("col: ", coll, source)
        #try:
        if isinstance(coll, Point):
            coll = [source]
        if isinstance(coll, LineString):# and 2 == len(coll):
            coll = [coll.coords]
        if isinstance(coll, MultiLineString) or isinstance(coll, MultiPoint):# and 2 == len(coll):
            #trace("multi")
            coll = [a.coords for a in coll.geoms]
        #except:
        #    pass
        #trace("intersect: ", coll)
        #coll.sort(key=lambda tup: tup[1])  # i=y, sorts in place
        linepts = []
        for coord in coll:
            for (x,y) in coord:
                #trace("begin: ", x, " end: ", y)
                #pps.append(Point3(*begin[0], *begin[1], 0))#, Point3(*end[0], *end[1], 0))
                linepts.append(Point3(x, y, 0))
                #trace(begin, end)
                #pps.push([Point3(x, y, 0), Point
                #if 2 == len(linepts):
                #    pps.append([x.Clone() for x in linepts])
                #    trace("linepts: ", linepts)
                #    linepts = []
        linepts.sort(key=lambda p: p.y)  # sort y
        pairs = []
        for point in linepts:
            pairs.append(point)
            if 2 == len(pairs):
                pps.append([x.Clone() for x in pairs])
                #trace("pairs: ", pairs)
                pairs = []

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
def hatchbox(rect, angle, spacing, hole=None):
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
    if holes is not None:
        x0, y0, dx, dy = windef.minmax_coords()
        rect = box(x0, y0, x0+dx, y0+dy)
        lines = lines.difference(rect)
    return rect.intersection(lines)

def get_bounding_lines(bounding_box, transformer=None):
    # z dir only
    ordered = [bounding_box['min_point'], bounding_box['max_point']]
    xs = [p.x for p in ordered]
    ys = [p.y for p in ordered]
    zs = [p.z for p in ordered]
    lines = []
    for i in range(2):
        for j in range(2):
            xx, yy = xs[i], ys[j]
            lines.append([Point3(xx, yy, zs[0]), Point3(xx, yy, zs[1])])
    print("4lines: ", lines)
    if transformer is not None:
        transformed_lines = []
        for pp in lines:
            lines_to_local = transformer.convertToLocal(pp)
            transformed_lines.append(lines_to_local)
        return transformed_lines
    return lines

# intersection function
def isect_line_plane_v3(p0, p1, p_co=[0,0,0], p_no=[0,0,1], epsilon=1e-6):
    """
    p0, p1: define the line
    p_co, p_no: define the plane:
        p_co is a point on the plane (plane coordinate).
        p_no is a normal vector defining the plane direction;
             (does not need to be normalized).

    return a Vector or None (when the intersection can't be found).
    """

    u = np.subtract(p1, p0) #sub_v3v3(p1, p0)
    dot = np.dot(p_no, u) #dot_v3v3(p_no, u)

    if abs(dot) > epsilon:
        # the factor of the point between p0 -> p1 (0 - 1)
        # if 'fac' is between (0 - 1) the point intersects with the segment.
        # otherwise:
        #  < 0.0: behind p0.
        #  > 1.0: infront of p1.
        w = np.subtract(p0, p_co) #sub_v3v3(p0, p_co)
        fac = -np.dot(p_no, w) / dot #dot_v3v3(p_no, w) / dot
        u = np.multiply(u, fac) #mul_v3_fl(u, fac)
        return np.add(p0, u) #add_v3v3(p0, u)
    else:
        # The segment is parallel to plane
        return None