# Don't know my licence. ask.
from __future__ import print_function
import sys
import pprint
from point import Point
import itertools #import izip
import re
import json
from constantdict import ConstantDict
import math

class Rotation(ConstantDict):
    """Tekla Position.Rotation"""
    FRONT = 0
    TOP = 1
    BACK = 2
    BELOW = 3

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = itertools.tee(iterable)
    next(b, None)
    return zip(a, b)

def centroid(points):
    x = [p.x for p in points]
    y = [p.y for p in points]
    z = [p.z for p in points]
    centroid = Point(sum(x) / len(points), sum(y) / len(points), sum(z) / len(points))
    return centroid

def toDistances(distanceList):
    sum = 0.0
    absolutes = []
    for dd in distanceList:
        absolutes.append(dd+sum)
        sum += dd
    return absolutes

def parse_profile(profile):
    p = re.compile('(\d+)\*(\d+)')
    m = p.match(profile)
    return m

def parse_height(profile):
    m = parse_profile(profile)
    height = m.group(1)
    trace("profile height: " + height)
    return float(height)

def parse_width(profile):
    m = parse_profile(profile)
    width = m.group(2)
    trace("profile width: " + width)
    return float(width)

def generate_loop(grid_x, grid_y, pairs):
    master_polygon = []
    xx = toDistances(grid_x)
    yy = toDistances(grid_y)
    for x_ind,y_ind in pairs:
        # zero level z
        edge = Point(xx[x_ind], yy[y_ind], 0.0)
        master_polygon.append(edge)
    return master_polygon

def write_out(grid_x, grid_y, sockleProfile, footingProfile, centerline, roof_angle):
    # define line, or grid intersect
    pairs = [
        (0,1),
        (1,1),
        (1,0),
        (2,0),
        (2,1),
        (3,1),
        (3,2),
        (0,2),
        (0,1)
    ]
    master_polygon = generate_loop(grid_x, grid_y, pairs)

    roof_pairs = [
        (0,1),
        (3,1),
        (3,2),
        (1,2),
        (0,1)
    ]
    roof_polygon = generate_loop(grid_x, grid_y, roof_pairs)

    trace("centroid is: ", centroid(master_polygon))
    #trace("sockle is: ", ', '.join([str(x) for x in polygon]))
    # TODO: make the layers bottom up and increase z offset
    z_offset = parse_height(footingProfile)
	#xy_offset = parse_width(footingProfile)
    footing = generate_footing(master_polygon, footingProfile, sockleProfile)
	# todo: use previous profile for xy-plane offset
    sockle = generate_sockle(master_polygon, sockleProfile, z_offset)
    lower_reach = generate_lower_reach(master_polygon, 1000.0)
    higher_reach = generate_lower_reach(master_polygon, 4750.0)
    wall_studs = generate_wall_studs(master_polygon, 1000.0, 3650)
    # bit different
    roof_woods = generate_roof_studs(roof_polygon, 4750.0, centerline, roof_angle)

    #trace("high: " + pprint.pformat(higher_reach))
    #trace("studs: " + pprint.pformat(wall_studs))
    #trace("low: " + pprint.pformat(lower_reach))
    trace("sockle is: " + pprint.pformat(sockle))
    trace("footing is: " + pprint.pformat(footing))

    combined_data = footing + sockle + lower_reach + wall_studs + higher_reach
    
    with open('data.json', 'w') as jsonfile:
        json.dump([
            named_section("footing", footing),
            named_section("sockle", sockle),
            named_section("lower_reach", lower_reach),
            named_section("higher_reach", higher_reach),
            named_section("wall_studs", wall_studs),
            named_section("roof_woods", roof_woods)
        ], jsonfile, cls=MyEncoder)
        #jsonfile.write(pprint.pformat(combined_data))

def named_section(name, data):
    # todo: can add assembly meta, classes etc.
    return { "section": name, "data": data }

def generate_lower_reach(polygon, z_offset):
    return generate_offsetted_beams(polygon, "100*100", 50.0, z_offset+50.0, "Timber_Undefined")

