## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

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
