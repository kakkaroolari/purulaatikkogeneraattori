# Don't know my licence.  ask.
from __future__ import print_function
import sys
import os
import pprint
from point import Point3
from stiffeners import Stiffener
from cladding import Cladding
from roofing import Roofing, RoofExpansionDefs
from windowframer import WindowFramer, windowDef, HoleDef
import itertools #import izip
import json
import math
from helpers import *


cornerwoodcolor = 41
#chimney_x = 3110
porch_depth = 3000
#chimney_y = 3080 + porch_depth

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def centroid(points):
    x = [p.x for p in points]
    y = [p.y for p in points]
    z = [p.z for p in points]
    centroid = Point3(sum(x) / len(points), sum(y) / len(points), sum(z) / len(points))
    return centroid

def toDistances(distanceList):
    sum = 0.0
    absolutes = []
    for dd in distanceList:
        absolutes.append(dd + sum)
        sum += dd
    return absolutes


def generate_loop(grid_x, grid_y, grid_z, pairs):
    master_polygon = []
    xx = toDistances(grid_x)
    yy = toDistances(grid_y)
    if not grid_z: #hack
        grid_z = [0.0]
    zz = toDistances(grid_z)
    #for x_ind,y_ind,z_ind in pairs:
    for item in pairs:
        z_ind = None
        try:
            x_ind,y_ind,z_ind = item
        except ValueError:
            x_ind,y_ind = item
        if not z_ind:
            z_ind = 0
        # zero level z
        edge = Point3(xx[x_ind], yy[y_ind], zz[z_ind])
        master_polygon.append(edge)
    return master_polygon

def is_closed_loop(grid):
    closed = grid[0].Compare(grid[-1])
    #trace("closed: ", closed)
    return closed

def is_short_side(p1, p2):
    # TODO: assumes purulaatikko always oriented same
    return abs(p2.y-p1.y) > 5000 

def clad_def(polygon, windows, elevations, usefits=False):
    return {'poly': polygon, 'windows': windows, "elevations": elevations, 'usefits': usefits}

def get_wall_section_by(section, attribute, getprop, wallname):
    #wallname = attribute #sect['name']
    for x in section: #specification['holedefs']:
        if x[attribute] == wallname:
            #trace("i found it!")
            prop = x[getprop]
            break
    else:
        trace("did not find it: ", wallname)
        prop = None
    return prop

