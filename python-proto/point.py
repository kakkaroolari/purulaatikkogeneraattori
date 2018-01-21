import math

class Point( object ):
    def __init__( self, x, y, z ):
        self.x, self.y, self.z = x, y, z
    def distFrom( self, x, y=None, z=None ):
        if isinstance(x, Point):
            (x,y,z) = (x.x, x.y, x.z)
        return math.sqrt( (self.x-x)**2 + (self.y-y)**2 + (self.z-z)**2 )
    
    def magnitude(v):
        return math.sqrt(v.x*v.x + v.y*v.y + v.z*v.z)

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
        return Point(new_x, new_y, new_z)
    
    def Translate(self, x, y=None, z=None):
        if isinstance(x, Point):
            (x,y,z) = (x.x, x.y, x.z)
        self.x += x
        self.y += y
        self.z += z

    #frakme
    #def Translate(self, point):
    #    self.Translate(point.x, point.y, point.z)

    def Clone(self):
        return self.moveCloserTo(Point(0.00,0.00,0.00), 0.0)
    
    def GetVectorTo(self, point):
        copy = self.Clone()
        copy.x = point.x - copy.x
        copy.y = point.y - copy.y
        copy.z = point.z - copy.z
        return copy

    def Normalize(vector, lenght=1):
        vmag = Point.magnitude(vector)
        normalized = Point(vector.x/vmag, vector.y/vmag, vector.z/vmag)
        normalized.x *= lenght
        normalized.y *= lenght
        normalized.z *= lenght
        return normalized

    #def default(self, obj):
    #    return {"point" : {"x":obj.x,"y":obj.y,"z":obj.z}}
    def __str__(self):
        return "Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
    def __unicode__(self):
        return u"Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
    def __repr__(self):
        return "Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
        #return {"point" : {"x":self.x,"y":self.y,"z":self.z}}