def create_wood_at(point, height, profile, rotation=None):
    low_point = point.Clone()
    high_point = low_point.Clone()
    high_point.Translate(height)
    return {
        "profile": profile,
        "rotation": rotation,
        "points": [low_point, high_point],
        "material": "Timber_Undefined"
    }

def generate_roof_studs(master_polygon, z_offset, centerline, roof_angle):
    overscan = 600.0 # negative to expand
    roof_polygon = extend_or_subtract(master_polygon, -overscan, z_offset)
    # hardcoded as rectangle
    begin = roof_polygon[0]
    end = roof_polygon[1]
    direction = begin.GetVectorTo(end)
    length = begin.distFrom(end)
    holppa = overscan+125.0
    count = int((length-2*holppa)/900.0)
    half_width = 3600.0 #roof_polygon[-2].distFrom(roof_polygon[-1])
    roofelevation = half_width*math.cos(math.radians(roof_angle))
    trace("halflife: ", half_width, " dist: ", length)
    # todo: much same as wall panel framing
    #tuned_start = begin.clone()
    # roof truss 5x2's
    current = begin.Clone()
    towards = Point.Normalize(direction, holppa)
    current.Translate(towards)
    roofpoints = []
    rotation = Rotation.FRONT
    roofpoints.append(create_wood_at(current, Point(0,half_width,roofelevation), "50*125", rotation))
    towards = Point.Normalize(direction, 900.0)
    #trace("start: {0}, end:{1}, direction: {2}".format(start, end, direction))
    for i in range(count):
        #trace("counting: ", i)
        current.Translate(towards)
        roofpoints.append(create_wood_at(current, Point(0,half_width,roofelevation), "50*125", rotation))
        #another = current.Clone()
        #another.x = end.x
        #roofpoints.append(create_wood_at(another, Point(0,half_width,roofelevation), "50*125", rotation))
    return roofpoints

def generate_wall_studs(polygon, z_offset, height):
    # todo: purulaatikko constant
    xy_offset = 50.0
    centerlines = generate_offsetted_lines(polygon, xy_offset, 1100.0)
    # run points around each lower wood k600
    studpoints = []
    for start,end in centerlines:
        # do one wall line
        direction = start.GetVectorTo(end)
        rotation = direction_to_rotation(direction)
        trace("beam rot type: ", type(rotation))
        #beamcenter = direction.Clone()
        length = start.distFrom(end)
        count = int((length-200.0)/600.0)
        # corner woods
        tuned_start = start.Clone()
        towards = Point.Normalize(direction, -50)
        tuned_start.Translate(towards)
        studpoints.append(create_wood_at(tuned_start, Point(0,0,height), "100*100", rotation))
        #studpoints.append(create_wood_at(end, height, "100*100"))
        # normal 4x2's
        current = start.Clone()
        towards = Point.Normalize(direction, -50)
        current.Translate(towards)
        towards = Point.Normalize(direction, 600)
        #trace("start: {0}, end:{1}, direction: {2}".format(start, end, direction))
        for i in range(count):
            #trace("counting: ", i)
            current.Translate(towards)
            studpoints.append(create_wood_at(current, Point(0,0,height), "50*100", rotation))
    return studpoints

def point_grid(startpoint, direction, count, first_offset, create_first):
    # UH, frakkit. needs running two points along...not height to reuse
    # todo: refactor
    grid = []
    tuned_start = start.Clone()
    towards = Point.Normalize(direction, -50)
    tuned_start.Translate(towards)
    #### studpoints.append(create_wood_at(tuned_start, height, "100*100", rotation))
    if create_first is not None:
        grid.append
    #studpoints.append(create_wood_at(end, height, "100*100"))
    # normal 4x2's
    current = start.Clone()
    towards = Point.Normalize(direction, -50)
    current.Translate(towards)
    towards = Point.Normalize(direction, 600)
    #trace("start: {0}, end:{1}, direction: {2}".format(start, end, direction))
    for i in range(count):
        #trace("counting: ", i)
        current.Translate(towards)
        grid.append(current.Clone())
    return grid

    
