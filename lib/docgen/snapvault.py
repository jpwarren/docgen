## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
SnapVault related design objects
"""
from docgen.base import XMLConfigurable, DynamicNaming

import debug
import logging
log = logging.getLogger('docgen')

class SnapVaultRelationship(XMLConfigurable, DynamicNaming):
    """
    A definition of a snapvault relationship
    """
    xmltag = 'snapvault'

    mandatory_attribs = [
        'basename',
        ]
    
    def configure_from_node(self, node, defaults, parent):
        self.configure_mandatory_attributes(node, defaults)
        self.configure_optional_attributes(node, defaults)
        
class SnapVault:
    """
    A SnapVault is a special kind of snapshot that requires a baseline
    to be taken on the source volume, which is then transferred to a
    SnapVault secondary device at some later time.

    A variant of the SnapVault is a destination only SnapVault snapshot,
    which assumes there is another SnapVault defined that will cause
    data to be transferred from a primary device. This destination only
    SnapVault is the mechanism recommended in the NetApp Best Practices Guide
    for doing weekly snapshots when you transfer data daily.
    """
    def __init__(self, sourcevol, targetvol, basename, src_schedule=None, dst_schedule=None):

        self.sourcevol = sourcevol
        self.targetvol = targetvol
        self.basename = basename
        self.src_schedule = src_schedule
        self.dst_schedule = dst_schedule

        self.sourcevol.snapvaults.append(self)
        self.targetvol.snapvaults.append(self)

    def __str__(self):
        return '<SnapVault: %s -> %s, %s, %s, %s>' % (self.sourcevol.namepath(),
                                                      self.targetvol.namepath(),
                                                      self.basename,
                                                      self.src_schedule,
                                                      self.dst_schedule,
                                                      )
    
def create_snapvault_from_node(node, defaults, parent):

    sv = SnapVaultRelationship()
    sv.configure_from_node(node, defaults, parent)
    return sv
