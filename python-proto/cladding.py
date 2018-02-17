import sys
import math
from point import Point3
from helpers import *

class Cladding( object ):
    def __init__( self, section_name):
        self.name = section_name
        self.precut_cladding = []

    def create_cladding(self, cladding_loop, profile, outwards):
        facades = []
        counter = 1
        A = cladding_loop[0].GetVectorTo(cladding_loop[1])
        B = cladding_loop[0].GetVectorTo(cladding_loop[-1])
        #coordinate_system = CoordinateSystem(cladding_loop[0], B.Cross(A))
        coordinate_system = TransformationPlane(cladding_loop[0], A, B)
        transform = Transformer(coordinate_system)
        endwall = transform.convertToLocal(cladding_loop)
        # todo: hardcoded magic numbers, 127 mm should fit 22x125 (?)
        point_pairs = create_hatch(endwall, 127.0, 50, 50)
        #boards = []
        for pp in point_pairs:
            offsetted = []
            for endpoint in pp:
                endpoint.Translate(0,0,outwards)
                offsetted.append(endpoint)
            pp_global = transform.convertToGlobal(offsetted)
            lowpoint = pp_global[1]#.Translate(0,0,outwards)
            highpoint = pp_global[0]
            self.precut_cladding.append((lowpoint, highpoint, profile, Rotation.TOP,))
        #testback = transform.convertToGlobal(test)
        #return boards

    def get_part_data(self):
        parts = []
        for ss,tt,profile,rotation in self.precut_cladding:
            parts.append(create_wood_at(ss,tt,profile,rotation))
        return parts