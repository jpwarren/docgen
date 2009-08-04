# $Id$
#

"""
Background element

This is used for arbitrary descriptive 'background' text
to be added to a document. The element wraps around
a bunch of DocBook format XML that is inserted into
appropriate human readable documentation.
"""
from docgen.base import XMLConfigurable, DynamicNaming

from lxml import etree

import debug
import logging
log = logging.getLogger('docgen')

class Background(XMLConfigurable, DynamicNaming):
    """
    Background descriptive prose explaining the project to humans.
    """
    xmltag = 'background'

    def configure_from_node(self, node, defaults, parent):
        self.node = node
        pass

    def get_docbook(self):
        """
        Return the contents of the node children.
        """
        retstr = ''
        for node in self.node.getchildren():
            retstr += etree.tostring(node, pretty_print=True)
            pass
        return retstr

def create_background_from_node(node, defaults, parent):
    background = Background()
    background.configure_from_node(node, defaults, parent)
    return background
        