def write_out(specification):
    # main grids
    grid_x = specification['grid_x']
    grid_y = specification['grid_y']
    grid_z = specification['grid_z']
    pelevs_z = specification['elev_z']
    roof_angle = specification['roofangle']
    porchroofangle = roofangle
    chimney_x = specification['chimney_x']
    chimney_y = specification['chimney_y']
    chimney_profile = specification['chimney_profile']
    footingProfile = specification['foundations'][0]["profile1"]
    sockleProfile = specification['foundations'][0]["profile2"]
        #sockle = "800*200"
    #footing = "200*500"


    # define line, or grid intersect
    pairs = specification['foundations'][0]["edges"]
    master_polygon = generate_loop(grid_x, grid_y, None, pairs)
    #trace(pprint.pformat(master_polygon))

    # porch grid elevations (keep separate)
    porch = specification['foundations'][1]["edges"]
    porch_polygon = generate_loop(grid_x, grid_y, None, porch)
    # get_plane_data

    high_pairs1 = [(0,1),
        (3,1)]
    high_pairs2 = [(0,3),
        (3,3)]
    high_polygon1 = generate_loop(grid_x, grid_y, None, high_pairs1)
    high_polygon2 = generate_loop(grid_x, grid_y, None, high_pairs2)

    # create window aabb's, possibly to be used all over the place
    #level1 = 1160
    #level2 = 4500 # random ass, todo: measure it
    holedefs = []
    holedefs_byname = {}
    for holedef in specification['holedefs']:
        wall_name = holedef['wall_line']
        wall_def = get_wall_section_by(specification['wall_sections'], "name", "line", wall_name)
        wall_line = generate_loop(grid_x, grid_y, grid_z, wall_def)
        window_defs = [windowDef([wd['offset'], wd['level']], wd["hole"], wd["splitters"]) for wd in holedef['holes']]
        holedefs.append((wall_line, window_defs,))
        holedefs_byname[wall_name] = window_defs
    window_cuts, window_woods = create_window_boxes(holedefs)
    trace("Holes for: ", len(window_cuts), " windows.", window_cuts)

    # chimney pipe
    section_cut = generate_loop(grid_x, grid_y, grid_z, [(0,1,0), (0,3,0), (0,3,3)])
    chimney_parts, pipe_cut = create_chimneypipe(section_cut, x=chimney_x, y=chimney_y, profile=chimney_profile, roofangle=roof_angle)

    # todo: move somplace more appropriate?
    fieldsaw = Cladding("cladding")
    board_areas = {}
    for sect in specification['wall_sections']:
        wallname = sect['name']
        elevations_key = sect['elevations']
        holes = holedefs_byname.get(wallname, None)
        segment_def = [tuple(pt) for pt in sect['line']]
        #trace("segdef: ", segment_def)
        board_areas[wallname] = clad_def(segment_def, holes, elevations_key, sect['usefits'])

    #porch_facades = {
    #    "kuisti_vas":   clad_def([(0,1,1),(0,0,1),(0,0,3),(0,1,3)],         None),
    #    "kuisti_etu":   clad_def([(0,0,1),(2,0,1),(2,0,3),(1,0,4),(0,0,3)], None, usefits=True),
    #    "kuisti_oik":   clad_def([(2,0,1),(2,1,1),(2,1,3),(2,0,3)],         None)
    #    }

    # corner boards
    corner_boards = create_corners_woods(grid_x, grid_y, specification, cornerwoodcolor)

    mass_center = centroid(master_polygon)
    # TODO: make the layers bottom up and increase z offset
    z_offset = parse_height(footingProfile)
	# todo: use previous profile for xy-plane offset
	#xy_offset = parse_width(footingProfile)
    footing = generate_footing(master_polygon, footingProfile, sockleProfile)
    sockle = generate_sockle(master_polygon, sockleProfile, z_offset)
    lower_reach = generate_lower_reach(master_polygon, 1000.0)
    higher_reach = generate_lower_reach(high_polygon1, 4750.0, mass_center)
    higher_reach += generate_lower_reach(high_polygon2, 4750.0, mass_center)
    wall_studs = generate_wall_studs(master_polygon, 1000.0, 3650, roof_angle)

    # bit different
    roof_woody = generate_main_roof(grid_x, grid_y, specification, pipe_cut)

    # porch
    #porch_decline = porch_depth*math.tan(math.radians(roof_angle))
    footing += generate_footing(porch_polygon, footingProfile, sockleProfile)
    sockle += generate_sockle(porch_polygon, sockleProfile, z_offset)
    offset_porch_woods_outwards(porch_polygon, mass_center)
    lower_reach += generate_lower_reach(porch_polygon, toDistances(pelevs_z)[1])
    higher_reach += generate_lower_reach(porch_polygon, toDistances(pelevs_z)[2])
    wall_studs += generate_wall_studs(porch_polygon, toDistances(pelevs_z)[1], pelevs_z[2]-100)
    porch_roofer = create_porch_roof(grid_x, grid_y, pelevs_z, roof_woody)

    # inner walls
    inside_walls = create_inside(chimney_x, chimney_y)
    #inside_walls = []
    #trace("iw: ", inside_walls)

    ## main json
    combined_data = [named_section("footing", footing),
            named_section("sockle", sockle),
            named_section("chimney", chimney_parts),
            named_section("lower_reach", lower_reach, 4),
            named_section("higher_reach", higher_reach, 3),
            named_section("wall_studs", wall_studs, 3),
            #named_section("inside_walls", inside_walls[0], 3),
            named_section("window_edges", window_woods),
            named_section("corner_boards", corner_boards)]

    # inside walls
    for idx in range(len(inside_walls)):
        wall, aabb = inside_walls[idx]
        cutsolids = None
        if aabb is not None:
            cutsolids = [aabb]
        combined_data.append(named_section("inside_wall_{}".format(idx), wall, 3, solids=cutsolids))


    # stiffener experiment
    stiffeners = stiffen_wall("mainwall", master_polygon, 1000.0, 3850, roof_angle, mass_center)
    # todo: 
    porch_height = pelevs_z[-2] + 100
    porch_stiffeners = stiffen_wall("porch", porch_polygon, 1000.0, porch_height, roof_angle, mass_center)
    

    for stf in stiffeners + porch_stiffeners:
        cuts = stf.get_cut_planes()
        fits = stf.get_fit_planes()
        #combined_data.append(named_section(stf.name, stf.get_stiffener_data(), planes=cuts, fits=fits, solids=window_cuts))

    # cladding boards
    append_cladding_data(board_areas, combined_data, specification, fieldsaw, window_cuts)
    #append_cladding_data(porch_facades, combined_data, grid_x, grid_y, pelevs_z, fieldsaw, [])

    #for key, value in board_areas.items():
    #    segment_name = "cladding_" + key
    #    trace("Creating cladding for: ", segment_name)
    #    segment_polygon = value['poly']
    #    segment_windows = value['windows']
    #    segment_isfitted = value['usefits']
    #    cladding_loop = generate_loop(grid_x, grid_y, grid_z, segment_polygon)
    #    wall_parts, fittings = fieldsaw.create_cladding(cladding_loop, "22*125", 33, segment_windows, fittings=segment_isfitted)
    #    combined_data.append(named_section(segment_name, wall_parts, 44, solids=window_cuts, planes=fittings, fits=fittings))

    #trace("roof_woody: ", roof_woody.get_roofs_faces(), porch_roofer.get_roofs_faces())
    for roof_face in roof_woody.get_roofs_faces() + porch_roofer.get_roofs_faces():
        trace("add roof: ", roof_face.get_name())
        #TDD 553 3
        # woods
        part_data, coord_sys, cut_aabbs, fit_planes = roof_face.get_woods_data()
        name = roof_face.get_name()
        combined_data.append(named_section("roof_woods_"+name, part_data, ts_class=12, csys=coord_sys,
                                           solids=cut_aabbs, fits=fit_planes))
        # steels
        geom_data, coord_sys, cut_aabbs, cut_planes, cub_objs = roof_face.get_steel_data()
        combined_data.append(named_section("roof_steels_"+name, geom_data, ts_class=3, csys=coord_sys, 
                                           solids=cut_aabbs, planes=cut_planes, contours=cub_objs))
        # side steels
        sides_data, coord_sys, fit_planes = roof_face.get_sides_data()
        combined_data.append(named_section("roof_sides_"+name, sides_data, ts_class=3, csys=coord_sys,
                                          fits=fit_planes))

    with open('data.json', 'w') as jsonfile:
        json.dump(combined_data, jsonfile, cls=MyEncoder, indent=2)
        #jsonfile.write(pprint.pformat(combined_data))
    print("wrote:\n\b", os.getcwd() + os.path.sep + "data.json")

