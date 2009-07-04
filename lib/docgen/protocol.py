# $Id$
#

"""
DocGen Protocol object
"""
from base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class Protocol(DynamicNamedXMLConfigurable):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'protocol'
    child_tags = [ 
        ]

    mandatory_attribs = [ 'name' ]
        
def create_protocol_from_node(node, defaults, parent):

    proto = Protocol()
    proto.configure_from_node(node, defaults, parent)
    return proto
