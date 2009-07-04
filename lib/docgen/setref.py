# $Id$
#

"""
DocGen SetRef object
This is used to refer to all the set objects,
like SnapVaultSet, SnapMirrorSet, etc.
"""
from base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class SetRef(DynamicNamedXMLConfigurable):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'setref'

    child_tags = [ 
        ]

    mandatory_attribs = [
        'type',
        'name',
        ]
        
def create_setref_from_node(node, defaults, parent):

    sr = SetRef()
    sr.configure_from_node(node, defaults, parent)
    return sr
