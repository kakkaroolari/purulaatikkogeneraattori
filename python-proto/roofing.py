import sys
import math
from point import Point3
from helpers import *
from transformations import (projection_matrix,
                             angle_between_vectors)
#from shapely.geometry import (box,
#                              LinearRing)

class RoofExpansionDefs( object ):
    def __init__( self, left=None, right=None, down=None, up=None):
        self._keys = {
            "left": [0,-1,0],
            "right": [0,1,0],
            "down": [1,0,0]
            }
        self._expander = {
            "left": left,
            "right": right,
            "down": down,
            "up": up,
            }

    def _get_key(self, key):
        return self._keys[key]

    def apply_expansion(self, open_loop, tolerance=1):
        ind = 0
        for point in open_loop[:-1]:
            toNext = point.GetVectorTo(open_loop[ind+1])
            toNext.z = 0 # level out to xy-plane
            # if vector is roof lape suuntainen, extrude
            expand = None
            for key, direction in self._keys.items():
                # big tolerance for jiiri, lyhty, whatnot.
                if angle_between_vectors(toNext.ToArr(), direction, directed=True) < math.radians(tolerance):
                    expand = self._expander[key]
                    break
            # paatyraystaat yli
            if expand is not None:
                open_loop[ind].Translate(expand)
                open_loop[ind+1].Translate(expand)
            ind += 1
        if self._expander["up"] is not None:
            open_loop[0].Translate(self._expander["up"])
            open_loop[-1].Translate(self._expander["up"])

        

