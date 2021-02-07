# -*- coding: utf-8 -*-

'''Section of Page.

In most cases, one section per page. But in case multi-columns page, sections are used 
to distinguish these different layouts.

.. note::
    Currently, support at most two columns.

::

{
    'bbox': (x0,y0,x1,y1)
    'cols': 1,
    'space': 0,
    'columns': [{
        ... # column properties
    }, ...]
}
'''

from ..common.docx import set_columns
from ..common.Collection import BaseCollection
from .Column import Column


class Section(BaseCollection):
    
    def __init__(self, space:int=0, columns:list=None, parent=None):
        """Initialize Section instance.

        Args:
            space (int, optional): [description]. Defaults to 0.
            columns (list, optional): [description]. Defaults to None.
            parent (Sections, optional): [description]. Defaults to None.
        """
        self.space = space
        super().__init__(columns, parent)
    

    @property
    def cols(self): return len(self)


    def store(self):
        '''Store parsed section layout in dict format.'''
        return {
            'bbox'   : tuple([x for x in self.bbox]),
            'cols'   : self.cols,
            'space'  : self.space,
            'columns': super().store()
        }
    

    def restore(self, raw:dict):
        '''Restore section from source dict.'''
        # bbox is maintained automatically based on columns
        self.cols  = raw.get('cols', 1) # one column by default
        self.space = raw.get('space', 0)   # space between adjacent columns

        # get each column
        for raw_col in raw.get('columns', []):
            column = Column().restore(raw_col)
            self.append(column)


    def parse(self, settings:dict):
        '''Parse section layout.'''
        for column in self: column.parse(settings)        
        return self
    

    def make_docx(self, doc):
        '''Create section in docx. 

        Args:
            doc (Document): ``python-docx`` document object
        '''
        # set section column
        section = doc.sections[-1]
        set_columns(section, self.cols, self.space)

        # add create each column
        for column in self:
            column.make_docx(doc)