def append_cladding_data(clad_defs, append_to, specification, fieldsaw, window_cuts):
    gridx = specification['grid_x']
    gridy = specification['grid_y']
    for key, value in clad_defs.items():
        segment_name = "cladding_" + key
        trace("Creating cladding for: ", segment_name)
        segment_polygon = value['poly']
        segment_windows = value['windows']
        segment_isfitted = value['usefits']
        segment_elevations_name = value['elevations']
        trace("s.e.n: ", segment_elevations_name)
        gridz = specification[segment_elevations_name]
        cladding_loop = generate_loop(gridx, gridy, gridz, segment_polygon)
        wall_parts, fittings = fieldsaw.create_cladding(cladding_loop, "22*125", 33, segment_windows, fittings=segment_isfitted)
        append_to.append(named_section(segment_name, wall_parts, 44, solids=window_cuts, planes=fittings, fits=fittings))

def named_section(name, part_list, ts_class=None, planes=None, csys=None, solids=None, fits=None, contours=None):
    # todo: can add assembly meta, classes etc.
    if ts_class is not None:
        for part in part_list:
            part["klass"] = ts_class
    return { 
        "section": name, 
        "parts": part_list, 
        "planes": remove_none_elements_from_list(planes), 
        "coordinate_system": csys,
        "cutobjects": remove_none_elements_from_list(solids),
        "fitplanes": remove_none_elements_from_list(fits),
        "cutcontours": remove_none_elements_from_list(contours)
        }

def generate_lower_reach(polygon, z_offset, mass_center=None):
    return generate_offsetted_beams(polygon, "100*100", 50.0, z_offset + 50.0, "Timber_Undefined", mass_center)

def offset_porch_woods_outwards(porch_polygon, mass_center):
    porch_mass = centroid(porch_polygon)
    between = porch_mass.GetVectorTo(mass_center)
    if abs(between.x) > abs(between.y):
        # extrude x-axis
        outwards_for_stiffeners = Point3(-22, 0, 0)
    else:
        outwards_for_stiffeners = Point3(0, -22, 0)
    porch_polygon[0].Translate(outwards_for_stiffeners)
    porch_polygon[-1].Translate(outwards_for_stiffeners)

def create_window_boxes(windows):
    # in: wall plane in 3d
    #     + vector wall-normal(?)
    #     + distance from start
    #     + window size
    aabbs = []
    #trace("glb: ", cornerwoodcolor)
    windower = WindowFramer(cornerwoodcolor)
    for wall_line in windows:
        line, defs = wall_line
        transform, rotation = create_vertical_stdplane(line)
        wall_local = transform.convertToLocal(line)
        # create aabb's
        for win_def in defs:
            low, high = win_def.minmax_points()
            in_world = transform.convertToGlobal([low, high])
            aabbs.append(create_cut_aabb(in_world))
            # window wood cutter
            windower.add_window(transform, low, high, rotation, win_def.multiframe())
    return aabbs, windower.get_framing_woods()

def create_corners_woods(grid_x, grid_y, spec, cornerwoodcolor):
    corner_woods = []
    for corner_spec in spec["corner_woods"]:
        segment_elevations_name = corner_spec["elevations"]
        grid_z = gridz = spec[segment_elevations_name]
        z_level = corner_spec["z_level"]
        loop = generate_loop(grid_x, grid_y, grid_z, corner_spec["points"])
        corner_woods += create_corner_boards([loop], cornerwoodcolor, z_level)
    return corner_woods

