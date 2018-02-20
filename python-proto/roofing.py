import sys
import math
from point import Point3
from helpers import *
from transformations import projection_matrix

class Roofing( object ):
    def __init__( self, section_name):
        self.name = section_name
        self.point_pairs = []

    def do_one_roof_face(self, face_polygon, high_point_actual):
        """ This is a geometry util func, Roofing will do the stuff.
            order is important. This comment is utter bollocks.
        """
        # first lape (xy plane)
        direction = face_polygon[0].GetVectorTo(face_polygon[1])
        direction = direction.Normalize(600)
        # now we should project this in actual roof plane (xyz)
        origo = face_polygon[1].Clone()
        A = origo.GetVectorTo(high_point_actual)
        B = origo.GetVectorTo(face_polygon[2])
        N = Point3.Cross(A, B)
        for point in face_polygon[1:-1]:
            # move raystas 600 mm outwards
            # TODO: This shit makes holppa==125.00 mm brake
            point.Translate(direction)
        # tilt roof plane from xy plane to actual angle
        mat = projection_matrix(origo.ToArr(), N.ToArr(), direction=[0,0,1])
        geomPlane = TransformationPlane(origo, B, A)
        self.transistor = Transformer(geomPlane) # geom plane is not used in convert_by_matrix
        points_in_correct_plane = self.transistor.convert_by_matrix(face_polygon, mat)
        trace("roof is at: ", points_in_correct_plane)
        # now start creating hatch
        local_points = self.transistor.convertToLocal(points_in_correct_plane)
        holppa = 125.0
        one_face_point_pairs = create_hatch(local_points, 900.0, holppa, holppa, ends_tight=True)
        # convert back to global csys
        #face_to_world = transistor.convertToGlobal(one_face_point_pairs)
        self.point_pairs.append(one_face_point_pairs)

    def get_part_data(self):
        roofparts = []
        for pp in self.point_pairs:
            for lowpoint, highpoint in pp:
                #endpoint.Translate(0,0,outwards)
                #offsetted()
                # roof truss 5x2's
                line_to_world = self.transistor.convertToGlobal([lowpoint, highpoint])
                roofparts.append(create_wood_at(line_to_world[0], line_to_world[1], "50*125", Rotation.FRONT))
        return roofparts