class Roofing( object ):
    def __init__( self, section_name, chimney_spec):
        self.name = section_name
        self.chimney_world = chimney_spec
        self.roof_decs = []
        self.default_expander = RoofExpansionDefs(left=Point3(-600, 0, 0), right=Point3(600, 0, 0))
        self.cut_poly = []

    def set_cutpoly(self, points):
        self.cut_poly = points


    def do_one_roof_face(self, section_name, face_polygon, high_point_actual, dirstart=None, main_expansion=None):
        """ This is a geometry util func, Roofing will do the stuff.
            order is important. This comment is utter bollocks.
            todo: lape name
        """
        # first lape (xy plane)
        if dirstart is None:
            dirstart = face_polygon[0]
        direction = dirstart.GetVectorTo(face_polygon[1])
        #direction = face_polygon[oin-1].GetVectorTo(face_polygon[oin])
        direction = direction.Normalize(600)
        # fit plane world - roof center
        fit_plane_world = [face_polygon[0].Clone(), face_polygon[-1].Clone(), face_polygon[0].CopyLinear(0,0,1000)]
        #trace("fpw: ", fit_plane_world)
        # now we should project this in actual roof plane (xyz)
        origo = face_polygon[1].Clone()
        Y = origo.GetVectorTo(high_point_actual)
        X = origo.GetVectorTo(face_polygon[2].Clone())
        N = Point3.Cross(X, Y).Normalize()
        trace("norml: ", X,Y,N)
        #dotlen = Point3.Dot(face_polygon[0].GetVectorTo(face_polygon[1]), direction)
        firstside = face_polygon[0].GetVectorTo(face_polygon[1])
        coslen = 600 / math.cos(angle_between_vectors(firstside.ToArr(), direction.ToArr()))
        trace("coslen: ", coslen)
        angular = firstside.Clone().Normalize(coslen)
        face_polygon[1].Translate(angular)
        for point in face_polygon[2:-2]:
            # move raystas 600 mm outwards
            # TODO: This shit makes holppa==125.00 mm brake
            point.Translate(direction)
        # todo dry
        lastside = face_polygon[-1].GetVectorTo(face_polygon[-2])
        coslen = 600 / math.cos(angle_between_vectors(lastside.ToArr(), direction.ToArr()))
        trace("coslen: ", coslen)
        angular = lastside.Clone().Normalize(coslen)
        face_polygon[-2].Translate(angular)

        # tilt roof plane from xy plane to actual angle
        mat = projection_matrix(origo.ToArr(), N.ToArr(), direction=[0,0,1])
        geomPlane = TransformationPlane(origo, X, Y)
        transistor = Transformer(geomPlane) # geom plane is not used in convert_by_matrix
        trace("facepoly:", face_polygon)
        points_in_correct_plane = Transformer.convert_by_matrix(face_polygon, mat)
        trace("picp:", points_in_correct_plane)
        # create part data object
        roof_data = _RoofDeck(section_name, geomPlane)
        # now start creating hatch
        local_roof_poly = transistor.convertToLocal(points_in_correct_plane)
        #trace("local pts: ", local_roof_poly)
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
        if main_expansion is None:
            main_expansion = self.default_expander
        main_expansion.apply_expansion(local_roof_poly)
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
        decking_data, cut_objs, cut_planes, sides = self._generate_roof_deck(local_roof_poly, 125/2 + 22 + 32)
        # add chimney to cut solids
        local_chimney = None
        if self.chimney_world is not None:
            chimney = get_bounding_lines(self.chimney_world, transistor)
            cut_corners_local = []
            for corner_line in chimney:
                # isect level 62.5 + 22 + 32 ~
                isect = isect_line_plane_v3(corner_line[0].ToArr(), corner_line[1].ToArr(), [0,0,100])
                if isect is not None:
                    cut_corners_local.append(Point3(isect[0], isect[1], 0))
            if 4 == len(cut_corners_local):
                cut_corners_local[0].z = -200
                cut_corners_local[-1].z = 200
                local_chimney = create_cut_aabb(cut_corners_local)

        fit_plane_data_local = transistor.convertToLocal(fit_plane_world)
        fit_planes = [to_planedef(fit_plane_data_local)]
        roof_data.set_deck_data(decking_data, sides, cut_objs, cut_planes, fit_planes, local_chimney)
        self.roof_decs.append(roof_data)

    def _generate_roof_deck(self, polygon, z_offset):
        contour_points = []
        profile_height = 18.40
        profile_width = 1100 # this is important
        extend_z = z_offset + profile_height/2
        trace("decking z-off: ", z_offset)
        # extend 40 mm over
        extend_down = -(40+22+22)
        extend_up = 50
        extend_left_right_abs = profile_width/2
        # then battens
        ind = 0
        local_roof_poly = [p.Clone() for p in polygon] #.copy()
        expander = RoofExpansionDefs(left=Point3(-extend_left_right_abs, 0, 0),
                                     right=Point3(extend_left_right_abs, 0, 0),
                                     down=Point3(0, extend_down, 0),
                                     up=Point3(0, extend_up, 0))
        expander.apply_expansion(local_roof_poly)
        # use corner steels or not, and later..
        start_edge_cut = vertical_straight_or_fit([polygon[1], polygon[0]])
        end_edge_cut = vertical_straight_or_fit([polygon[-1], polygon[-2]])
        # todo: closedloop or not..
        roofing_poly = local_roof_poly
        if start_edge_cut is not None or end_edge_cut is not None:
            min_x, min_y, max_x, max_y = bounding_box(roofing_poly)
            # manual expansion, angled edges don't do that
            if start_edge_cut:
                min_x -= extend_left_right_abs
            if end_edge_cut:
                max_x += extend_left_right_abs
            page = box(min_x, min_y, max_x, max_y)
            roofing_poly = [Point3(p[0],p[1],0) for p in page.exterior.coords]
        steel_point_pairs = create_hatch(roofing_poly, profile_width, profile_width + 20, exact=True)
        decking_data = []
        for spp in steel_point_pairs:
            for point in spp:
                point.Translate(0, 0, extend_z)
            decking_data.append((spp, "S18-92W-1100-04", None,))
        
        # L100
        side_steels = []
        xlin = 100/2-1
        zlin = z_offset + profile_height - xlin
        #xabs = xlin
        extend_up2 = extend_up + 50 # todo: does not intersect
        lpp = [polygon[1].CopyLinear(xlin,extend_down,zlin), polygon[0].CopyLinear(xlin,extend_up2,zlin)]
        rpp = [polygon[-1].CopyLinear(-xlin,extend_up2,zlin), polygon[-2].CopyLinear(-xlin,extend_down,zlin)]
        if start_edge_cut is None:
            side_steels.append((lpp, "L100*100*1", Rotation.BACK,))
        if end_edge_cut is None:
            side_steels.append((rpp, "L100*100*1", Rotation.BACK,))
        # then cutting
        cuts = get_differences(polygon)
        cutAABBs = []
        for aabb in cuts:
            for point in aabb:
                point.Translate(0, extend_down, 0)
            aabb[0].Translate(0, -50, 0)
            cutAABBs.append(create_cut_aabb(aabb))
        # last cut is plane in the far end
        cutPlanes = []
        # check if either side diagonal
        for possible_fitting in [start_edge_cut, end_edge_cut]:
            if possible_fitting is not None:
                cutAABBs = []
                cutPlanes.append(possible_fitting)
        cutPlanes.append(create_cut_plane(polygon[-1], polygon[-2], Point3(1,0,0)))
        return decking_data, cutAABBs, cutPlanes, side_steels

    def get_roofs_faces(self):
        return self.roof_decs