def create_corner_boards(corner_loops, cornerwoodcolor, z_level):
    corner_woods = []
    for corner_tri in corner_loops:
        #trace("corner tri: ", corner_tri)
        # create 2d coord sys
        height = corner_tri[1].z - corner_tri[0].z
        X = corner_tri[0].GetVectorTo(corner_tri[-1])
        Y = corner_tri[0].GetVectorTo(corner_tri[1])
        rotation = direction_to_rotation(Point3.Cross(X, Y))
        rotation2 = direction_to_rotation(Point3.Reversed(X))
        #trace("corner xy: ", corner_tri[0], X, Y)
        coordinate_system = TransformationPlane(corner_tri[0], X, Y)
        transform = Transformer(coordinate_system)
        corner_local = transform.convertToLocal(corner_tri)
        # offsetting
        profile1 = "22*125" # forwards
        half1 = parse_width(profile1)/2
        thick1 = parse_height(profile1)
        profile2 = "22*100" # behind
        half2 = parse_width(profile2)/2
        thick2 = parse_height(profile2)
        # forwards
        offset_x1 = -(z_level+thick2) + half1
        offset_z1 = z_level + thick1/2
        locallow = corner_local[0].CopyLinear(offset_x1, 0, offset_z1)
        localhigh = locallow.CopyLinear(0,height,0)
        in_world = transform.convertToGlobal([locallow, localhigh])
        corner_woods.append(create_wood_at(in_world[0], in_world[1], profile1, rotation, cornerwoodcolor))
        # behind
        offset_x2 = -(z_level+thick2/2)
        offset_z2 = z_level - half2
        locallow = corner_local[0].CopyLinear(offset_x2, 0, offset_z2)
        localhigh = locallow.CopyLinear(0,height,0)
        in_world = transform.convertToGlobal([locallow, localhigh])
        corner_woods.append(create_wood_at(in_world[0], in_world[1], profile2, rotation2, cornerwoodcolor))
    return corner_woods

def create_chimneypipe(section_cut, x, y, profile, roofangle):
    pro_x = parse_height(profile)
    pro_y = parse_width(profile)
    delta_x = pro_x/2
    delta_y = pro_y/2
    startPoint = Point3(x+delta_x, y+delta_y, 0)
    # section cut at least 3 points
    # tilt cut section plane to yz plane at placement of chimney
    projection = projection_matrix(startPoint.ToArr(), [1,0,0], direction=[1,0,0])
    section_cut_at_chimney = Transformer.convert_by_matrix(section_cut, projection)
    profiler = create_cut_aabb(section_cut_at_chimney)
    height = profiler['max_point'].z
    wall_lenght = profiler['max_point'].y - profiler['min_point'].y
    ceiling = get_ceiling(startPoint, section_cut_at_chimney[0], height, wall_lenght, roofangle)
    main_elevation = ceiling + 800
    endPoint = startPoint.CopyLinear(0, 0, main_elevation) # regs. 800 mm over
    cutting_aabb = create_cut_aabb([Point3(x,y,0), Point3(x+pro_x, y+pro_y, main_elevation)])
    concrete_parts = []
    concrete_parts.append(get_part_data(profile, None, [startPoint, endPoint], "Concrete_Undefined"))
    # hifistely
    joined = endPoint.Clone()
    top_elev = joined.CopyLinear(0, 0, 85) # module
    end_profile = "{}*{}".format(parse_height(profile)+130, parse_width(profile)+130)
    concrete_parts.append(get_part_data(end_profile, None, [joined, top_elev], "Concrete_Undefined"))
    return concrete_parts, cutting_aabb

def generate_main_roof(grid_x, grid_y, spec, chimney_pipe):
    testroof0 = spec["roof_sections"][0]
    testgridz = spec["grid_z"]
    # xy plane
    #roof_tuples_1 = [(0,2,3), # with porch roof extension
    #    (0,1,3),
    #    #(1,1,4),
    #    #(1,0,4),
    #    #(2,0,4),
    #    #(2,1,4),
    #    (3,1,3),
    #    (3,2,3)]
    roof_polygon_1 = generate_loop(grid_x, grid_y, testgridz, testroof0["faces"][0]["edges"])
    #trace("roof poly 1: ", roof_polygon_1)
    #roof_tuples_2 = [(3,2,3),
    #    (3,3,3),
    #    (0,3,3),
    #    (0,2,3)]
    roof_polygon_2 = generate_loop(grid_x, grid_y, testgridz, testroof0["faces"][1]["edges"])
    # centerline at highest elevation
    centerline = generate_loop(grid_x, grid_y, testgridz, testroof0["centerline"])
    #trace("roof centerline: ", centerline)
    roofer = Roofing("roof_studs", chimney_pipe)
    #direction1 = roof_polygon1[0].GetVectorTo(
    roofer.do_one_roof_face("lape_1", roof_polygon_1, centerline[0])
    roofer.do_one_roof_face("lape_2", roof_polygon_2, centerline[1])
    # todo: hack, return face1 plane outside

    return roofer

