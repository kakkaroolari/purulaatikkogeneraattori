# Don't know my licence.  ask.
from __future__ import print_function
import sys
import os
import pprint
from point import Point3
from stiffeners import Stiffener
from cladding import Cladding
import itertools #import izip
import re
import json
import math
from helpers import *

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

def parse_profile(profile):
    p = re.compile('(\d+)\*(\d+)')
    m = p.match(profile)
    return m

def parse_height(profile):
    m = parse_profile(profile)
    height = m.group(1)
    #trace("profile height: " + height)
    return float(height)

def parse_width(profile):
    m = parse_profile(profile)
    width = m.group(2)
    #trace("profile width: " + width)
    return float(width)

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

def write_out(grid_x, grid_y, grid_z, sockleProfile, footingProfile, centerline, roof_angle):
    # define line, or grid intersect
    pairs = [(0,1),
        #(1,1),
        #(1,0),
        #(2,0),
        #(2,1),
        (3,1),
        (3,3),
        (0,3),
        (0,1)]
    master_polygon = generate_loop(grid_x, grid_y, None, pairs)
    #trace(pprint.pformat(master_polygon))

    porch = [(1,1),
        (1,0),
        (2,0),
        (2,1)]
    porch_polygon = generate_loop(grid_x, grid_y, None, porch)

    roof_pairs = [(0,1),
        (3,1),
        (3,3),
        (0,3),
        (0,1)]
    roof_polygon = generate_loop(grid_x, grid_y, None, roof_pairs)

    high_pairs1 = [(0,1),
        (3,1)]
    high_pairs2 = [(0,3),
        (3,3)]
    high_polygon1 = generate_loop(grid_x, grid_y, None, high_pairs1)
    high_polygon2 = generate_loop(grid_x, grid_y, None, high_pairs2)

    # todo: move somplace more appropriate?
    fieldsaw = Cladding("cladding")
    cladding_loop = generate_loop(grid_x, grid_y, grid_z, [(0,3,1),(0,1,1),(0,1,2),(0,3,2)])
    fieldsaw.create_cladding(cladding_loop, "22*125", 33) # ( 22 + 22/2 ) mm
    # top triangle
    cladding_loop = generate_loop(grid_x, grid_y, grid_z, [(0,3,2),(0,1,2),(0,1,3),(0,2,4),(0,3,3)])
    fieldsaw.create_cladding(cladding_loop, "22*125", 33)

    cladding_test = fieldsaw.get_part_data()
    # Used for testing stiffeners
    #stiff_pairs = [(0,1),(3,1)]
    #stiff_poly = generate_loop(grid_x, grid_y, stiff_pairs)

    mass_center = centroid(master_polygon)
    #trace("centroid is: ", mass_center)
    #trace("sockle is: ", ', '.join([str(x) for x in polygon]))
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

    # porch
    footing += generate_footing(porch_polygon, footingProfile, sockleProfile)
    sockle += generate_sockle(porch_polygon, sockleProfile, z_offset)
    offset_porch_woods_outwards(porch_polygon, mass_center)
    lower_reach += generate_lower_reach(porch_polygon, 1000.0)
    higher_reach += generate_lower_reach(porch_polygon, 3750.0)
    wall_studs += generate_wall_studs(porch_polygon, 1000.0, 2650)


    # bit different
    roof_woods = generate_roof_studs(roof_polygon, 4900.0, centerline, roof_angle)

    #trace("high: " + pprint.pformat(higher_reach))
    #trace("studs: " + pprint.pformat(wall_studs))
    #trace("low: " + pprint.pformat(lower_reach))
    #trace("sockle is: " + pprint.pformat(sockle))
    #trace("footing is: " + pprint.pformat(footing))

    # first 3d loop experiment


    #combined_data = footing + sockle + lower_reach + wall_studs + higher_reach
    
    combined_data = [named_section("footing", footing),
            named_section("sockle", sockle),
            named_section("lower_reach", lower_reach, 4),
            named_section("higher_reach", higher_reach, 3),
            named_section("wall_studs", wall_studs, 3),
            named_section("cladding_test", cladding_test), # todo: oikeasti class niinku stiffeners
            named_section("roof_woods", roof_woods, 12)]

    # stiffener experiment
    stiffeners = stiffen_wall("mainwall", master_polygon, 1000.0, 3850, roof_angle, mass_center)
    porch_stiffeners = stiffen_wall("porch", porch_polygon, 1000.0, 2850, roof_angle, mass_center)
    

    for stf in stiffeners + porch_stiffeners:
        combined_data.append(named_section(stf.name, stf.get_part_data()))

    with open('data.json', 'w') as jsonfile:
        json.dump(combined_data, jsonfile, cls=MyEncoder, indent=2)
        #jsonfile.write(pprint.pformat(combined_data))
    print("wrote:\n\b", os.getcwd() + os.path.sep + "data.json")

