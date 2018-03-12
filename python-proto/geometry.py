# Don't know my licence.  ask.
from __future__ import print_function
import sys
import os
import pprint
from point import Point3
from stiffeners import Stiffener
from cladding import Cladding
from roofing import Roofing
from windowframer import WindowFramer, windowDef, HoleDef
import itertools #import izip
import json
import math
from helpers import *


cornerwoodcolor = 41
chimney_x = 3110
porch_depth = 3000
chimney_y = 3080 + porch_depth

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

def clad_def(polygon, windows, usefits=False):
    return {'poly': polygon, 'windows': windows, 'usefits': usefits}

def write_out(grid_x, grid_y, grid_z, sockleProfile, footingProfile, centerline, roof_angle):
    # define line, or grid intersect
    pairs = [(0,1),
        (3,1),
        (3,3),
        (0,3),
        (0,1)]
    master_polygon = generate_loop(grid_x, grid_y, None, pairs)
    #trace(pprint.pformat(master_polygon))

    # porch grid elevations (keep separate)
    porch_width = toDistances(grid_x)[2]
    #trace("pw: ", porch_width)
    porchroofangle = roofangle
    pelevs_z = [0.00, 1000.00, 3000, (porch_width/2)*math.tan(math.radians(porchroofangle))]
    pgrid_x = [0.00, porch_width/2, porch_width/2]
    pgrid_y = [0.00, porch_depth]
    porch = [(0,1),
        (0,0),
        (2,0),
        (2,1)]
    porch_polygon = generate_loop(pgrid_x, pgrid_y, None, porch)
    #get_plane_data

    high_pairs1 = [(0,1),
        (3,1)]
    high_pairs2 = [(0,3),
        (3,3)]
    high_polygon1 = generate_loop(grid_x, grid_y, None, high_pairs1)
    high_polygon2 = generate_loop(grid_x, grid_y, None, high_pairs2)

    # create window aabb's, possibly to be used all over the place
    level1 = 1160
    level2 = 4500 # random ass, todo: measure it
    attic_offset = grid_y[-1]-300 # 600mm/2
    line0 = generate_loop(grid_x, grid_y, grid_z, [(0,3,1), (0,1,1)])
    defs0 = [windowDef([attic_offset, 5000], "6*6", splitters=False)]
    line1 = generate_loop(grid_x, grid_y, grid_z, [(2,1,1), (3,1,1)])
    defs1 = [windowDef([1870, level1], "14*12")]
    line2 = generate_loop(grid_x, grid_y, grid_z, [(3,1,1), (3,3,1)])
    defs2 = [windowDef([2650, level1], "11*12"), windowDef([attic_offset, 5000], "6*6", splitters=False)]
    line3 = generate_loop(grid_x, grid_y, grid_z, [(3,3,1), (0,3,1)])
    defs3 = [windowDef([2100, level1], "14*12"), windowDef([6290, level1], "11*12")]
    window_cuts, window_woods = create_window_boxes([(line0, defs0),(line1, defs1),(line2, defs2),(line3, defs3)])
    trace("Holes for: ", len(window_cuts), " windows.", window_cuts)

    # chimney pipe
    section_cut = generate_loop(grid_x, grid_y, grid_z, [(0,1,0), (0,3,0), (0,3,4)])
    chimney_parts, pipe_cut = create_chimneypipe(section_cut, x=chimney_x, y=chimney_y, profile="620*900", roofangle=roof_angle)

    # todo: move somplace more appropriate?
    fieldsaw = Cladding("cladding")
    board_areas = {
        #"paaty_ala":    clad_def([(0,3,1),(0,1,1),(0,1,3),(0,3,3)],         defs0),
        #"paaty_kolmio": clad_def([(0,3,3),(0,1,3),(0,1,4),(0,2,5),(0,3,4)], None, usefits=True),
        #"vasemmalla":   clad_def([(0,1,1),(1,1,1),(1,1,4),(0,1,4)],         None),
        "oikealla":     clad_def([(2,1,1),(3,1,1),(3,1,4),(2,1,4)],         defs1),
        #"etela_ala":    clad_def([(3,1,1),(3,3,1),(3,3,3),(3,1,3)],         defs2),
        #"etela_yla":    clad_def([(3,1,3),(3,3,3),(3,3,4),(3,2,5),(3,1,4)], None, usefits=True),
        #"takaseina":    clad_def([(3,3,1),(0,3,1),(0,3,4),(3,3,4)],         defs3),
        #"kuisti_vas":   clad_def([(1,1,1),(1,0,1),(1,0,2),(1,1,4)],         None, usefits=True),
        #"kuisti_etu":   clad_def([(1,0,1),(2,0,1),(2,0,2),(1,0,2)],         None, usefits=True),
        #"kuisti_oik":   clad_def([(2,0,1),(2,1,1),(2,1,4),(2,0,2)],         None, usefits=True)
        }

    # corner boards
    corner_boards = create_corner_boards(grid_x, grid_y, grid_z, cornerwoodcolor)

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
    roof_woody = generate_main_roof(grid_x, grid_y, grid_z, pipe_cut)

    # porch
    porch_decline = porch_depth*math.tan(math.radians(roof_angle))
    footing += generate_footing(porch_polygon, footingProfile, sockleProfile)
    sockle += generate_sockle(porch_polygon, sockleProfile, z_offset)
    offset_porch_woods_outwards(porch_polygon, mass_center)
    lower_reach += generate_lower_reach(porch_polygon, toDistances(pelevs_z)[1])
    higher_reach += generate_lower_reach(porch_polygon, toDistances(pelevs_z)[2])
    wall_studs += generate_wall_studs(porch_polygon, toDistances(pelevs_z)[1], pelevs_z[2]-100)
    porch_roofer = create_porch_roof(pgrid_x, pgrid_y, pelevs_z, roof_woody)

    # inner walls
    inside_walls = create_inside()
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
    porch_stiffeners = stiffen_wall("porch", porch_polygon, 1000.0, 3850-porch_decline, roof_angle, mass_center)
    

    for stf in stiffeners + porch_stiffeners:
        cuts = stf.get_cut_planes()
        fits = stf.get_fit_planes()
        #combined_data.append(named_section(stf.name, stf.get_part_data(), planes=cuts, fits=fits, solids=window_cuts))

    # cladding boards
    for key, value in board_areas.items():
        segment_name = "cladding_" + key
        trace("Creating cladding for: ", segment_name)
        segment_polygon = value['poly']
        segment_windows = value['windows']
        segment_isfitted = value['usefits']
        cladding_loop = generate_loop(grid_x, grid_y, grid_z, segment_polygon)
        wall_parts, fittings = fieldsaw.create_cladding(cladding_loop, "22*125", 33, segment_windows, fittings=segment_isfitted)
        combined_data.append(named_section(segment_name, wall_parts, 44, solids=window_cuts, planes=fittings, fits=fittings))

    #trace("roof_woody: ", roof_woody.get_roofs_faces(), porch_roofer.get_roofs_faces())
    for roof_face in roof_woody.get_roofs_faces() + porch_roofer.get_roofs_faces():
        trace("add roof: ", roof_face.get_name())
        # woods
        part_data, coord_sys, cut_aabbs, fit_planes = roof_face.get_woods_data()
        name = roof_face.get_name()
        combined_data.append(named_section("roof_woods_"+name, part_data, ts_class=12, csys=coord_sys, solids=cut_aabbs, fits=fit_planes))
        # steels
        geom_data, coord_sys, cut_aabbs, cut_planes = roof_face.get_steel_data()
        combined_data.append(named_section("roof_steels_"+name, geom_data, ts_class=3, csys=coord_sys, solids=cut_aabbs, planes=cut_planes))
        # side steels
        sides_data, coord_sys, fit_planes = roof_face.get_sides_data()
        combined_data.append(named_section("roof_sides_"+name, sides_data, ts_class=3, csys=coord_sys, fits=fit_planes))

    with open('data.json', 'w') as jsonfile:
        json.dump(combined_data, jsonfile, cls=MyEncoder, indent=2)
        #jsonfile.write(pprint.pformat(combined_data))
    print("wrote:\n\b", os.getcwd() + os.path.sep + "data.json")