def create_porch_roof(grid_x, grid_y, pgrid_z, main_roofer):
    # isect porch roof to main roof: p0, p1, origo, normal
    pgrid_x = grid_x[:3]
    pgrid_y = grid_y[:2]
    centerline = generate_loop(pgrid_x, pgrid_y, pgrid_z, [(1,1,-1),(1,0,-1)])
    pco, pno = main_roofer.roof_decs[0].get_plane_data()
    p1 = centerline[0].ToArr()
    p2 = centerline[1].ToArr()
    pl = generate_loop(pgrid_x, pgrid_y, pgrid_z, [(0,1,2)])
    pr = generate_loop(pgrid_x, pgrid_y, pgrid_z, [(2,1,2)])
    #trace("wtf: ", p1,p2,pco,pno)
    rooftip = Point3.FromArr(isect_line_plane_v3(p1,p2,pco,pno))
    lape1l = Point3.FromArr(isect_line_plane_v3(p1,pl[0].ToArr(),pco,pno))
    lape2r = Point3.FromArr(isect_line_plane_v3(p1,pr[0].ToArr(),pco,pno))

    # xy plane
    roof_tuples_1 = [(1,-1,-2),
        (0,-1,-2),
        (0,0,-2),
        (1,0,-2)]
    #trace("pw3: ", pgrid_x, pgrid_y, pgrid_z)
    roof_polygon_1 = generate_loop(pgrid_x, pgrid_y, pgrid_z, roof_tuples_1)
    roof_tuples_2 = [(1,0,-2),
        (2,0,-2),
        (2,-1,-2),
        (1,-1,-2)]
    #trace("pw3: ", pgrid_x, pgrid_y, pgrid_z)
    roof_polygon_2 = generate_loop(pgrid_x, pgrid_y, pgrid_z, roof_tuples_2)

    cut_object = None
    if rooftip is not None and lape1l is not None and lape2r is not None:
        #dist_ytop = rooftip.distFrom(centerline[0]
        xyplane_elevation = roof_polygon_1[0].z
        #highpoint = centerline[0].
        unadjusted_y = centerline[0].y
        #unadjusted_yr = centerline[1].y
        #centerline[0] = rooftip.Clone()
        # lape 1
        cut_tip = rooftip.Clone()
        rooftip.z = xyplane_elevation
        #lape1p2 = Point3(lape1l.x, rooftip.y, xyplane_elevation)
        lape1p3 = Point3(lape1l.x, unadjusted_y, xyplane_elevation)
        # lape 2
        lape2p_3 = Point3(lape2r.x, unadjusted_y, xyplane_elevation)
        lape2p_2 = Point3(lape2r.x, rooftip.y, xyplane_elevation)
        #roof_polygon_1 = [rooftip, lape1p2, lape1p3] + roof_polygon_1[1:]
        roof_polygon_1 = [rooftip] + roof_polygon_1[1:]
        roof_polygon_2 = roof_polygon_2[:-1] + [rooftip]
        trace("roof_polygon_1: ", roof_polygon_1)
        trace("centerline: ", centerline)
        # cut main roof with the extension
        cut_vector1 = cut_tip.GetVectorTo(lape1l)
        cut_vector2 = cut_tip.GetVectorTo(lape2r)
        cut_vector1 = cut_vector1.Normalize(1.2*(1000 + cut_vector1.magnitude()))
        cut_vector2 = cut_vector2.Normalize(1.2*(1000 + cut_vector2.magnitude()))
        cut_polygon = [cut_tip, cut_tip.CopyLinear(cut_vector1), cut_tip.CopyLinear(cut_vector2)]
        #cut_object = get_part_data("PL200", Rotation.FRONT, cut_polygon, "ANTIMATERIAL")
        # TODO: hardcoder roofdeck order, 0 is the porch side
        cut_world = main_roofer.roof_decs[0].add_ext_cut_part(cut_polygon)

    roofer = Roofing("porch_rafters", None)

    expansion1 = RoofExpansionDefs(right=Point3(600, 0, 0))
    expansion2 = RoofExpansionDefs(left=Point3(-600, 0, 0))
    start1 = centerline[0].Clone()
    start1.z = xyplane_elevation
    #direction1 = start1.GetVectorTo(roof_polygon_1[1])
    #trace("direction1", direction1)
    roofer.do_one_roof_face("porch_lape_1", roof_polygon_1, centerline[0], start1, main_expansion=expansion1)
    #start2 = centerline[1].Clone()
    #start2.z = xyplane_elevation
    #direction2 = start2.GetVectorTo(roof_polygon_2[1])
    roofer.do_one_roof_face("porch_lape_2", roof_polygon_2, centerline[1], main_expansion=expansion2)
    # todo: hack, return face1 plane outside
    #if cut_polygon is not None:

    return roofer #, cut_polygon


