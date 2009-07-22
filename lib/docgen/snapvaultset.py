# $Id$
#

"""
SnapVault set definitions
"""
from docgen.base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class SnapVaultSet(DynamicNamedXMLConfigurable):
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
        ]

    optional_attribs = [
        'targetaggregate',
        'targetvolume',
        ]

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)
        # If targetvolume isn't defined, targetaggregate is required.
        if self.targetvolume is None and self.targetaggregate is None:
            raise KeyError("'%s' node attribute 'targetaggregate' is not set" % self.xmltag)

def create_snapvaultset_from_node(node, defaults, parent):
    """
    Create a snapvault set from a node definition.
    """
    svs = SnapVaultSet()
    return svs.configure_from_node(node, defaults, parent)