def direction_to_rotation(direction):
    if abs(direction.y) > abs(direction.x):
        if direction.y > 0:
            return Rotation.FRONT
        return Rotation.BACK
    if direction.x > 0:
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
    return [{
        "profile": sockleProfile,
        "rotation": None,
        "points": sockleCenter,
        "material": "Concrete_Undefined"
    }]

def generate_footing(foundationPolygon, footingProfile, sockleProfile):
	# footing is not centerline, but polybeam concrete panel is outer limits

    # move sockle to footing center, sockle polygon is not centerline but
	# outer limits to get the polybeam fully casted in closed loop corner.
    #footingWidth = parse_width(footingProfile)
    sockleWidth = parse_width(sockleProfile)
    xy_offset = sockleWidth/2
    footingCenterZ = parse_height(footingProfile)/2
    #hack_profile = xy_offset + "*"
    #centerlines = generate_offsetted_lines(foundationPolygon, xy_offset, footingCenterZ)
    #beams = []
    #for aa,bb in centerlines:
    #    beams.append({
    #        "profile": footingProfile,
    #        "points": [aa, bb],
    #        "material": "Concrete_Undefined"
    #    })
    #return beams
    return generate_offsetted_beams(foundationPolygon, footingProfile, xy_offset, footingCenterZ, "Concrete_Undefined")
    
def generate_offsetted_beams(foundationPolygon, profile, xy_offset, z_offset, material):
    #xy_offset = parse_width(profile)/2
    centerlines = generate_offsetted_lines(foundationPolygon, xy_offset, z_offset, profile)
    beams = []
    for aa,bb in centerlines:
        beams.append({
            "profile": profile,
            "rotation": None,
            "points": [aa, bb],
            "material": material
        })
    return beams
    
def extend_or_subtract(polygon, xy_offset, z_offset):
    mass_center = centroid(polygon)
    footingCenter = []
	#if instanceof(profile, float):
	#	h_offset = profile
	#else
	#	h_offset = parse_width(profile)/2
    for node in polygon:
        # todo: parse from profile
        endpoint = node.moveCloserTo(mass_center, xy_offset)
        endpoint.Translate(0, 0, z_offset)
        footingCenter.append(endpoint)
    return footingCenter

def generate_offsetted_lines(master_polygon, xy_offset, z_offset, adjustByProfile=None):
    # move points i.e. 50mm closer to structure center (to 100*100 beam centerline)
    footingCenter = extend_or_subtract(master_polygon, xy_offset, z_offset)
    footingLines = pairwise(footingCenter)
    polygonMidpoints = []
    adjustEndPoints = xy_offset
    if adjustByProfile is not None:
        # footing pads have different widht than xy_offset
        adjustEndPoints = parse_width(adjustByProfile)/2
    for start,end in footingLines:
        vector = start.GetVectorTo(end)
        #trace(start, )
        corners = Point.Normalize(vector, adjustEndPoints)
        #trace("start: {0}, end:{1}, direction: {2} translate vector: {3}".format(start, end, vector, corners,))
        #start.Translate(corners)
        #end.Translate(corners)
        aa = start.Clone()
        bb = end.Clone()
        aa.Translate(corners)
        bb.Translate(corners)
        polygonMidpoints.append((aa,bb,))
        #footings.append({
        #    "profile": profile,
        #    "points": [aa, bb],
        #    "material": material
        #})
    return polygonMidpoints

def trace(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    
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
    """
    #zz = pairwise(["a","b","c","d","e"])
    #trace("pairwise: ", list(zz))
    
    grid_x = [0.00, 750.00, 3300.00, 5060.00]
    grid_y = [0.00, 1660.00, 7600.00]
    centerline = [Point(0, 1660.0+7600.0/2, 0), Point(sum(grid_x), 1660.0+7600.0/2, 0)]
    sockle = "800*200"
    footing = "200*500"

    #trace("CONVERTED:\n" + pprint.pformat(attr_dict))
    write_out(grid_x, grid_y, sockle, footing, centerline, 36.64)