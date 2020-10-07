# -*- coding: utf-8 -*-

'''
Module to determin stream table borders.

Though no exact borders exist for stream table, it's better to simplify table structure by
aligning borders as more as possible. Taking vertical borders for example, it can be moved 
in a valid range in horizontal direction, but restricted by top and bottom borders in vertical 
direction. It's also true for horizontal borders.

Accordingly, introduce `Border` object, which has the following attributes:
- valid range, e. g. (100, 250);
- boundary borders, e. g. (top_border, bottom_border) for v-border, 
                       or (left_border, right_border) for h-border.

The target is to finalize the position in valid range, e. g. x=125 for v-border with valid range 
(120, 250). Then it's y-direction is determined by its boundary borders, where the y-coordinates 
are finalized in same logic. Finally, this border is fixed since both x- and y- directions are 
determined.

NOTE:
Consider horizontal and vertical borders only.

@created: 2020-08-29
@author: train8808@gmail.com
'''


from ..shape.Shapes import Shapes
from ..shape.Shape import Stroke
from ..common.utils import RGB_value
from ..common import constants
from ..common.base import RectType


class Border:

    def __init__(self, border_range:tuple=None, borders:tuple=None):
        '''Border for stream table.
            ---
            Args:
            - border_range: valid range, e.g. (x0, x1) for vertical border
            - borders: boundary borders, e.g. top and bottom horizontal borders for current vertical
            border; left and right vertical borders for current horizontal border. 
        '''
        # valid range
        self.set_border_range(border_range)

        # boundary borders
        self.set_boundary_borders(borders)
        
        # border style
        self.width = constants.HIDDEN_W_BORDER
        self.color = RGB_value((1,1,1)) # white by default

        # whether the position is determined
        self.finalized = False

    
    def is_valid(self, x:float):
        '''Whether the given position `x` locates in the valid border range.'''
        # consider margin here, but pay attention to underline which may be counted
        return (self.LRange-constants.MINOR_DIST) <= x <= (self.URange+constants.MINOR_DIST) 
    
    def set_border_range(self, border_range):
        '''Set border valid ranges.'''
        if border_range:
            x0, x1 = border_range
        else:
            x0, x1 = -9999, 9999
        self.LRange:float = x0
        self.URange:float = x1
        return self

    def set_boundary_borders(self, borders):
        '''Set boundary borders.'''
        if borders:
            lower_border, upper_border = borders
        else:
            lower_border, upper_border = None, None
        self._LBorder:Border = lower_border # left border, or top border
        self._UBorder:Border = upper_border # right border, or bottom border
        return self    

    @property
    def centerline(self):
        raise NotImplementedError

    def to_stroke(self):
        '''Convert to border stroke.'''
        stroke = Stroke({'color': self.color, 'width': self.width}).update_bbox(self.centerline)
        stroke.type = RectType.BORDER # set border style
        
        return stroke


class HBorder(Border):

    def __init__(self, border_range:tuple=None, borders:tuple=None):
        '''Horizontal border -> to determin y-coordinate.'''
        super().__init__(border_range, borders)
        self._y = None
    
    @property
    def y(self):
        ''' y-coordinate of horizontal border. Average value if not finalized.'''
        return self._y if self.finalized else (self.LRange+self.URange)/2.0

    @property
    def centerline(self):
        '''Center line of this border.'''
        return (self._LBorder.x, self.y, self._UBorder.x, self.y)

    def finalize(self, y:float):
        ''' Finalize border with given position.'''
        # can be finalized only one time
        if self.finalized or not self.is_valid(y): return self
        self._y = y
        self.finalized = True
        return self

    def finalize_by_stroke(self, stroke:Stroke):
        ''' Finalize border with specified horizontal stroke shape, which is generally a showing border.        
            NOTE: the boundary borders may also be affected by this stroke shape.
        '''
        x0, x1 = stroke.x0, stroke.x1
        y = stroke.y0 # equal to stroke.y1

        # skip if 

        # skip if no intersection in y-direction
        if self.finalized or not self.is_valid(y): return self

        # skip if not span in x-ditrection
        if x0 > self._LBorder.URange and x1 < self._UBorder.LRange: return self

        # now, it can be used to finalize current border
        self.finalize(y)
        self.color = stroke.color
        self.width = stroke.width

        # and, try to finalize boundary borders
        self._LBorder.finalize(x0)
        self._UBorder.finalize(x1)

        # update rect type as table border
        stroke.type = RectType.BORDER

        return self


class VBorder(Border):

    def __init__(self, border_range:tuple=None, borders:tuple=None):
        '''Vertical border -> to determin x-coordinate.'''
        super().__init__(border_range, borders)
        self._x = None

    @property
    def x(self):
        ''' x-coordinate of vertical border. Average value if not finalized.'''
        return self._x if self.finalized else (self.LRange+self.URange)/2.0

    @property
    def centerline(self):
        '''Center line of this border.'''
        return (self.x, self._LBorder.y, self.x, self._UBorder.y)  
    
    def finalize(self, x:float):
        '''Finalize border with given position.'''
        # can be finalized fo only one time
        if self.finalized or not self.is_valid(x): return self
        self._x = x
        self.finalized = True
        return self
    
    def finalize_by_stroke(self, stroke:Stroke):
        ''' Finalize border with specified horizontal rect, which is generally a showing border.        
            NOTE: the boundary borders may also be affected by this rect.
        '''
        y0, y1 = stroke.y0, stroke.y1
        x = stroke.x0 # or stroke.x1

        # skip if no intersection in x-direction
        if self.finalized or not self.is_valid(x): return self

        # skip if no intersection in x-ditrection
        if y0 > self._LBorder.URange and y1 < self._UBorder.LRange: return self

        # now, it can be used to finalize current border
        self.finalize(x)
        self.color = stroke.color
        self.width = stroke.width

        # and, try to finalize boundary borders
        self._LBorder.finalize(y0)
        self._UBorder.finalize(y1)

        # update rect type as table border
        stroke.type = RectType.BORDER

        return self


