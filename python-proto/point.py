class Point( object ):
    def __init__( self, x, y, z ):
        self.x, self.y, self.z = x, y, z
    def distFrom( self, x, y, z ):
        return math.sqrt( (self.x-x)**2 + (self.y-y)**2 + (self.z-z)**2 )
    
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
    
    def __str__(self):
        return "Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
    def __unicode__(self):
        return u"Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
    def __repr__(self):
        return "Point({0:.2f}, {1:.2f}, {2:.2f})".format(self.x, self.y, self.z)
