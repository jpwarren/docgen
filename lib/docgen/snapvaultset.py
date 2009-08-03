# $Id$
#

"""
SnapVault set definitions
"""
from ConfigParser import NoSectionError, NoOptionError

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

    defaults_section = 'snapvault'
    
    child_tags = [
        'snapvaultdef',
        ]
    
    mandatory_attribs = [
        'name',
        'targetfiler',
        ]

    optional_attribs = [
        'targetaggregate',
        'targetvolume',
        'targetsuffix',
        'multiplier',
        'targetusable',
        ]

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)
        # If targetvolume isn't defined, targetaggregate is required.
        if self.targetvolume is None and self.targetaggregate is None:
            raise KeyError("'%s' node attribute 'targetaggregate' is not set" % self.xmltag)

        # Use a default multiplier if one isn't specified
        if self.multiplier is None:
            try:
                self.multiplier = defaults.getfloat(self.defaults_section, 'multiplier')
            except (NoSectionError, NoOptionError):
                self.multiplier = 2.5
            pass
        else:
            self.multiplier = float(self.multiplier)

        # Convert targetusable from text to a float 
        if self.targetusable is not None:
            self.targetusable = float(self.targetusable)
            pass

        if self.targetsuffix is None:
            try:
                self.targetsuffix = defaults.get(self.defaults_section, 'volsuffix')
            except (NoSectionError, NoOptionError):
                self.targetsuffix = 'b'
                pass
            pass

def create_snapvaultset_from_node(node, defaults, parent):
    """
    Create a snapvault set from a node definition.
    """
    obj = SnapVaultSet()
    obj.configure_from_node(node, defaults, parent)
    return obj