def named_section(name, part_list, ts_class=None, planes=None, csys=None, solids=None, fits=None):
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
        "fitplanes": remove_none_elements_from_list(fits)
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

#def _create_window_hole(distance_x, distance_y, 
def create_corner_boards(grid_x, grid_y, grid_z, cornerwoodcolor, z_level=44):
    corners = [
        generate_loop(grid_x, grid_y, grid_z, [(0,1,1), (0,1,3), (1,1,1)]),
        generate_loop(grid_x, grid_y, grid_z, [(3,1,1), (3,1,3), (3,2,1)]),
        generate_loop(grid_x, grid_y, grid_z, [(3,3,1), (3,3,3), (2,3,1)]),
        generate_loop(grid_x, grid_y, grid_z, [(0,3,1), (0,3,3), (0,2,1)])
    ]
    corner_woods = []
    for corner_tri in corners:
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

def generate_main_roof(grid_x, grid_y, grid_z, chimney_pipe):
    # xy plane
    roof_tuples_1 = [(0,2,4), # with porch roof extension
        (0,1,4),
        #(1,1,4),
        #(1,0,4),
        #(2,0,4),
        #(2,1,4),
        (3,1,4),
        (3,2,4)]
    roof_polygon_1 = generate_loop(grid_x, grid_y, grid_z, roof_tuples_1)
    #trace("roof poly 1: ", roof_polygon_1)
    roof_tuples_2 = [(3,2,4),
        (3,3,4),
        (0,3,4),
        (0,2,4)]
    roof_polygon_2 = generate_loop(grid_x, grid_y, grid_z, roof_tuples_2)
    # centerline at highest elevation
    centerline = generate_loop(grid_x, grid_y, grid_z, [(0,2,5),(3,2,5)])
    #trace("roof centerline: ", centerline)
    roofer = Roofing("roof_studs", chimney_pipe)
    roofer.do_one_roof_face("lape_1", roof_polygon_1, centerline[0])
    #roofer.do_one_roof_face("lape_2", roof_polygon_2, centerline[1])
    # todo: hack, return face1 plane outside

    return roofer

