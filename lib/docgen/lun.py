# $Id$
#

"""
DocGen SetRef object
This is used to refer to all the set objects,
like SnapVaultSet, SnapMirrorSet, etc.
"""
from base import DynamicNamedXMLConfigurable

import util

import debug
import logging
log = logging.getLogger('docgen')

class Lun(DynamicNamedXMLConfigurable):
    """
    A LUN representation object
    """
    xmltag = 'lun'

    child_tags = [ 
        'export',
        ]

    mandatory_attribs = [
        ]

    optional_attribs = [
        'name',
        'size',
        'lunid',
        'ostype',
        'restartnumbering',
        ]

    def __init__(self):
        self.igroup = None

    def configure_optional_attributes(self, node, defaults):
        """
        Configure optional Lun attributes
        """
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)        
        # Check to see if we need to restart the lunid numbering
        if self.restartnumbering is not None:
            self.parent.set_current_lunid( int(self.restartnumbering) )
            pass
        
        # Check to see if the lunid is specified for this lun
        if self.lunid is not None:
            self.lunid = int(self.lunid)
            log.debug("lunid manually specified: %d", self.lunid)
        else:
            self.lunid = self.parent.get_next_lunid()
            
        try:
            self.size = float(self.size)
        except TypeError:
            log.debug("No LUN size specified. Figuring it out...")

            # If you specify LUN sizes, the system will use exactly
            # what you define in the config file.
            # If you don't specify the LUN size, then the system will
            # divide up however much storage is left in the volume evenly
            # between the number of LUNs that don't have a size specified.

            # Count the number of LUNs with no size specified. Available
            # usable storage will be divided evenly between them
            nosize_luns = len(node.xpath("parent::*/descendant-or-self::lun[not(@size)]"))

            # total the number of sized luns
            sized_luns = node.xpath("parent::*/descendant-or-self::lun[(@size)]")
            log.debug("sized luns are: %s", sized_luns)
            sized_total = sum([ int(lun.attrib['size']) for lun in sized_luns ])
            log.debug("sized total is: %s", sized_total)

            log.debug("Available for allocation: %s", self.parent.get_iscsi_usable() - sized_total)

            self.size = float(self.parent.get_iscsi_usable() - sized_total) / nosize_luns
            log.debug("calculated lun size of: %s", self.size)
            pass
        
        log.debug("Allocating %sg storage to LUN", self.size)
        self.parent.add_to_lun_total(self.size)

    def full_path(self):
        """
        Return the full path string for LUN creation
        """
        return '%s/%s' % (self.parent.full_path(), self.name)

    def get_create_size(self):
        return util.get_create_size(self.size)
        
def create_lun_from_node(node, defaults, parent):

    lun = Lun()
    lun.configure_from_node(node, defaults, parent)
    return lun
