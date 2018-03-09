import sys
import math
from point import Point3
from helpers import *
from transformations import (projection_matrix,
                             angle_between_vectors)
#from shapely.geometry import (box,
#                              LinearRing)
class HoleDef(object):
    def __init__(self, loc, size):
        try:
            self.location = [loc[0], loc[1]]
        except:
            self.location = [loc, 0]
        self.size = size

    def loc2D(self):
        return self.location

    def width(self):
        # e.g. "9*4" defined the wrong way
        return parse_height(self.size)*100

    def height(self):
        return parse_width(self.size)*100 # module

    def minmax_points(self, lowz=-200, highz=400):
        dx = self.width() #parse_height(holesize)*100 # "wrong way"
        dy = self.height() #parse_width(holesize)*100 # module
        xc = self.location[0] #distance
        yc = self.location[1] #1160
        low = Point3(xc, yc, lowz)
        high = low.CopyLinear(dx, dy, highz)
        return low, high
    
class windowDef(HoleDef):
    def __init__(self, loc, size, splitters=True):
        self.splitters = splitters
        super().__init__(loc, size)
        #python2 compat: HoleDef.__init__(self, self, loc, size)

    def multiframe(self):
        return self.splitters

class WindowFramer( object ):
    def __init__( self, woods_class ):
        #self.transform = transformation_plane
        self.windows = []
        self.glassklass = 42
        self.otherklass = woods_class

    def add_window(self, transform, lowleft, highright, rotation, divisor=True):
        #rotation = direction_to_rotation(direction)
        midx = Point3.Midpoint(lowleft, highright).x
        width = int(abs(highright.x - lowleft.x))
        # put "glass" that's 10 mm thick
        thickness = 10
        stiff_n_cladding = 22 + 22
        profile = "{}*{}".format(thickness, width)
        win_low = Point3(midx, lowleft.y, thickness/2)
        win_high = Point3(midx, highright.y, thickness/2)
        self._insert_wood_to_world(transform, win_low, win_high, profile, rotation, self.glassklass)
        # pielet (22)*100
        edgeprofile = "25*100" # magic number
        level = parse_height(edgeprofile)
        offset = parse_width(edgeprofile)
        z_level = stiff_n_cladding + level/2
        # up
        upper0 = Point3(lowleft.x-offset/2, highright.y, z_level)
        upper1 = upper0.CopyLinear(width+offset, 0, 0)
        self._insert_wood_to_world(transform, upper0, upper1, edgeprofile, Rotation.FRONT, self.otherklass)
        # left
        down = 50 if divisor else 0
        lefty0 = Point3(lowleft.x, highright.y-offset/2, z_level)
        lefty1 = Point3(lowleft.x, lowleft.y-offset/2-down, z_level)
        self._insert_wood_to_world(transform, lefty0, lefty1, edgeprofile, rotation, self.otherklass)
        # right
        rigty0 = Point3(highright.x, highright.y-offset/2, z_level)
        rigty1 = Point3(highright.x, lowleft.y-offset/2-down, z_level)
        self._insert_wood_to_world(transform, rigty0, rigty1, edgeprofile, rotation, self.otherklass)
        # downer
        downy0 = Point3(lowleft.x+offset/2, lowleft.y, z_level)
        downy1 = Point3(highright.x-offset/2, lowleft.y, z_level)
        self._insert_wood_to_world(transform, downy0, downy1, edgeprofile, Rotation.FRONT, self.otherklass)
        # glass frame separators
        height = highright.y - lowleft.y
        strength = stiff_n_cladding - thickness
        div_wid = 50
        divprofile = "{}*{}".format(strength, div_wid)
        divlevel = thickness + strength/2
        # todo all around frames
        is_wide_window = True if width > height+1e-06 else False
        # just visible
        if is_wide_window:
            unit = width / 4
        else:
            unit = width / 3
        # edges vertical
        self._create_inner_upside(lowleft, highright, lowleft.x+div_wid/2, div_wid, divlevel, divprofile, rotation, transform)
        self._create_inner_upside(lowleft, highright, highright.x-div_wid/2, div_wid, divlevel, divprofile, rotation, transform)
        # edges horizontal
        self._create_inner_horizontal(lowleft, highright, highright.y-div_wid/2, div_wid, divlevel, divprofile, transform)
        self._create_inner_horizontal(lowleft, highright, lowleft.y+div_wid/2, div_wid, divlevel, divprofile, transform)
        if not divisor:
            # i.e. attic windows
            return
        # left inner
        self._create_inner_upside(lowleft, highright, lowleft.x+unit, div_wid, divlevel, divprofile, rotation, transform)
        if is_wide_window:
            # right inner
            self._create_inner_upside(lowleft, highright, highright.x-unit, div_wid, divlevel, divprofile, rotation, transform)

    def _create_inner_upside(self, lowleft, highright, at_x, div_wid, divlevel, profile, rotation, transform):
        in0 = Point3(at_x, lowleft.y+div_wid, divlevel)
        in1 = Point3(at_x, highright.y-div_wid, divlevel)
        self._insert_wood_to_world(transform, in0, in1, profile, rotation, self.otherklass)

    def _create_inner_horizontal(self, lowleft, highright, at_y, div_wid, divlevel, profile, transform):
        in0 = Point3(lowleft.x, at_y, divlevel)
        in1 = Point3(highright.x, at_y, divlevel)
        self._insert_wood_to_world(transform, in0, in1, profile, Rotation.FRONT, self.otherklass)

    def _insert_wood_to_world(self, transform, begin, end, profile, rotation, ts_class):
        in_world = transform.convertToGlobal([begin, end])
        self.windows.append(create_wood_at(in_world[0], in_world[1], profile, rotation, klass=ts_class))

    def get_framing_woods(self):
        return self.windows