class Borders:
    '''Collection of Border instances.'''
    def __init__(self):
        ''' Init collection with empty borders.'''
        self._HBorders = [] # type: list[HBorder]
        self._VBorders = [] # type: list[VBorder]


    def __iter__(self):
        return (instance for instance in self._HBorders+self._VBorders)

    def __len__(self):
        return len(self._HBorders) + len(self._VBorders)
    

    def add(self, border:Border):
        '''Add border.'''
        if isinstance(border, HBorder):
            self._HBorders.append(border)        
        elif isinstance(border, VBorder):
            self._VBorders.append(border)
    

    def extend(self, borders:list):
        for border in borders: self.add(border)

    @property
    def HBorders(self): return self._HBorders

    @property
    def VBorders(self): return self._VBorders

    def finalize(self, strokes:Shapes, fills:Shapes):
        ''' Finalize the position of all borders:
            - follow explicit stroke/border
            - follow explicit fill/shading
            - align h-borders or v-borders as more as possible to simplify the table structure.
            ---
            Args:
            - strokes: a group of explicit border strokes.
            - fills: a group of explicit cell shadings.
        '''
        # finalize borders by explicit strokes in first priority
        h_strokes = filter(lambda stroke: stroke.horizontal, strokes)
        v_strokes = filter(lambda stroke: stroke.vertical,   strokes)
        self._finalize_by_strokes(h_strokes, v_strokes)

        # finalize borders by explicit fillings in second priority
        h_strokes, v_strokes = [], []
        for fill in fills:
            x0, y0, x1, y1 = fill.bbox
            h_strokes.extend([
                Stroke().update_bbox((x0, y0, x1, y0)),
                Stroke().update_bbox((x0, y1, x1, y1))
            ])
            v_strokes.extend([
                Stroke().update_bbox((x0, y0, x0, y1)),
                Stroke().update_bbox((x1, y0, x1, y1))
            ])
        self._finalize_by_strokes(h_strokes, v_strokes)

        # finalize borders by their layout finally
        # un-finalized h-borders
        borders = list(filter(lambda border: not border.finalized, self._HBorders))
        self._finalize_by_layout(borders)

        # un-finalized v-borders
        borders = list(filter(lambda border: not border.finalized, self._VBorders))
        self._finalize_by_layout(borders)

    
    def _finalize_by_strokes(self, h_strokes:list, v_strokes:list):
        '''Finalize by explicit strokes.'''
        for stroke in h_strokes:
            for border in self._HBorders:            
                border.finalize_by_stroke(stroke)

        for stroke in v_strokes:
            for border in self._VBorders:            
                border.finalize_by_stroke(stroke)


    @staticmethod
    def _finalize_by_layout(borders:list):
        ''' Finalize the position of all borders: align borders as more as possible to simplify the table structure.
            ---
            Args:
            - borders: a list of HBorder or VBorder instances
            
            Taking finalizing vertical borders for example:
            - initialize a list of x-coordinates, [x0, x1, x2, ...], with the interval points of each border
            - every two adjacent x-coordinates forms an interval for checking, [x0, x1], [x1, x2], ...
            - for each interval, count the intersection status of center point, x=(x0+x1)/2.0, with all borders
            - sort center point with the count of intersections in decent order
            - finalize borders with x-coordinate of center points in sorting order consequently
            - terminate the process when all borders are finalized
        '''
        # collect interval points and sort in x-increasing order
        x_points = set()
        for border in borders:
            x_points.add(border.LRange)
            x_points.add(border.URange)
        
        x_points = list(x_points)
        x_points.sort()

        # check intersection status of each intervals
        x_status = [] # [(x, status), ...]
        for i in range(len(x_points)-1):
            x = (x_points[i]+x_points[i+1])/2.0 # cenper point
            s = list(map(
                    lambda border: int(border.is_valid(x)), borders))
            x_status.append((x,s))
            
        # sort per count since preferring passing through more borders
        x_status.sort(key=lambda item: sum(item[1]), reverse=True)

        # finalize borders
        num = len(borders)
        current_status = [0] * num
        for x, status in x_status:
            # terminate if all borders are finalized
            if sum(current_status) == num: break

            # only one line is allowed to pass through one border range -> sum(A.*B)=0
            #  e.g. A = [1,0,1,0], B=[0,1,0,0] -> valid
            #       A = [1,0,1,0], B =[1,0,0,0] -> invalid due to two lines passing through border 1
            duplicated = sum([c1*c2 for c1,c2 in zip(current_status, status)])
            if duplicated: continue

            # update current status
            current_status = [c1+c2 for c1,c2 in zip(current_status, status)]

            # now, finalize borders
            for border, border_status in zip(borders, status):
                if border_status: border.finalize(x)