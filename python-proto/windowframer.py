import sys
import math
from point import Point3
from helpers import *
from transformations import (projection_matrix,
                             angle_between_vectors)
#from shapely.geometry import (box,
#                              LinearRing)

class WindowFramer( object ):
    def __init__( self, woods_class ):
        #self.transform = transformation_plane
        self.windows = []
        self.glassklass = 42
        self.otherklass = woods_class

    def add_window(self, transform, lowleft, highright, rotation):
        #rotation = direction_to_rotation(direction)
        midx = Point3.Midpoint(lowleft, highright).x
        width = int(abs(highright.x - lowleft.x))
        # put "glass" that's 22mm thick
        thickness = 22
        profile = "{}*{}".format(thickness, width)
        win_low = Point3(midx, lowleft.y, thickness/2)
        win_high = Point3(midx, highright.y, thickness/2)
        self._insert_wood_to_world(transform, win_low, win_high, profile, rotation, self.glassklass)
        # pielet (22)*100
        edgeprofile = "25*100" # magic number
        level = parse_height(edgeprofile)
        offset = parse_width(edgeprofile)
        z_level = 22 + 22 + level/2
        # up
        upper0 = Point3(lowleft.x-offset/2, highright.y, z_level)
        upper1 = upper0.CopyLinear(width+offset, 0, 0)
        self._insert_wood_to_world(transform, upper0, upper1, edgeprofile, Rotation.FRONT, self.otherklass)
        # left
        down=50
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


    def _insert_wood_to_world(self, transform, begin, end, profile, rotation, ts_class):
        in_world = transform.convertToGlobal([begin, end])
        self.windows.append(create_wood_at(in_world[0], in_world[1], profile, rotation, klass=ts_class))

    def get_framing_woods(self):
        return self.windows