from imp import C_EXTENSION
from tkinter import W


class CollisionBox:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.coll = False
        self.colour = (0, 0, 255)

    # Checks if point is within box
    def DetectCollision(self, cx, cy):

        # Begin detection
        detected = False

        if (cx > self.x and cx < self.x + self.w and
            cy > self.y and cy < self.y + self.h):

            detected = True
        
        # If recording collison AND no collision detected
        if (self.coll==True and detected==False):
            # Collision is over, end recording
            self.coll = False
            return False

        # If not recording collison AND collision detected
        elif (self.coll==False and detected==True):
            # New collision, begin recording
            self.coll = True
            return True

        # Any other case
        else:
            return False




