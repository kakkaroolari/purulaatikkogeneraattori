import math
import sys
#from numpy import *
import numpy as np
from numbers import Number

# https://stackoverflow.com/questions/3252194/numpy-and-line-intersections
#
# line segment intersection using vectors
# see Computer Graphics by F.S. Hill
#
def perp( a ) :
    b = empty_like(a)
    b[0] = -a[1]
    b[1] = a[0]
    return b

# line segment a given by endpoints a1, a2
# line segment b given by endpoints b1, b2
# return 
def seg_intersect(a1,a2, b1,b2) :
    da = a2-a1
    db = b2-b1
    dp = a1-b1
    dap = perp(da)
    denom = dot( dap, db)
    num = dot( dap, dp )
    return (num / denom.astype(float))*db + b1


# no deps....



# ----------------------
# generic math functions

def add_v3v3(v0, v1):
    return (
        v0[0] + v1[0],
        v0[1] + v1[1],
        v0[2] + v1[2],
        )


def sub_v3v3(v0, v1):
    return (
        v0[0] - v1[0],
        v0[1] - v1[1],
        v0[2] - v1[2],
        )


def dot_v3v3(v0, v1):
    return (
        (v0[0] * v1[0]) +
        (v0[1] * v1[1]) +
        (v0[2] * v1[2])
        )


def len_squared_v3(v0):
    return dot_v3v3(v0, v0)


def mul_v3_fl(v0, f):
    return (
        v0[0] * f,
        v0[1] * f,
        v0[2] * f,
        )