def create_one_side_trusses(begin, mainwall, mainwall_length, count, last, holppa, half_width, roofelevation, halflife2, roofdeclination):
    direction = mainwall.Clone()
    pt_array = point_grid(begin, direction, count, holppa, 900)
    # stupid way to add last roof truss
    towards = Point3.Normalize(direction, last)
    last_ninja = pt_array[-1].Clone()
    last_ninja.Translate(towards)
    pt_array.append(last_ninja)
    roofparts = []
    for ii in range(len(pt_array)):
        lowpoint = pt_array[ii]
        highpoint = lowpoint.CopyLinear(0, half_width, roofelevation)
        lowpoint.Translate(0, halflife2, roofdeclination)
        # roof truss 5x2's
        roofparts.append(create_wood_at(lowpoint, highpoint, "50*125", Rotation.FRONT))
    return roofparts

def stiffen_wall(prefix, stiff_poly, z_offset, height, roof_angle, mass_center):
    centerlines = generate_offsetted_lines(stiff_poly, -11.0, z_offset, None, mass_center)
    # todo stiff it up
    stiffs = []
    counter = 1
    for aa,bb in centerlines:
        use_angle = None
        is_short = False
        if is_short_side(aa,bb):
            use_angle = roof_angle
            is_short = True
        wallline = aa.GetVectorTo(bb)
        #rotation = direction_to_rotation(wallline)
        eps = Stiffener(prefix + "_" + str(counter), mass_center)
        #trace(aa, bb, height, use_angle)
        eps.stiffener_one_plane(aa, bb, height, use_angle)
        stiffs.append(eps)
        #for ss,tt in eps:
        #   stiffs.append(create_wood_at(ss,tt, "22*100", Rotation.FRONT))
    return stiffs



def generate_wall_studs(polygon, z_offset, height, roofangle=None):
    # todo: purulaatikko constant
    xy_offset = 50.0
    centerlines = generate_offsetted_lines(polygon, xy_offset, 1100.0)
    # run points around each lower wood k600
    studpoints = []
    first_item = True
    for start,end in centerlines:
        wall_begin = start.Clone()
        # do one wall line
        direction = start.GetVectorTo(end)
        rotation = direction_to_rotation(direction)
        #trace("beam rot type: ", type(rotation))
        length = start.distFrom(end)
        count = int((length - 200.0) / 600.0)
        # stud grid along one edge
        first_offset = -50
        if first_item and not is_closed_loop(polygon):
            first_offset = 0
        wood_grid = point_grid(start, direction, count, first_offset, 600)
        use_ceiling = is_short_side(start,end) and roofangle # todo something smarter
        for ii in range(len(wood_grid)):
            lowpoint = wood_grid[ii].Clone()
            current_height = height
            # normal 4x2's
            profile = "50*100"
            if ii == 0:
                # corners have 4x4
                profile = "100*100"
            elif use_ceiling:
                current_height = get_ceiling(lowpoint, wall_begin, height, length, roofangle) + 50
            highpoint = lowpoint.CopyLinear(0,0,current_height)
            studpoints.append(create_wood_at(lowpoint, highpoint, profile, rotation))
        first_item = False
    return studpoints

def point_grid(startpoint, dir_vector, count, first_offset, kdist):
    grid = []
    direction = dir_vector.Clone()
    # normal 4x2's
    current = startpoint.Clone()
    if abs(first_offset) > 0.5:
        towards = Point3.Normalize(direction, first_offset)
        current.Translate(towards)
    grid.append(current.Clone())
    towards = Point3.Normalize(direction, kdist)
    #trace("start: {0}, end:{1}, direction: {2}".format(start, end, direction))
    for i in range(count):
        #trace("counting: ", i)
        current.Translate(towards)
        grid.append(current.Clone())
    return grid


def generate_sockle(foundationPolygon, sockleProfile, z_offset):
    sockleCenter = []

    for node in foundationPolygon:
        # kinda cloning
        clonepoint = node.Clone()
        clonepoint.Translate(0, 0, z_offset)
        sockleCenter.append(clonepoint)
    # todo: closedloop or not..
    return [get_part_data(sockleProfile, None, sockleCenter, "Concrete_Undefined", 1)]

def generate_footing(foundationPolygon, footingProfile, sockleProfile):
	# footing is not centerline, but polybeam concrete panel is outer limits
    # move sockle to footing center, sockle polygon is not centerline but
	# outer limits to get the polybeam fully casted in closed loop corner.
    sockleWidth = parse_width(sockleProfile)
    xy_offset = sockleWidth / 2
    footingCenterZ = parse_height(footingProfile) / 2
    return generate_offsetted_beams(foundationPolygon, footingProfile, xy_offset, footingCenterZ, "Concrete_Undefined")
    