def create_porch_roof(pgrid_x, pgrid_y, pgrid_z, main_roofer):
    # isect porch roof to main roof: p0, p1, origo, normal
    centerline = generate_loop(pgrid_x, pgrid_y, pgrid_z, [(1,1,-1),(1,0,-1)])
    pco, pno = main_roofer.roof_decs[0].get_plane_data()
    p1 = centerline[0].ToArr()
    p2 = centerline[1].ToArr()
    #trace("wtf: ", p1,p2,pco,pno)
    rooftip = None #isect_line_plane_v3(p1,p2,pco,pno)
    if rooftip is not None:
        maxy = toDistances(pgrid_y)[-1]
        max2y = rooftip[1]
        trace("pw22: ", maxy, "rt: ", rooftip)
        ylastdist = max2y - maxy, 
        pgrid_y.append(ylastdist)

    # xy plane
    roof_tuples_1 = [(1,-1,-2),
        (0,-1,-2),
        (0,0,-2),
        (1,0,-2)]
    #trace("pw3: ", pgrid_x, pgrid_y, pgrid_z)
    roof_polygon_1 = generate_loop(pgrid_x, pgrid_y, pgrid_z, roof_tuples_1)
    roofer = Roofing("porch_rafters", None)
    roofer.do_one_roof_face("porch_lape_1", roof_polygon_1, centerline[0])
    #roofer.do_one_roof_face("lape_2", roof_polygon_2, centerline[1])
    # todo: hack, return face1 plane outside

    return roofer


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

def create_inside():
    # create grids
    boards = 22 #+ 13
    outer_wall = 100 + boards
    inside_wall = 170 #100 + 2*boards
    porch_off = porch_depth + outer_wall
    igrid_x = [outer_wall, chimney_x - outer_wall, 620-inside_wall/2, inside_wall/2, 5280-boards]
    igrid_y = [porch_off, (chimney_y-porch_off), inside_wall/2, 900-inside_wall, inside_wall/2, 3220-boards]
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
         - ulkovuorilaud. + rimat + nurkka + vesip.
         - (holpat)
         - loop-object with continues(), corners adjust
         - attic windows
         - roof border woods
    """
    #zz = pairwise(["a","b","c","d","e"])
    #trace("pairwise: ", list(zz))
    roofangle = 36.64
    porch_decline = porch_depth*math.tan(math.radians(roofangle))
    
    # todo: add centerline to master grid later..
    grid_x = [0.00, 750.00, 3300.00, 5060.00]
    grid_y = [0.00, porch_depth, 3800.00, 3800.00]
    #grid_z = [0.00, 1000.00, 3700.00-porch_decline, porch_decline, 150.00, 3800*math.tan(math.radians(roofangle))]
    grid_z = [0.00, 1000.00, 3850.00-porch_decline, porch_decline-150, 150, 3800*math.tan(math.radians(roofangle))]
    # harja
    #grid_z.append(grid_z[-1] + math.tan(math.radians(roofangle)))
    centerline = [Point3(0, porch_depth + 7600.0 / 2, 0), Point3(sum(grid_x), porch_depth + 7600.0 / 2, 0)]
    sockle = "800*200"
    footing = "200*500"

    #trace("CONVERTED:\n" + pprint.pformat(attr_dict))
    write_out(grid_x, grid_y, grid_z, sockle, footing, centerline, roofangle)

