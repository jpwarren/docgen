# $Id$
#

"""
SnapMirror set definitions
"""
from docgen.base import XMLConfigurable, DynamicNaming
from docgen.snapvaultset import SnapVaultSet

import debug
import logging
log = logging.getLogger('docgen')

class SnapMirrorSet(SnapVaultSet):
    """
    A SnapMirrorSet is the same kind of idea as a SnapVaultSet,
    but it contains snapmirror definitions instead.
    """
    xmltag = 'snapmirrorset'
    
    child_tags = [ 'snapmirror', ]

def create_snapmirrorset_from_node(node, defaults, parent):
    """
    Create a snapvault set from a node definition.
    """
    sms = SnapMirrorSet()
    sms.configure_from_node(node, defaults, parent)
    return sms
