import math
import sys
from constantdict import ConstantDict

class Rotation(ConstantDict):
    """Tekla Position.Rotation"""
    FRONT = 0
    TOP = 1
    BACK = 2
    BELOW = 3

def get_ceiling(current, start, height, fullwidth, roofangle):
    if not roofangle:
        return height
    dist_to_start = current.distFrom(start)
    coeff = math.tan(math.radians(roofangle))
    inner_width = fullwidth - 100 # todo profile
    if dist_to_start < inner_width/2:
        elevation = dist_to_start * coeff
    else:
        elevation = (inner_width - dist_to_start) * coeff
    return height + elevation

def trace(*args, **kwargs):
    print(*args, file = sys.stderr, **kwargs)

def create_wood_at(point, point2, profile, rotation=None):
    low_point = point.Clone()
    high_point = point2.Clone()
    return get_part_data(profile, rotation, [low_point, high_point], "Timber_Undefined")

def get_part_data(profile, rotation, points, material, ts_class=None):
    return {
        "profile": profile,
        "rotation": rotation,
        "points": points,
        "material": material,
        "klass": ts_class
    }
