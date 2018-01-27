import sys
import math
from point import Point
from helpers import *
#from geometry import create_wood_at

# no depss... end...
class Stiffener( object ):
    def __init__( self, section_name, mass_center):
        self.name = section_name
        self.masscenter = mass_center
        self.precut_stiffeners = []
        self.planes = []

    def get_part_data(self):
        parts = []
        for ss,tt in self.precut_stiffeners:
            parts.append(create_wood_at(ss,tt, "22*100", Rotation.FRONT))
        return parts
        #return self.precut_stiffeners

    def get_planes(self):
        return self.planes

    def stiffener_one_plane(self, startpoint, endpoint, height, roofangle):
        """
        Create 45 degree stiffeners for two sections of a wall line.
        TODO: refactor to draw boards symmetrically for beautify reasons.
        TODO: 22 mm offset to porch (woods only!)

        face vectors:

                (C)
               /   \
             /   |   \
           /           \
         /       |       \
       (D)               (F)
        |        |        |
        |                 |
        |        |        |
       (A)------(B)------(E)
        """
        #roofangle = roof_angle
        #if not is_short_side(startpoint, endpoint):
        #    roofangle = None
        wall_line = startpoint.GetVectorTo(endpoint)
        length = startpoint.distFrom(endpoint)
        boxmax = max(height*2, length) * math.sqrt(2)
        A = startpoint.Clone()
        B = Point.Midpoint(startpoint, endpoint)
        extremely_short_wall = length < 3000
        if extremely_short_wall:
            B = endpoint.Clone() # TODO: fix this, won't work with upper roof polygon stuff
            roofangle = None
        C = B.CopyLinear(0,0,get_ceiling(startpoint, B, height, length, roofangle))
        D = A.CopyLinear(0,0,height)
        trace("ABCD: ", A, B, C, D)
        # fit vectors (to export json)
        self.planes.append((A.Clone(), A.GetVectorTo(B)),)
        self.planes.append((A.Clone(), A.GetVectorTo(D)),)
        if extremely_short_wall:
            self.planes.append((B.Clone(), B.GetVectorTo(A)),)
        else:
            self.planes.append((endpoint.Clone(), endpoint.GetVectorTo(B)),)
        # helper vinolaudat
        gridfull = math.sqrt(2)*100.0
        gridhalf = gridfull/2
        # directions 
        increment_h = wall_line
        stiffener_lines = []
        towards_xy = Point.Normalize(wall_line, gridfull) # todo begin at full
        towards_up = Point(0,0,gridfull) # z-vector
        aa = startpoint.Clone()
        bb = startpoint.Clone()
        toN = Point.Normalize(towards_up.Add(towards_xy.Reversed()), boxmax)
        toM = Point.Normalize(towards_xy.Add(towards_up.Reversed()), boxmax)
        aa.Translate(toN)
        bb.Translate(toM)
        grid_direction = Point.Normalize(towards_up.Add(towards_xy), 100)
        counter = int(boxmax/gridfull)
        trace("stiff count: ", counter)
        for rep in range(counter):
            aa.Translate(grid_direction)
            bb.Translate(grid_direction)
            stiffener_lines.append((aa.Clone(),bb.Clone(),)) # todo remove and precut
        # now we should intersect the shit
        #self.precut_stiffeners = []
        ceiling = get_ceiling(B, A, height, length, roofangle)
        roof_normal_vector = get_roof_vector(A,B,C,D)
        last_ninja = None
        # precut'em
        for N,M in stiffener_lines:
            # 1. cut AD -> nm
            beg = Point.isect_line_plane_v3_wrap(N,M,A,wall_line)
            # 2. if no, DC -> nm
            if beg.distFrom(A) > height:
                beg = Point.isect_line_plane_v3_wrap(N,M,D,roof_normal_vector)
            # 3. cut AB -> nm
            end = Point.isect_line_plane_v3_wrap(N,M,A,towards_up)
            # if no, BC -> nm
            cutlength = length if extremely_short_wall else length/2
            if end.distFrom(A) > cutlength:
                end = Point.isect_line_plane_v3_wrap(N,M,B,towards_xy)
            # skip all going over
            if beg.z - B.z > ceiling + 10.0 or end.z - B.z > ceiling + 10.0:
                continue
            last_ninja = end.Clone()
            self.precut_stiffeners.append((beg, end),)
        if extremely_short_wall:
            return # precut_stiffeners
        if last_ninja is None:
            #return None
            self.precut_stiffeners = None
        #return precut_stiffeners
        # continue to other side, transpose 90 deg
        stiffener_dir = Point.Normalize(grid_direction, boxmax)
        trace("boxmax: ", boxmax, stiffener_dir)
        #grid_direction = get_roof_vector(A,B,C,D).Normalize(-50)
        last_ninja.Translate(0,0,-math.sqrt(50*50+50*50)) # ca 70 mm down
        #last_ninja.Traslate(grid_direction) # ca 70 mm down
        stiffener_lines = []
        aa = last_ninja.Clone()
        for i in range(counter):
            beg = aa.Clone()
            end = aa.CopyLinear(stiffener_dir)
            stiffener_lines.append((beg.Clone(), end.Clone()),)
            aa.Translate(0,0, -gridfull)
        # todo precut othor said
        E = endpoint.Clone()
        F = endpoint.CopyLinear(0,0,height)
        #towards_down = Point(0,0,-100)
        for N,M in stiffener_lines:
            # 1. cut BE -> nm
            beg = N.Clone()
            if beg.z < B.z:
                beg = Point.isect_line_plane_v3_wrap(N,M,B,towards_up)
            # 2. cut EF -> nm
            end = M.Clone()
            end = Point.isect_line_plane_v3_wrap(N,M,E,towards_xy)
            # 3. cut FC -> nm (if there's a roof angle)
            if end.distFrom(E) > height: #and roofangle:
                end = Point.isect_line_plane_v3_wrap(N,M,F,get_roof_vector(E,B,C,F))
                # skip all going under (10 mm tolerance)
            if beg.z < B.z - 10.0 or end.z < B.z - 10.0:
                continue
            if beg.distFrom(A) > length + 10.0 and end.distFrom(A) > length + 10.0:
                continue
            self.precut_stiffeners.append((beg.Clone(),end),)
        #return precut_stiffeners

def get_roof_vector(A,B,C,D):
    ad = A.GetVectorTo(D)
    ab = A.GetVectorTo(B)
    dc = D.GetVectorTo(C)
    helper = Point.Cross(ad, ab)
    return Point.Cross(helper, dc)
