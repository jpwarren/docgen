## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
NetApp iSCSI related objects
"""
import logging
import debug
log = logging.getLogger('docgen')

class LUN:
    """
    A LUN lives in a Qtree and is used for iSCSI, predominantly.
    """

    def __init__(self, name, qtree, lunid, size, ostype, lunnode=None):

        self.name = name
        self.qtree = qtree
        self.size = size

        if ostype.lower().startswith('solaris'):
            ostype = 'solaris'

        elif ostype.lower().startswith('windows'):
            ostype = 'windows'

        elif ostype.lower().startswith('linux'):
            ostype = 'linux'

        else:
            raise ValueError("Operating system '%s' not support for iSCSI LUNs" % ostype)

        self.ostype = ostype
        self.lunid = lunid
        self.lunnode = lunnode
        self.exportlist = []
        
        self.igroup = None

        log.debug("Created lun: %s", self.name)

        qtree.luns.append(self)

    def full_path(self):
        """
        Return the full path string for LUN creation
        """
        return '%s/%s' % (self.qtree.full_path(), self.name)
        #return self.name

    def get_create_size(self):
        return get_create_size(self.size)

    def __repr__(self):
        return '<LUN %d: %s, %sg, %s, %s>' % (self.lunid, self.full_path(), self.size, self.ostype, self.igroup)

class iGroup:
    """
    An iGroup is a LUN mask for NetApp filers. It maps particular LUNs
    to the hosts (iSCSI initiators) that can access the LUNs.
    """

    def __init__(self, name, filer, exportlist=[], lunlist=[], type='windows'):
        self.name = name
        self.filer = filer
        self.type = type
        self.exportlist = exportlist
        self.lunlist = lunlist
        log.debug("Created iGroup %s", self)

    def __repr__(self):
        return '<iGroup: %s, %s, %s, %s>' % (self.name, self.type, self.filer.name, self.exportlist)

def create_lun():
    """
    Create a default LUN for a volume
    """
    
def create_lun_from_node(node, defaults, current_lunid, vol):
    """
    Create a LUN object from a node
    """
    # Check to see if we need to restart the lunid numbering
    if node.attrib.has_key('restartnumbering'):
        current_lunid = int(lunnode.attrib['restartnumbering'])

    # Check to see if the lunid is specified for this lun
    try:
        lunid = int(lunnode.attrib['lunid'])
        log.debug("lunid manually specified: %d", lunid)
    except KeyError:
        lunid = current_lunid
        current_lunid += 1

    try:
        lunsize = float(lunnode.xpath("@size")[0])
    except IndexError:
        log.debug("No LUN size specified. Figuring it out...")

        # If you specify LUN sizes, the system will use exactly
        # what you define in the config file.
        # If you don't specify the LUN size, then the system will
        # divide up however much storage is left in the volume evenly
        # between the number of LUNs that don't have a size specified.
        
        # Count the number of LUNs with no size specified. Available
        # usable storage will be divided evenly between them
        nosize_luns = len(vol.volnode.xpath("descendant-or-self::lun[not(@size)]"))

        # total the number of sized luns
        sized_luns = vol.volnode.xpath("descendant-or-self::lun[(@size)]")
        log.debug("sized luns are: %s", sized_luns)
        sized_total = sum([ int(lun.attrib['size']) for lun in sized_luns ])
        log.debug("sized total is: %s", sized_total)

        log.debug("Available for allocation: %s", vol.iscsi_usable - sized_total)

        lunsize = float(vol.iscsi_usable - sized_total) / nosize_luns
        log.debug("calculated lun size of: %s", lunsize)
        pass

    log.debug("Allocating %sg storage to LUN", lunsize)
    lun_total += lunsize

    # See if a qtree parent node exists
    try:
        qtree_parent_node = lunnode.xpath('parent::qtree')[0]
        qtree_parent = [ qtree for qtree in vol.qtrees.values() if qtree_parent_node == qtree.qtreenode ][0]
    except IndexError:
        # No qtree node defined, so use the first one in the volume.
        # Technically, there should only be one.
        qtree_parent = vol.qtrees.values()[0]

    try:
        lunname = lunnode.xpath("@name")[0]
    except IndexError:
        ns = qtree_parent.populate_namespace()
        ns['lunid'] = lunid
        lunname = defaults.get('lun', 'default_lun_name') % ns
        pass

    # ostype defaults to the same as the first host in my exportlist
    return LUN(name, qtree_parent, lunid, size, ostype, lunnode=node)
