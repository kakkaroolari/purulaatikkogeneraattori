# Don't know my licence. ask.
from __future__ import print_function
import sys
import pprint
from point import Point
import itertools #import izip
import re


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
    z_offset = parse_height(footingProfile)
    footing = generate_footing(master_polygon, footingProfile)
    sockle = generate_sockle(master_polygon, sockleProfile, z_offset)

    trace("sockle is: " + pprint.pformat(sockle))
    trace("footing is: " + pprint.pformat(footing))

def generate_sockle(foundationPolygon, profile, z_offset):
    sockleCenter = []
    for node in foundationPolygon:
        # kinda cloning
        clonepoint = node.Clone()
        clonepoint.Translate(0, 0, z_offset)
        sockleCenter.append(clonepoint)
    # todo: closedloop or not..
    return {
        "profile": profile,
        "points": sockleCenter,
        "material": "Concrete_Undefined"
    }
    
def generate_footing(foundationPolygon, profile):
    mass_center = centroid(foundationPolygon)
    footingCenter = []
    for node in foundationPolygon:
        # todo: parse from profile
        footingCenter.append(node.moveCloserTo(mass_center, 250.0))
    footingLines = pairwise(footingCenter)
    footings = []
    for start,end in footingLines:
        footings.append({
            "profile": profile,
            "points": [start, end],
            "material": "Concrete_Undefined"
        })
    return footings

def trace(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)
    

if __name__ == "__main__":
    """
         This script generates parts for purulaatikko

         Usage:
         $ python copysettings.py

         After completion, implement geometry generator in Tekla..

         ..to view what has changed.
    """
    
    grid_x = [0.00, 750.00, 3300.00, 5060.00]
    grid_y = [0.00, 1660.00, 7600.00]
    sockle = "800*200"
    footing = "200*500"

    #trace("CONVERTED:\n" + pprint.pformat(attr_dict))
    write_out(grid_x, grid_y, sockle, footing)