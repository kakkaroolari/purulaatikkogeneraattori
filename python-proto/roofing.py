import sys
import math
from point import Point3
from helpers import *
from transformations import (projection_matrix,
                             angle_between_vectors)

class Roofing( object ):
    def __init__( self, section_name):
        self.name = section_name
        self.roof_rafter_coords = []

    def do_one_roof_face(self, face_polygon, high_point_actual):
        """ This is a geometry util func, Roofing will do the stuff.
            order is important. This comment is utter bollocks.
            todo: lape name
        """
        # first lape (xy plane)
        direction = face_polygon[0].GetVectorTo(face_polygon[1])
        direction = direction.Normalize(600)
        # now we should project this in actual roof plane (xyz)
        origo = face_polygon[1].Clone()
        Y = origo.GetVectorTo(high_point_actual)
        X = origo.GetVectorTo(face_polygon[2].Clone())
        N = Point3.Cross(X, Y).Normalize()
        #trace("norml: ", N)
        for point in face_polygon[1:-1]:
            # move raystas 600 mm outwards
            # TODO: This shit makes holppa==125.00 mm brake
            point.Translate(direction)
        # tilt roof plane from xy plane to actual angle
        mat = projection_matrix(origo.ToArr(), N.ToArr(), direction=[0,0,1])
        geomPlane = TransformationPlane(origo, X, Y)
        transistor = Transformer(geomPlane) # geom plane is not used in convert_by_matrix
        points_in_correct_plane = transistor.convert_by_matrix(face_polygon, mat)
        #trace("roof is at: ", points_in_correct_plane)
        # now start creating hatch
        local_roof_poly = transistor.convertToLocal(points_in_correct_plane)
        #trace("local pts: ", local_points)
        holppa = 125.0
        one_face_point_pairs = create_hatch(local_roof_poly, 900.0, holppa, holppa)
        # convert back to global csys
        for pp in one_face_point_pairs:
            pp2 = transistor.convertToGlobal(pp)
            self.roof_rafter_coords.append((pp2[0], pp2[1], "50*125", Rotation.FRONT,))
        # rimat
        for rr in one_face_point_pairs:
            for point in rr:
                # rimat above the studs
                point.Translate(0,0,62.5 + 11)
            rr2 = transistor.convertToGlobal(rr)
            self.roof_rafter_coords.append((rr2[0], rr2[1], "22*50", Rotation.TOP,))
        # then battens
        ind = 0
        trace("local roof battens1: ", local_roof_poly)
        for point in local_roof_poly[:-1]:
            toNext = point.GetVectorTo(local_roof_poly[ind+1])
            toNext.z = 0 # level out to xy-plane
            # if vector is roof lape suuntainen, extrude
            expand = None
            #trace("tonext: ", toNext)
            if angle_between_vectors(toNext.ToArr(), [0,-1,0], directed=True) < math.radians(1):
                #trace ("left")
                expand = Point3(-600, 0, 0)
            elif angle_between_vectors(toNext.ToArr(), [0,1,0], directed=True) < math.radians(1):
                #trace ("right")
                expand = Point3(600, 0, 0)
            #else:
            #    trace("none")
            if expand is not None:
                #trace("ind: ", ind)
                local_roof_poly[ind].Translate(expand)
                local_roof_poly[ind+1].Translate(expand)
            ind += 1
        trace("local roof battens2: ", local_roof_poly)
        one_face_batten_pairs = create_hatch(local_roof_poly, 350.0, first_offset=50, horizontal=True)
        # add battens
        for bb in one_face_batten_pairs:
            for point in bb:
                # rimat above the studs
                point.Translate(0,0,62.5 + 22/2 + 32/2)
            bb2 = transistor.convertToGlobal(bb)
            trace(bb2[0], bb2[1], "32*100")
            self.roof_rafter_coords.append((bb2[0], bb2[1], "32*100", Rotation.TOP,))

    def get_part_data(self):
        roofparts = []
        #for pp in self.roof_stud_coords:
        for lowpoint, highpoint, profile, rotation in self.roof_rafter_coords:
            roofparts.append(create_wood_at(lowpoint, highpoint, profile, rotation))
        return roofparts