def generate_offsetted_beams(polygon, profile, xy_offset, z_offset, material, mass_center = None):
    #xy_offset = parse_width(profile)/2
    centerlines = generate_offsetted_lines(polygon, xy_offset, z_offset, profile, mass_center)
    beams = []
    first_item = True
    for aa,bb in centerlines:
        first_offset = -50
        if is_closed_loop(polygon) or not first_item:
            first_offset = 0
        if abs(first_offset) > 0.5:
            direction = aa.GetVectorTo(bb)
            towards = Point3.Normalize(direction, first_offset)
            aa.Translate(towards)
        beams.append(get_part_data(profile, None, [aa, bb], material))
        first_item = False
    return beams
    
def extend_or_subtract(polygon, xy_offset, z_offset, mass_center):
    if not mass_center:
        mass_center = centroid(polygon)
    footingCenter = []
	#if instanceof(profile, float):
	#	h_offset = profile
	#else
	#	h_offset = parse_width(profile)/2
    for node in polygon:
        # todo: parse from profile
        #endpoint = node
        #if len(polygon) > 2:
        endpoint = node.moveCloserTo(mass_center, xy_offset)
        endpoint.Translate(0, 0, z_offset)
        footingCenter.append(endpoint)
    return footingCenter

def generate_offsetted_lines(master_polygon, xy_offset, z_offset, adjustByProfile=None, mass_center=None):
    # move points i.e. 50mm closer to structure center (to 100*100 beam centerline)
    footingCenter = extend_or_subtract(master_polygon, xy_offset, z_offset, mass_center)
    footingLines = pairwise(footingCenter)
    polygonMidpoints = []
    adjustEndPoints = xy_offset
    if adjustByProfile is not None:
        # footing pads have different widht than xy_offset
        adjustEndPoints = parse_width(adjustByProfile) / 2
    #undisclosed_ending =
    first_item = True
    for start,end in footingLines:
        vector = start.GetVectorTo(end)
        #trace(start, )
        corners = Point3.Normalize(vector, adjustEndPoints)
        #trace("start: {0}, end:{1}, direction: {2} translate vector:
        #{3}".format(start, end, vector, corners,))
        #start.Translate(corners)
        #end.Translate(corners)
        aa = start.Clone()
        bb = end.Clone()
        if not first_item or is_closed_loop(master_polygon):
            aa.Translate(corners)
        #else:
        #    trace("------------ skip 1")
        #if not is_last_item(master_polygon, bb) and
        #is_closed_loop(master_polygon):
        bb.Translate(corners)
        #else:
        #    trace("------------ skip -1")
        polygonMidpoints.append((aa,bb,))
        #footings.append({
        #    "profile": profile,
        #    "points": [aa, bb],
        #    "material": material
        #})
        first_item = False
    return polygonMidpoints

def looper(gx, gy, gz, xy1, xy2, zlow=0, zup=1):
    grid_points = []
    for x,y in [xy1, xy2]:
        grid_points.append((x,y,zlow))
    for x,y in [xy2, xy1]:
        grid_points.append((x,y,zup))
    return generate_loop(gx, gy, gz, grid_points)

def create_inside(chimney_x, chimney_y):
    # create grids
    boards = 22 #+ 13
    outer_wall = 100 + boards
    inside_wall = 170 #100 + 2*boards
    porch_off = porch_depth + outer_wall
    igrid_x = [outer_wall, chimney_x - outer_wall, 620-inside_wall/2, inside_wall/2, 5280-boards]
    igrid_y = [porch_off, (chimney_y-porch_off), inside_wall/2, 900-inside_wall, inside_wall/2, 3520-boards]
    igrid_z = [1200.00, 2500.0]
    # first inside wall
    wall1, aabb1 = create_inside_wall(looper(igrid_x, igrid_y, igrid_z, (0,2), (1,2)), holedef=HoleDef(1250, "9*19"))
    wall2, aabb2 = create_inside_wall(looper(igrid_x, igrid_y, igrid_z, (3,3), (4,3)), holedef=HoleDef(1600, "9*19"))
    wall3, aabb3 = create_inside_wall(looper(igrid_x, igrid_y, igrid_z, (2,1), (2,0)), holedef=HoleDef(1100, "9*19"))
    wall4, aabb4 = create_inside_wall(looper(igrid_x, igrid_y, igrid_z, (2,4), (2,5)), holedef=HoleDef(1000, "9*19"))
    return [(wall1, aabb1), (wall2, aabb2), (wall3, aabb3), (wall4, aabb4)]