def vertical_straight_or_fit(edge):
    edge_dir = edge[0].GetVectorTo(edge[1])
    zpoint = edge[0].CopyLinear(0,0,1)
    z_dir = edge[0].GetVectorTo(zpoint)
    normal = Point3.Cross(z_dir, edge_dir)
    if angle_between_vectors(edge_dir.ToArr(), [0,1,0], directed=False) < math.radians(1):
        return None
    return create_cut_plane(edge[0], edge[1], normal)

class _RoofDeck(object):
    def __init__( self, section_name, plane):
        self.name = section_name
        if not isinstance(plane, TransformationPlane):
            raise ValueError("Not transformation plane: ", plane)
        self.transformation_plane = plane
        self.roof_part_data = []
        self.roof_deck_data = []
        self.roof_cut_data = []
        self.roof_cut_parts = []

    def get_plane_data(self):
        origin = self.transformation_plane.origin()
        x = self.transformation_plane.x_axis()
        y = self.transformation_plane.y_axis()
        normal = Point3.Cross(x, y).ToArr()
        return origin, normal

    def add_part_data(self, lowpoint, highpoint, profile, rotation):
        self.roof_part_data.append((lowpoint.Clone(), highpoint.Clone(), profile, rotation,))

    def set_deck_data(self, deck_data, side_data, cut_data, cut_planes, fit_plane, chimney_cut):
        self.roof_deck_data = deck_data
        self.roof_side_data = side_data
        self.roof_cut_data = cut_data
        self.roof_cut_planes = cut_planes
        self.roof_fit_planes = fit_plane
        self.chimney_cut = chimney_cut

    def add_ext_cut_part(self, cut_points):
        # expecting these to be in world coordinates
        transistor = Transformer(self.transformation_plane)
        cut_polygon = transistor.convertToLocal(cut_points)
        # create a contour plate cut object
        cut_object = get_part_data("PL400", Rotation.FRONT, cut_polygon, "ANTIMATERIAL")
        self.roof_cut_parts.append(cut_object)

    def get_woods_data(self):
        roofparts = []
        #for pp in self.roof_stud_coords:
        for lowpoint, highpoint, profile, rotation in self.roof_part_data:
            roofparts.append(create_wood_at(lowpoint, highpoint, profile, rotation))
        # add steel
        return roofparts, self.transformation_plane, [self.chimney_cut], self.roof_fit_planes

    def get_steel_data(self):
        roofparts = []
        for points, profile, rotation in self.roof_deck_data:
            roofparts.append(get_part_data(profile, rotation, points, "S235JR", 3))
        # todo: add cut aabb's
        steel_cuts = self.roof_cut_data + [self.chimney_cut]
        return roofparts, self.transformation_plane, steel_cuts, self.roof_cut_planes, self.roof_cut_parts

    def get_sides_data(self):
        sideparts = []
        for points, profile, rotation in self.roof_side_data:
            sideparts.append(get_part_data(profile, rotation, points, "S235JR", 3))
        return sideparts, self.transformation_plane, self.roof_fit_planes

    def get_name(self):
        return self.name