def named_section(name, part_list, ts_class=None, planes=None):
    # todo: can add assembly meta, classes etc.
    if ts_class is not None:
        for part in part_list:
            part["klass"] = ts_class
    return { "section": name, "parts": part_list, "planes": planes }

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

def generate_roof_studs(roof_polygon, z_offset, centerline, roof_angle):
    #overscan = 600.0 # negative to expand
    #roof_polygon = extend_or_subtract(master_polygon, -overscan, z_offset)
    # hardcoded as rectangle
    begin = roof_polygon[0].Clone()
    end = roof_polygon[1].Clone()
    begin.Translate(0, 0, z_offset)
    end.Translate(0, 0, z_offset)
    mainwall = begin.GetVectorTo(end)
    mainwall_length = begin.distFrom(end)
    holppa = 125.0
    last = (mainwall_length - 2 * holppa) % 900.0
    count = int((mainwall_length - 2 * holppa) / 900.0)
    othercorner = roof_polygon[-2].Clone()
    othercorner.Translate(0, 0, z_offset)
    #trace("begin: ", begin, " other: ", othercorner)
    sidewall = begin.distFrom(othercorner)
    # ylajuoksun linja shiftataan harjakorkeutaan
    half_width = sidewall / 2
    roofelevation = half_width * math.tan(math.radians(roof_angle))
    # ylatukipuun linja siftataan raystaslinjaksi
    halflife2 = 600.0
    roofdeclination = -halflife2 * math.tan(math.radians(roof_angle))
    #trace("halflife: ", half_width, " dist: ", mainwall_length, " elev: ", roofelevation)
    # todo: much same as wall panel framing
    lowside = create_one_side_trusses(begin, mainwall, mainwall_length, count, last, holppa, half_width, roofelevation, -halflife2, roofdeclination)
    highside = create_one_side_trusses(othercorner, mainwall, mainwall_length, count, last, holppa, -half_width, roofelevation, halflife2, roofdeclination)
    return lowside + highside

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

    
def direction_to_rotation(direction, invert=False):
    (x, y) = (direction.x, direction.y)
    if invert:
        temp = x
        x = y
        y = temp
    if abs(y) > abs(x):
        if y > 0:
            return Rotation.FRONT
        return Rotation.BACK
    if x > 0:
        return Rotation.TOP
    return Rotation.BELOW

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
         - kattolappeet per puoli -> porch business
         - elevation grid, and roof centerline definitions
         - ulkovuorilaud. + rimat + nurkka + vesip.
         - kattoruoteet + pellit + (holpat)
         - loop-object with continues(), corners adjust
         - python 2d shapely grid for cladding
           (https://gis.stackexchange.com/questions/91362/looking-for-a-simple-hatching-algorithm)
         - 
    """
    #zz = pairwise(["a","b","c","d","e"])
    #trace("pairwise: ", list(zz))
    roofangle = 36.64
    
    # todo: add centerline to master grid later..
    grid_x = [0.00, 750.00, 3300.00, 5060.00]
    grid_y = [0.00, 1660.00, 3800.00, 3800.00]
    grid_z = [0.00, 1000.00, 3700.00, 150.00, 3800*math.tan(math.radians(roofangle))]
    # harja
    #grid_z.append(grid_z[-1] + math.tan(math.radians(roofangle)))
    centerline = [Point3(0, 1660.0 + 7600.0 / 2, 0), Point3(sum(grid_x), 1660.0 + 7600.0 / 2, 0)]
    sockle = "800*200"
    footing = "200*500"

    #trace("CONVERTED:\n" + pprint.pformat(attr_dict))
    write_out(grid_x, grid_y, grid_z, sockle, footing, centerline, roofangle)