# no depss... end...
class Point3( object ):
    def __init__( self, x, y, z ):
        for i in [x, y, z]:
            if not isinstance(i, Number):
                raise ValueError("{} is not a number.".format(i))
        self.x, self.y, self.z = x, y, z
    def distFrom( self, x, y=None, z=None ):
        if isinstance(x, Point3):
            (x,y,z) = (x.x, x.y, x.z)
        return math.sqrt( (self.x-x)**2 + (self.y-y)**2 + (self.z-z)**2 )
    
    def magnitude(v):
        return math.sqrt(v.x*v.x + v.y*v.y + v.z*v.z)

    def Compare(self, other):
        return (abs(self.x - other.x) < 0.5 and
                abs(self.y - other.y) < 0.5 and
                abs(self.z - other.z) < 0.5 )

    def Add(self, x, y=None, z=None):
        if isinstance(x, Point3):
            (x,y,z) = (x.x, x.y, x.z)
        return Point3(self.x + x, self.y + y, self.z + z)

    def moveCloserTo(self, point, amount):
        new_x = self.x
        new_y = self.y
        new_z = self.z
        
        if ( point.x - self.x > 0):
            new_x += amount
        else:
            new_x -= amount
        if ( point.y - self.y > 0):
            new_y += amount
        else:
            new_y -= amount
        return Point3(new_x, new_y, new_z)
    
    def Translate(self, x, y=None, z=None):
        if isinstance(x, Point3):
            (x,y,z) = (x.x, x.y, x.z)
        self.x += x
        self.y += y
        self.z += z

    # helper
    def CopyLinear(self, x, y=None, z=None):
        if isinstance(x, Point3):
            (x,y,z) = (x.x, x.y, x.z)
        copy = self.Clone()
        copy.Translate(x, y, z)
        return copy

    def Clone(self):
        return self.moveCloserTo(Point3(0.00,0.00,0.00), 0.0)
    
    def GetVectorTo(self, point):
        copy = self.Clone()
        copy.x = point.x - copy.x
        copy.y = point.y - copy.y
        copy.z = point.z - copy.z
        return copy

    def Normalize(vector, lenght=1):
        vmag = Point3.magnitude(vector)
        normalized = Point3(vector.x/vmag, vector.y/vmag, vector.z/vmag)
        normalized.x *= lenght
        normalized.y *= lenght
        normalized.z *= lenght
        return normalized

    def Reversed(vector):
        return Point3(-vector.x, -vector.y, -vector.z)

    def Midpoint(p1, p2):
        return Point3((p1.x+p2.x)/2, (p1.y+p2.y)/2, (p1.z+p2.z)/2)

    # rainy day module..
    def Cross(a, b):
        c = Point3(a.y*b.z - a.z*b.y,
             a.z*b.x - a.x*b.z,
             a.x*b.y - a.y*b.x)
        return c

    def Dot(v1, v2):
        vector1 = (v1.x,v1.y,v1.z)
        vector2 = (v2.x,v2.y,v2.z)
        return sum(p*q for p,q in zip(vector1, vector2))

    def ccw(A,B,C):
        return (C.y-A.y)*(B.x-A.x) > (B.y-A.y)*(C.x-A.x)

    def intersect(A,B,C,D):
        return ccw(A,C,D) != ccw(B,C,D) and ccw(A,B,C) != ccw(A,B,D)


    # ---------------------- numpy wrap ----------------------
    def seg_isect_wrap(a, b, n, m):
        isect = seg_intersect(a.ToArr(), b.ToArr(), n.ToArr(), m.ToArr())
        #print("np.arr:", isect)
        return Point3(isect[0], isect[1], isect[2])

    def ToList(self):
        return [self.x, self.y, self.z]

    def ToArr(self):
        return np.array([self.x, self.y, self.z])

    def IsValid(self):
        return isinstance(self.x, float) and isinstance(self.y, float) and isinstance(self.z, float)

    #def __add__(self, y):
    #    return self.Add(y)

    #def __sub__(self, y):
    #    return self.Add(y)

    # https://stackoverflow.com/questions/4543506/algorithm-for-intersection-of-2-lines
    def LineSegmentIntersect(line1V1, line1V2, line2V1, line2V2):
        # Line1
        A1 = line1V2.y - line1V1.y
        B1 = line1V2.x - line1V1.x
        C1 = A1*line1V1.y + B1*line1V1.y

        # Line2
        A2 = line2V2.y - line2V1.y
        B2 = line2V2.x - line2V1.x
        C2 = A2 * line2V1.x + B2 * line2V1.y

        det = A1*B2 - A2*B1
        if abs(det) < sys.float_info.epsilon:
            return None # parallel lines
        else:
            x = (B2*C1 - B1*C2)/det;
            y = (A1 * C2 - A2 * C1) / det;
            return Point3(x,y,0)

    #def default(self, obj):
    #    return {"point" : {"x":obj.x,"y":obj.y,"z":obj.z}}
    def __str__(self):
        return "Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
    def __unicode__(self):
        return u"Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
    def __repr__(self):
        return "Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
        #return {"point" : {"x":self.x,"y":self.y,"z":self.z}}

    # yet another intersect
    def isect_line_plane_v3_wrap(p0, p1, p_co, p_no):
        isect = isect_line_plane_v3(p0.ToList(), p1.ToList(), p_co.ToList(), p_no.ToList())
        #print("np.arr:", isect)
        return Point3(isect[0], isect[1], isect[2])

# intersection function
def isect_line_plane_v3(p0, p1, p_co, p_no, epsilon=1e-6):
    """
    p0, p1: define the line
    p_co, p_no: define the plane:
        p_co is a point on the plane (plane coordinate).
        p_no is a normal vector defining the plane direction;
                (does not need to be normalized).

    return a Vector or None (when the intersection can't be found).
    """

    u = sub_v3v3(p1, p0)
    dot = dot_v3v3(p_no, u)

    if abs(dot) > epsilon:
        # the factor of the point between p0 -> p1 (0 - 1)
        # if 'fac' is between (0 - 1) the point intersects with the segment.
        # otherwise:
        #  < 0.0: behind p0.
        #  > 1.0: infront of p1.
        w = sub_v3v3(p0, p_co)
        fac = -dot_v3v3(p_no, w) / dot
        u = mul_v3_fl(u, fac)
        return add_v3v3(p0, u)
    else:
        # The segment is parallel to plane
        return None
