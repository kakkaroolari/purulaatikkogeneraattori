# Don't know my licence. ask.
from __future__ import print_function
import sys
import pprint
from point import Point
import itertools #import izip
import re
import json


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

def write_out(grid_x, grid_y, sockleProfile, footingProfile):
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
    master_polygon = []
    xx = toDistances(grid_x)
    yy = toDistances(grid_y)
    for x_ind,y_ind in pairs:
        # zero level z
        edge = Point(xx[x_ind], yy[y_ind], 0.0)
        master_polygon.append(edge)
    
    trace("centroid is: ", centroid(master_polygon))
    #trace("sockle is: ", ', '.join([str(x) for x in polygon]))
    # TODO: make the layers bottom up and increase z offset
    z_offset = parse_height(footingProfile)
    footing = generate_footing(master_polygon, footingProfile)
    sockle = generate_sockle(master_polygon, sockleProfile, z_offset)
    lower_reach = generate_lower_reach(master_polygon, 1000.0)
    higher_reach = generate_lower_reach(master_polygon, 4750.0)
    wall_studs = generate_wall_studs(master_polygon, 1000.0, 3650)

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
            named_section("wall_studs", wall_studs)
        ], jsonfile, cls=MyEncoder)
        #jsonfile.write(pprint.pformat(combined_data))

def named_section(name, data):
    # todo: can add assembly meta, classes etc.
    return { "section": name, "data": data }

def generate_lower_reach(polygon, z_offset):
    return generate_offsetted_beams(polygon, "100*100", z_offset, "Timber_Undefined")

def create_wood_at(point, height, profile):
    low_point = point.Clone()
    high_point = low_point.Clone()
    high_point.Translate(0,0,height)
    return {
        "profile": profile,
        "points": [low_point, high_point],
        "material": "Timber_Undefined"
    }

def generate_wall_studs(polygon, z_offset, height):
    centerlines = generate_offsetted_lines(polygon, "100*100", 1100.0)
    # run points around each lower wood k600
    studpoints = []
    for start,end in centerlines:
        # do one wall line
        direction = start.GetVectorTo(end)
        length = start.distFrom(end)
        count = int((length-200.0)/600.0)
        # corner woods
        studpoints.append(create_wood_at(start, height, "100*100"))
        #studpoints.append(create_wood_at(end, height, "100*100"))
        # normal 4x2's
		#pitk‰sein‰ middle.top.left.. eh ts paskaa
		#p‰‰tysein‰ Ver.Rot.Hor=down,back, middle
        current = start.Clone()
        towards = Point.Normalize(direction, 50)
        current.Translate(towards)
        towards = Point.Normalize(direction, 600)
        #trace("start: {0}, end:{1}, direction: {2}".format(start, end, direction))
        for i in range(count):
            #trace("counting: ", i)
            current.Translate(towards)
            # todo: orientation(?)
            studpoints.append(create_wood_at(current, height, "50*100"))
    return studpoints

def generate_sockle(foundationPolygon, profile, z_offset):
    sockleCenter = []
    for node in foundationPolygon:
        # kinda cloning
        clonepoint = node.Clone()
        clonepoint.Translate(0, 0, z_offset)
        sockleCenter.append(clonepoint)
    # todo: closedloop or not..
    return [{
        "profile": profile,
        "points": sockleCenter,
        "material": "Concrete_Undefined"
    }]

def generate_footing(foundationPolygon, profile):
    return generate_offsetted_beams(foundationPolygon, profile, 0, "Concrete_Undefined")
    
def generate_offsetted_beams(foundationPolygon, profile, z_offset, material):
    centerlines = generate_offsetted_lines(foundationPolygon, profile, z_offset)
    beams = []
    for aa,bb in centerlines:
        beams.append({
            "profile": profile,
            "points": [aa, bb],
            "material": material
        })
    return beams
    
def generate_offsetted_lines(foundationPolygon, profile, z_offset):
    mass_center = centroid(foundationPolygon)
    footingCenter = []
    h_offset = parse_width(profile)/2
    for node in foundationPolygon:
        # todo: parse from profile
        endpoint = node.moveCloserTo(mass_center, h_offset)
        endpoint.Translate(0, 0, z_offset)
        footingCenter.append(endpoint)
    footingLines = pairwise(footingCenter)
    footings = []
    for start,end in footingLines:
        vector = start.GetVectorTo(end)
        #trace(start, )
        corners = Point.Normalize(vector, h_offset)
        #trace("start: {0}, end:{1}, direction: {2} translate vector: {3}".format(start, end, vector, corners,))
        #start.Translate(corners)
        #end.Translate(corners)
        aa = start.Clone()
        bb = end.Clone()
        aa.Translate(corners)
        bb.Translate(corners)
        footings.append((aa,bb,))
        #footings.append({
        #    "profile": profile,
        #    "points": [aa, bb],
        #    "material": material
        #})
    return footings

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
    sockle = "800*200"
    footing = "200*500"

    #trace("CONVERTED:\n" + pprint.pformat(attr_dict))
    write_out(grid_x, grid_y, sockle, footing)