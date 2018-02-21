import sys
import math
from point import Point3
from helpers import *
from transformations import (projection_matrix,
                             angle_between_vectors)

class Roofing( object ):
    def __init__( self, section_name):
        self.name = section_name
        self.roof_decs = []

    def do_one_roof_face(self, section_name, face_polygon, high_point_actual):
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
        # create part data object
        roof_data = _RoofDeck(section_name, geomPlane)
        #trace("roof is at: ", points_in_correct_plane)
        # now start creating hatch
        local_roof_poly = transistor.convertToLocal(points_in_correct_plane)
        #trace("local pts: ", local_points)
        holppa = 125.0
        one_face_point_pairs = create_hatch(local_roof_poly, 900.0, holppa, holppa)
        # convert back to global csys
        for pp in one_face_point_pairs:
            #pp2 = transistor.convertToGlobal(pp)
            pp2 = pp
            roof_data.add_part_data(pp2[0], pp2[1], "50*125", Rotation.FRONT)
        # rimat
        for rr in one_face_point_pairs:
            for point in rr:
                # rimat above the studs
                point.Translate(0,0,62.5 + 11)
            #rr2 = transistor.convertToGlobal(rr)
            rr2 = rr
            roof_data.add_part_data(rr2[0], rr2[1], "22*50", Rotation.TOP)
        # then battens
        ind = 0
        for point in local_roof_poly[:-1]:
            toNext = point.GetVectorTo(local_roof_poly[ind+1])
            toNext.z = 0 # level out to xy-plane
            # if vector is roof lape suuntainen, extrude
            expand = None
            if angle_between_vectors(toNext.ToArr(), [0,-1,0], directed=True) < math.radians(1):
                expand = Point3(-600, 0, 0)
            elif angle_between_vectors(toNext.ToArr(), [0,1,0], directed=True) < math.radians(1):
                expand = Point3(600, 0, 0)
            # paatyraystaat yli
            if expand is not None:
                local_roof_poly[ind].Translate(expand)
                local_roof_poly[ind+1].Translate(expand)
            ind += 1
        one_face_batten_pairs = create_hatch(local_roof_poly, 350.0, first_offset=50-22, horizontal=True)
        # add battens
        for bb in one_face_batten_pairs:
            for point in bb:
                # rimat above the studs
                point.Translate(0, 0, 125/2 + 22 + 32/2)
            #bb2 = transistor.convertToGlobal(bb)
            bb2 = bb
            #trace(bb2[0], bb2[1], "32*100")
            roof_data.add_part_data(bb2[0], bb2[1], "32*100", Rotation.TOP)
        #decking_profile_half = 20 # todo: educated guess at this juncture
        decking_data = self._generate_roof_deck(local_roof_poly, 125/2 + 22 + 32)
        roof_data.set_deck_data(decking_data)
        self.roof_decs.append(roof_data)

    def _generate_roof_deck(self, polygon, z_offset):
        contour_points = []
        profile_height = 18.40
        z_offset += profile_height/2
        trace("decking z-off: ", z_offset)
        # extend 40 mm over
        extend_down = -(40+22+22)
        for node in polygon[1:-1]:
            contour_points.append(node.CopyLinear(0, extend_down, z_offset))
        # end points towards centerline
        extend_up = 50
        contour_points = [polygon[0].CopyLinear(0, extend_up, z_offset)] + \
                         contour_points + \
                         [polygon[-1].CopyLinear(0, extend_up, z_offset)]
        # todo: closedloop or not..
        profile_width = 1100 # this is important
        steel_point_pairs = create_hatch(contour_points, profile_width, profile_width/2, exact=True)
        decking_data = []
        for spp in steel_point_pairs:
            decking_data.append((spp, "S18-92W-1100-04", None,))
        return decking_data

    def get_roofs_faces(self):
        return self.roof_decs

class _RoofDeck(object):
    def __init__( self, section_name, plane):
        self.name = section_name
        if not isinstance(plane, TransformationPlane):
            raise ValueError("Not transformation plane: ", plane)
        self.transformation_plane = plane
        self.roof_part_data = []
        self.roof_deck_data = []

    def add_part_data(self, lowpoint, highpoint, profile, rotation):
        self.roof_part_data.append((lowpoint.Clone(), highpoint.Clone(), profile, rotation,))

    def set_deck_data(self, deck_data):
        self.roof_deck_data = deck_data

    def get_part_data(self):
        roofparts = []
        #for pp in self.roof_stud_coords:
        for lowpoint, highpoint, profile, rotation in self.roof_part_data:
            roofparts.append(create_wood_at(lowpoint, highpoint, profile, rotation))
        # add steel
        for points, profile, rotation in self.roof_deck_data:
            roofparts.append(get_part_data(profile, rotation, points, "S235JR", 3))
        # todo: add cut aabb's
        return roofparts, self.transformation_plane

    def get_name(self):
        return self.name