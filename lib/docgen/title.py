# $Id$
#

"""
Title element

This is used for the document titles.
"""
from docgen.base import XMLConfigurable, DynamicNaming

import debug
import logging
log = logging.getLogger('docgen')

class Title(XMLConfigurable, DynamicNaming):
    """
    The project title, used in various documents.
    """
    xmltag = 'title'

    def configure_from_node(self, node, defaults, parent):
        self.value = node.text
        pass

def create_title_from_node(node, defaults, parent):
    title = Title()
    return title.configure_from_node(node, defaults, parent)
        
