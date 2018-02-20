import sys
import math
from point import Point3
from helpers import *
from transformations import projection_matrix

class Roofing( object ):
    def __init__( self, section_name):
        self.name = section_name
        self.roof_stud_coords = []

    def do_one_roof_face(self, face_polygon, high_point_actual):
        """ This is a geometry util func, Roofing will do the stuff.
            order is important. This comment is utter bollocks.
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
        local_points = transistor.convertToLocal(points_in_correct_plane)
        #trace("local pts: ", local_points)
        holppa = 125.0
        one_face_point_pairs = create_hatch(local_points, 900.0, holppa, holppa)
        # convert back to global csys
        for pp in one_face_point_pairs:
            #trace(pp)
            pp2 = transistor.convertToGlobal(pp)
            #trace(pp2)
            #for lowpoint, highpoint in pp2:
            # roof truss 5x2's
            self.roof_stud_coords.append((pp2[0], pp2[1], "50*125", Rotation.FRONT,))
        # rimat
        for rr in one_face_point_pairs:
            for point in rr:
                # rimat above the studs
                point.Translate(0,0,62.5 + 11)
            rr2 = transistor.convertToGlobal(rr)
            #for lowpoint, highpoint in rr2:
            self.roof_stud_coords.append((rr2[0], rr2[1], "22*50", Rotation.TOP,))


    def get_part_data(self):
        roofparts = []
        #for pp in self.roof_stud_coords:
        for lowpoint, highpoint, profile, rotation in self.roof_stud_coords:
            roofparts.append(create_wood_at(lowpoint, highpoint, profile, rotation))
        return roofparts
