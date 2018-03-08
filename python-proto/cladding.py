import sys
import math
from point import Point3
from helpers import *

class Cladding( object ):
    def __init__( self, section_name):
        self.name = section_name
        #self.facades = []
        #self.rimat = []

    def create_cladding(self, cladding_loop, profile, outwards, holes, fittings=False):
        precut_cladding = []
        rimat = []
        counter = 1
        A = cladding_loop[0].GetVectorTo(cladding_loop[1])
        B = cladding_loop[0].GetVectorTo(cladding_loop[-1])
        rotation = direction_to_rotation(Point3.Cross(A, B))
        #coordinate_system = CoordinateSystem(cladding_loop[0], B.Cross(A))
        coordinate_system = TransformationPlane(cladding_loop[0], A, B)
        transform = Transformer(coordinate_system)
        endwall = transform.convertToLocal(cladding_loop)
        # todo: hardcoded magic numbers, 127 mm should fit 22x125 (?)
        point_pairs = create_hatch(endwall, 127.0, 87.50, 87.50, holes=holes)
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
                rimat.append((rima[0], rima[1], "22*50", rotation,))
            previous_line = list(offsetted)
            # local to world
            pp_global = transform.convertToGlobal(offsetted)
            lowpoint = pp_global[1]#.Translate(0,0,outwards)
            highpoint = pp_global[0]
            precut_cladding.append((lowpoint, highpoint, profile, rotation,))
        fits = None
        if fittings:
            #origo = endwall[-1].Clone()
            #x_axis = origo.GetVectorTo(endwall[-2])
            #y_axis = origo.CopyLinear(0,0,1000)
            #normal = Point3.Cross(
            leftpts = [endwall[-1], endwall[-2], endwall[-1].CopyLinear(0,0,1000)]
            left_to_world = transform.convertToGlobal(leftpts)
            left = to_planedef(left_to_world)
            #origo = endwall[-3].Clone()
            #x_axis = endwall[-2].GetVectorTo(origo)
            #y_axis = origo.CopyLinear(0,0,1000)
            rightpts = [endwall[-2], endwall[-3], endwall[-2].CopyLinear(0,0,1000)]
            right_to_world = transform.convertToGlobal(rightpts)
            right = to_planedef(right_to_world)
            fits = [left, right]
        #self.facades.append((precut_cladding, rimat, fits,))
        return self._get_part_data(precut_cladding, rimat), fits
        #testback = transform.convertToGlobal(test)
        #return boards

    def _get_part_data(self, precut_cladding, rimat):
        parts = []
        for ss,tt,profile,rotation in precut_cladding:
            parts.append(create_wood_at(ss,tt,profile,rotation))
        for ss,tt,profile,rotation in rimat:
            parts.append(create_wood_at(ss,tt,profile,rotation))
        return parts