def create_inside_wall(wall_loop, holedef=None):
    transform, rotation = create_vertical_stdplane(wall_loop[:2])
    wall_local = transform.convertToLocal(wall_loop)
    #length = wall_local[1].x
    profile = "50*100"
    halfpro = 25
    # alajuoksu, ei se oikeesti nain mee mutta..
    lower = [wall_local[0].CopyLinear(0, halfpro, 0), wall_local[1].CopyLinear(0, halfpro, 0)]
    #upper = [wall_local[-1].CopyLinear(0, -halfpro, 0), wall_local[-2].CopyLinear(0, -halfpro, 0)]
    # studs
    for point in wall_local[:2]:
        # up by 50 mm
        point.Translate(0, halfpro*2, 0)
    #for point in wall_local[2:]:
    #    # down by 50 mm
    #    point.Translate(0, -halfpro*2, 0)
    on_face_point_pairs = create_hatch(wall_local, 600.0, halfpro, halfpro)
    # to some csys?
    stud_data = []
    for pp in [lower]:
        to_world = transform.convertToGlobal(pp)
        stud_data.append(create_wood_at(to_world[0], to_world[1], profile, Rotation.TOP))
    legal_face_point_pairs = []
    aabb = None
    if holedef is None:
        legal_face_point_pairs = on_face_point_pairs
    else:
        x0, y0, dx, dy = holedef.minmax_coords()
        low, high = holedef.minmax_points()
        ## aabb

        height = holedef.height()-halfpro*2
        left = Point3(low.x-halfpro, 2*halfpro, 0)
        right = Point3(high.x+halfpro, 2*halfpro, 0)
        stud_found = False
        for pp in on_face_point_pairs:
            #if pp[0].x < x0-halfpro and pp[0].distFrom(left) < 100:
            #    pp[0].x = left.x
            #    pp[1].x = left.x
            if pp[0].x > x0-3*halfpro and pp[0].x < x0+dx+3*halfpro:
                stud_found = True
            else:
                legal_face_point_pairs.append(pp)
        if stud_found:
            legal_face_point_pairs.append([left, left.CopyLinear(0,height,0)])
            legal_face_point_pairs.append([right, right.CopyLinear(0,height,0)])
            # upper wood
            over = [left.CopyLinear(-halfpro,height+halfpro,0), right.CopyLinear(halfpro,height+halfpro,0)]
            to_world = transform.convertToGlobal(over)
            stud_data.append(create_wood_at(to_world[0], to_world[1], profile, Rotation.TOP))

    for pp in legal_face_point_pairs:
        to_world = transform.convertToGlobal(pp)
        stud_data.append(create_wood_at(to_world[0], to_world[1], profile, rotation-1))
    # hatch..
    pps_local = create_hatch(wall_local, 100, first_offset=0, horizontal=True, holes=None)
    for pp in pps_local:
        # both sides
        l, r = pp[0], pp[1]
        board_strength = 22/2
        l1 = l.CopyLinear(0,0,50+board_strength)
        r1 = r.CopyLinear(0,0,50+board_strength)
        l2 = l.CopyLinear(0,0,-(50+board_strength))
        r2 = r.CopyLinear(0,0,-(50+board_strength))
        for p1,p2 in [(l1,r1),(l2,r2)]:
            to_world = transform.convertToGlobal([p1,p2])
            stud_data.append(create_wood_at(to_world[0], to_world[1], "22*100", Rotation.FRONT))
    # aabb's
    aabb = None
    if holedef is not None:
        low, high = holedef.minmax_points()
        to_world = transform.convertToGlobal([low, high])
        aabb = create_cut_aabb(to_world)

    return stud_data, aabb


from json import JSONEncoder
class MyEncoder(JSONEncoder):
    def default(self, o):
        return o.__dict__

if __name__ == "__main__":
    """
         This script generates parts for purulaatikko

         Usage:
         $ python geometry.py

         After completion, implement geometry generator in Tekla..

         ..to view what has changed.

         TODO list
         - lattiajuoksut
         - valipohjavasat
         - ullakko ristikko
         - (holpat)
         - loop-object with continues(), corners adjust
    """
    filename = sys.argv[1]
    specification = json.load(open(filename))

    roofangle = specification['roofangle']
    #porch_decline = porch_depth*math.tan(math.radians(roofangle))

    # todo: add centerline to master grid later..
    grid_z = specification['grid_z']
    trace("roof tip error: ~", int(round(abs(3800*math.tan(math.radians(roofangle))-grid_z[-1]))), "mm.")
    # harja
    #grid_z.append(grid_z[-1] + math.tan(math.radians(roofangle)))
    #centerline = [Point3(0, porch_depth + 7600.0 / 2, 0), Point3(sum(grid_x), porch_depth + 7600.0 / 2, 0)]

    #trace("CONVERTED:\n" + pprint.pformat(attr_dict))
    write_out(specification)

