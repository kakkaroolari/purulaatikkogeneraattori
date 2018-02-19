import sys
import math
from point import Point3
from helpers import *

class Cladding( object ):
    def __init__( self, section_name):
        self.name = section_name
        self.precut_cladding = []
        self.rimat = []

    def create_cladding(self, cladding_loop, profile, outwards):
        facades = []
        counter = 1
        A = cladding_loop[0].GetVectorTo(cladding_loop[1])
        B = cladding_loop[0].GetVectorTo(cladding_loop[-1])
        rotation = direction_to_rotation(Point3.Cross(A, B))
        #coordinate_system = CoordinateSystem(cladding_loop[0], B.Cross(A))
        coordinate_system = TransformationPlane(cladding_loop[0], A, B)
        transform = Transformer(coordinate_system)
        endwall = transform.convertToLocal(cladding_loop)
        # todo: hardcoded magic numbers, 127 mm should fit 22x125 (?)
        point_pairs = create_hatch(endwall, 127.0, 50, 50)
        #boards = []
        previous_line = []
        for pp in point_pairs:
            offsetted = []
            for endpoint in pp:
                endpoint.Translate(0,0,outwards)
                offsetted.append(endpoint)
            # add 22x50 in between
            if len(previous_line) == 2:
                rimaLow = Point3.Midpoint(offsetted[1], previous_line[1])
                rimaHigh = Point3.Midpoint(offsetted[0], previous_line[0])
                rimaLow.Translate(0,0,22)
                rimaHigh.Translate(0,0,22)
                #trace("rimalow: ", rimaLow, " high: ", rimaHigh)
                rima = transform.convertToGlobal([rimaLow, rimaHigh])
                self.rimat.append((rima[0], rima[1], "22*50", rotation,))
            previous_line = list(offsetted)
            # local to world
            pp_global = transform.convertToGlobal(offsetted)
            lowpoint = pp_global[1]#.Translate(0,0,outwards)
            highpoint = pp_global[0]
            self.precut_cladding.append((lowpoint, highpoint, profile, rotation,))
        #testback = transform.convertToGlobal(test)
        #return boards

    def get_part_data(self):
        parts = []
        for ss,tt,profile,rotation in self.precut_cladding:
            parts.append(create_wood_at(ss,tt,profile,rotation))
        for ss,tt,profile,rotation in self.rimat:
            parts.append(create_wood_at(ss,tt,profile,rotation))
        return parts