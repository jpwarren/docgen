## $Id$

"""
SnapVaultDef object
"""
from base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class SnapVaultDef(DynamicNamedXMLConfigurable):
    """
    A definition of a snapvault relationship
    """
    xmltag = 'snapvaultdef'

    mandatory_attribs = [
        'basename',
        ]

    optional_attribs = [
        'snapschedule',
        'snapvaultschedule',
        ]

def create_snapvaultdef_from_node(node, defaults, parent):

    obj = SnapVaultDef()
    obj.configure_from_node(node, defaults, parent)
    return obj
