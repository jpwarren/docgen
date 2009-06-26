# $Id$
#

"""
SnapVault set definitions
"""
from docgen.base import XMLConfigurable, DynamicNaming

import debug
import logging
log = logging.getLogger('docgen')

class SnapVaultSet(XMLConfigurable, DynamicNaming):
    """
    A SnapVaultSet defines a set of SnapVault relationships
    that can be used as a grouping mechanism. This allows
    you to define a single rule for snapvaults that can be
    used for multiple volumes.
    """
    xmltag = 'snapvaultset'
    
    child_tags = [ 'snapvault', ]
    
    mandatory_attribs = [
        'id',
        'targetfiler',
        'targetaggregate',
        ]

    optional_attribs = [
        ]

def create_snapvaultset_from_node(node, defaults, parent):
    """
    Create a snapvault set from a node definition.
    """
    svs = SnapVaultSet()
    return svs.configure_from_node(node, defaults, parent)
