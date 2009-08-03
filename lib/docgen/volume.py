## $Id$

"""
NetApp Volumes
"""
from ConfigParser import NoSectionError, NoOptionError
from lxml import etree

from docgen.base import DynamicNamedXMLConfigurable
from docgen import util
from docgen.qtree import Qtree

import logging
import debug
log = logging.getLogger('docgen')

class Volume(DynamicNamedXMLConfigurable):
    """
    A NetApp volume object
    """
    xmltag = 'volume'

    child_tags = [
        'qtree',
        'lun',
        'setref',
        'option',
        #'protocol',
#        'autosize',
#        'autodelete',
        ]

    mandatory_attribs = [
        ]

    optional_attribs = [
        'name',
        'prefix',
        'suffix',
        'type',
        'usable',
        'raw',
        'snapreserve',
        'iscsi_snapspace',
        'snapstorage',
#        'autosize',
#        'autodelete',
        'protocol',
        'oplocks',
        ]

    # FIXME: May not need the parent_type_names feature
#     parent_type_names = [ 'Aggregate',
#                           ]

    def __init__(self):
        self.current_lunid = 0
        self.lun_total = 0

    def __str__(self):
        return '<Volume: %s:/vol/%s, %s, aggr: %s, size: %sg usable (%sg raw)>' % (self.parent.get_filer().name, self.name, self.type, self.parent.name, self.usable, self.raw)

    def _depr__init__(self, name, filer, aggr, usable, snapreserve=20,
                 raw=None, type="fs", proto="nfs",
                 voloptions=[], volnode=None,
                 snapref=[], snapvaultref=[],
                 snapmirrorref=[], snapvaultmirrorref=[],
                 iscsi_snapspace=0):
        
        self.name = name
        self.filer = filer
        self.type = type
        self.proto = proto
        self.aggregate = aggr
        self.usable = float(usable)

    def configure_from_node(self, node, defaults, parent):
        """
        Volume configuration is quite complex, due to the way we attempt
        to cater for all kinds of situations automatically, using configurable
        defaults and various overrides.
        """
        self.parent = parent
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        # Check if iscsi is an enabled protocol. If so, use 'iscsi_snapspace' instead
        # of snapreserve
        #if 'iscsi' in [ x.name for x in self.get_protocols() ]:
        if 'iscsi' == self.protocol:
            self.snapreserve = 0
            if getattr(self, 'iscsi_snapspace', None):
                self.iscsi_snapspace = defaults.getint('volume', 'default_iscsi_snapspace')
            else:
                self.iscsi_snapspace = int(self.iscsi_snapspace)
                pass
            pass

            # iSCSI LUN sizing is... interesting
            # Best practice is to have no snapreserve for volumes
            # used for iscsi, but we need to have some storage
            # available for snapshots. Because LUNs are just files full
            # of blocks, we have to allocate enough storage for all
            # of the blocks to change, so we need 2 * LUNsize GiB to
            # store the snapshots.
            # If you're not using snapshots, you will need a little extra
            # space in the volume so the LUN can fit within it. The LUN
            # can't take up 100% of the volume (i.e.: A LUN of 100GiB
            # will require a volume of 101GiB in size)

            log.debug("volume proto is iscsi")
            # If snapshots are configured, double the usable storage to allow for 50% 'snapreserve'
            if len(self.get_snaprefs()) > 0 or \
                    len(self.get_snapvaultrefs()) > 0 or \
                    len(self.get_snapmirrorrefs()) > 0 or \
                    len(self.get_snapvaultmirrorrefs()) > 0:
                
                log.debug("snapshots present. doubling usable space of %s GiB for iscsi volume", self.usable)
                #snapdiv = (100 - float(iscsi_snapspace))/100
                snapspace = self.usable * ( float(iscsi_snapspace)/100 )
                log.debug("Adding iscsi_snapspace (%s%%) of %s GiB", iscsi_snapspace, snapspace)
                self.usable = (self.usable * 2.0) + snapspace
                log.debug("usable is now: %s GiB, iscsi_usable is: %s GiB", self.usable, self.iscsi_usable)
            else:
                # If no snapshots are configured, make the raw slightly more than usable
                log.debug("No snapshots, adding 1 GiB usable to volume size.")
                self.raw = self.usable + 1
                pass
            pass
        
#         self.snapref = snapref
#         self.snapvaultref = snapvaultref
#         self.snapmirrorref = snapmirrorref
#         self.snapvaultmirrorref = snapvaultmirrorref

        # Lists of the actual snapX objects, added when they're created
        self.snaps = []
        self.snapvaults = []
        self.snapmirrors = []

        #self.qtrees = {}

        # Set volume options as a dictionary
        options = {}
        if len(self.children['option']) == 0:
            # FIXME: deal with user errors in the config file better
            for opt in defaults.get('volume', 'default_options').split(','):
                name, value = opt.split('=')
                options[name] = value
                pass
        else:
            for opt in self.children['option']:
                name, value = opt.split('=')
                options[name] = value
                pass
            pass
        self.children['option'] = options

        self.volnode = node

        # If volume export is not allowed, check that qtrees exist in the
        # volume. If not, create a single default data qtree.
        self.check_volume_export_allowed(defaults)

        self.autosize = None
        self.autodelete = None

        log.debug("volume usable is: %f", self.usable)

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)
        
        # Set volume name prefix
        self.prefix = getattr(self, 'prefix', '')

        # Set volume name suffix
        self.suffix = getattr(self, 'suffix', '')

        # Set volume name suffix
        if self.type is None:
            self.type = defaults.get('volume', 'default_vol_type')

        # Check to see if we want to restart the volume numbering
        # FIXME: Get the current volume numbering thing from parent
        volnum = getattr(self, 'restartnumbering', None)
        if volnum is None:
            # Don't grab a new number if this is the root volume
            # for a vfiler. Only number data volumes.
            if self.type != 'root':
                self.volnum = self.parent.get_next_volnum()
        else:
            self.volnum = int(volnum)
            parent.set_volnum(self.volnum)

        # Set usable storage
        if getattr(self, 'usable', None) is None:
            self.usable = defaults.getfloat('volume', 'default_size')
        else:
            self.usable = float(self.usable)

        # Set allowable protocols for the volume
        # The volume protocol is either a protocol set in the volume definition
        # using the 'proto' attribute, or it will be the first protocol in
        # the list of possible protocols for the vfiler.
        # If neither of these are set, it will be set to the default
        try:
            self.protocol = node.attrib['protocol'].lower()
            log.debug("Proto defined for volume: %s", self.protocol)

        except KeyError:
            try:
                self.protocol = node.xpath("ancestor::*/vfiler/protocol/text()")[0].lower()
                #log.debug("Found proto in vfiler ancestor: %s", self.protocol)
            except IndexError:
                self.protocol = defaults.get('protocol', 'default_storage_protocol')
                log.debug("Proto set to default: %s", self.protocol)
            
        # Set snapreserve and iSCSI snapspace
        if getattr(self, 'snapreserve', None) is None:

            # If the volume is a type that we know has a high rate of change,
            # we set a different snapreserve.
            try:
                highdelta_types = defaults.get('volume', 'high_delta_types')
            except (NoSectionError, NoOptionError):
                highdelta_types = []
                pass
            
            if self.type in highdelta_types:
                self.snapreserve = defaults.getint('volume', 'default_highdelta_snapreserve')
            else:
                self.snapreserve = defaults.getint('volume', 'default_snapreserve')
        else:
            self.snapreserve = float(self.snapreserve)
            pass

        # Round the snapreserve
        self.snapreserve = int(round(self.snapreserve))
            
        # A special kind of usable that is used for the actual iscsi LUN space
        # iSCSI really is a pain to allocate on WAFL
        self.iscsi_usable = self.usable
        try:
            self.iscsi_snapspace = defaults.get('volume', 'iscsi_snapspace')
        except (NoOptionError, NoSectionError):
            self.iscsi_snapspace = 0

        if getattr(self, 'raw', None) is None:
            try:
                self.raw = self.usable / ( (100 - float(self.snapreserve) )/100 )
            except ZeroDivisionError, e:
                log.critical("snapreserve of 100% is not a valid value. You probably mean 50%.")
                raise ZeroDivisionError(e)
        else:
            self.raw = float(self.raw)
            
        # Default volume space guarantee setting is 'volume',
        # but for NearStores we want the space guarantee to be 'none',
        # unless overridden in the node definition
        # FIXME: Do this using defaults config file
        if getattr(self, 'space_guarantee', None) is None:
            log.debug("space_guarantee not set. Using default.")
            option_name = "%s_space_guarantee_default" % self.parent.get_filer().type
            self.space_guarantee = defaults.get('volume', option_name)
            pass
        
    def name_dynamically(self, defaults):
        # Work out the volume name, if it isn't set
        if getattr(self, 'name', None) is None:

            # Set up a namespace for use in naming
            ns = self.populate_namespace()

            volname_convention = defaults.get('volume', 'volume_name')
            #log.debug("volume naming convention: %s", volname_convention)
            try:
                self.name = volname_convention % ns
            except KeyError, e:
                raise KeyError("Unknown variable %s for volume naming convention" % e)
        
    def populate_namespace(self, ns={}):
        """
        Add my own namespace pieces
        """
        ns = self.parent.populate_namespace(ns)
        ns['volume_name'] = self.name
        ns['volume_type'] = self.type
        ns['voltype'] = self.type
        ns['volprefix'] = self.prefix
        ns['volsuffix'] = self.suffix
        ns['volnum'] = self.volnum
        return ns

    def get_filer(self):
        return self.parent.get_filer()
    
    def get_create_size(self):
        """
        Get the raw size in a format acceptable to the vol create command,
        ie: integer amounts, and the appropriate scale (0.02g == 20m)
        """
        return util.get_create_size(self.raw)

    def shortpath(self):
        """
        The short path for the volume, eg: /vol/myproj_vol03
        """
        return '/vol/%s' % self.name

    def full_path(self):
        return self.shortpath()
    
    def namepath(self):
        """
        The name path to the filer/volume, eg: exip-nas-02:/vol/myproj_vol03
        """
        return '%s:%s' % ( self.parent.get_filer().name, self.shortpath() )

    def _ippath(self):
        """
        Similar to the name path, but using the storage IP of the filer as the target.
        """
        return '%s:%s' % ( self.filer.name, self.shortpath() )

    def has_snaps(self):
        """
        If the volume has snapshots of any kind (snapshot, SnapVaults, SnapMirrors), return True
        """
        if len(self.snaps) > 0 or len(self.snapvaults) > 0 or len(self.snapmirrors) > 0:
            return True

    def get_next_lunid(self):
        """
        Get the next available lunid for the volume
        """
        value = self.current_lunid
        self.current_lunid += 1
        return value

    def set_current_lunid(self, value):
        self.current_lunid = value

    def add_to_lun_total(self, amount):
        """
        Add an amount of gigabytes to the running lun total for
        the volume.
        """
        self.lun_total += amount

    def get_iscsi_usable(self):
        return self.iscsi_usable

    def check_volume_export_allowed(self, defaults):
        """
        Check to see if the volume itself is allowed to be exported.
        If not, check that qtrees exist in the volume. If they don't,
        then we create a default data qtree that can be exported.
        """
        try:
            vol_export_allowed = defaults.getboolean('volume', 'allow_volume_export')
        except (NoOptionError, NoSectionError), e:
            # assume no
            vol_export_allowed = False
            pass

        if not vol_export_allowed and not self.type == 'root':
            log.debug("volume export not allowed. checking for qtrees...")
            if len(self.get_qtrees()) == 0:
                log.debug("No qtrees.")
                # Create a qtree and add it to myself.
                xmldata = """<qtree/>"""
                node = etree.fromstring(xmldata)
                qtree = Qtree()
                qtree.configure_from_node(node, defaults, self)
                self.add_child(qtree)
                log.debug("Added a default qtree for export: %s, %s", qtree, self.get_qtrees())

    def get_luns(self):
        """
        Fetch all the LUNs defined in the volume and any
        of its qtrees.
        """
        # get a copy of my list of luns
        luns = self.children['lun'][:]

        # add all the luns in my qtrees as well
        for qtree in self.get_qtrees():
            luns.extend( qtree.get_luns() )
            pass

        return luns

    def get_snapmirror_setrefs(self):
        return [ x for x in self.get_setrefs() if x.type == 'snapmirror' ]

    def get_snapvault_setrefs(self):
        return [ x for x in self.get_setrefs() if x.type == 'snapvault' ]
    
class VolumeAutoSize:
    """
    VolumeAutoSize is a setting used for Volumes to define how
    they grow automatically.
    """
    def __init__(self, volume, max, increment):

        # My parent Volume object
        self.volume = volume

        # The maximum size to grow to
        self.max = max

        # How much to grow by whenever we increase
        self.increment = increment

    ## FIXME: These should be split off into a subclass. This would
    ## allow another set of 'zapi_add' style commands, or ModiPy
    ## changes or change templates, perhaps.
    def command_add(self):
        """
        The sequence of commands to use when provisioning for the first time
        """
        cmdset = []
        cmdset.append("vol autosize %s -m %s -i %s on" % (self.volume.name, self.max, self.increment) )
        return cmdset

    def command_change(self, previous):
        """
        The sequence of commands to use when changing my value when compared
        with the 'previous' setting.
        """
        cmdset = []
        cmdset.append("vol autosize %s -m %s -i %s on" % (self.volume.name, self.max, self.increment) )
        return cmdset

    def command_delete(self):
        """
        The sequence of commands to use when deleting me from the device configuration.
        """
        cmdset = []
        cmdset.append("vol autosize %s off" % (self.volume.name))
        return cmdset

    
class VolumeAutoDelete:
    """
    VolumeAutoDelete defines how a volume can be set up to have
    snapshots automatically deleted if it gets full.
    """
    
    def __init__(self, volume, commitment='try',
                 trigger='volume',
                 target_free_space=80,
                 delete_order='oldest_first',
                 defer_delete='none'):
        """
        Define the snapshot autodelete settings for a volume
        """
        self.volume = volume
        self.commitment = commitment
        self.trigger = trigger
        self.target_free_space = target_free_space
        self.delete_order = delete_order
        self.defer_delete = defer_delete
        self.prefix = None

    def __str__(self):
        """
        Stringified representation of VolumeAutoDelete
        """
        return "<AutoDelete: %s: %s %s %s %s" % ( self.volume.name, self.commitment,
                                                  self.trigger, self.target_free_space,
                                                  self.delete_order)

    def configure_from_node(self, node):
        """
        Re-configure myself from the settings defined in the XML node
        """
        for option in ['commitment',
                       'trigger',
                       'target_free_space',
                       'delete_order',
                       ]:
            try:
                setattr(self, option, node.attrib[option])
                #log.debug("set attribute '%s' to '%s'", option, getattr(self, option))
            except KeyError:
                #log.debug("attribute '%s' not defined in XML node." % option)
                pass

    def command_add(self):
        """
        Commandset to add this configuration to a device.
        """
        cmdset = []
        # set all the autodelete options
        for option in [ 'commitment',
                        'trigger',
                        'target_free_space',
                        'delete_order',
                        ]:
            cmdset.append("snap autodelete %s %s %s" % (self.volume.name, option, getattr(self, option)) )
            pass

        # then, actually turn on autodelete
        cmdset.append("snap autodelete %s on" % (self.volume.name))
        return cmdset

                

    def get_settings(self):
        """
        Return a dictionary of my settings.
        This is useful for building tables in the human readable output documents.
        """
        dict = {}
        for option in [ 'commitment',
                        'trigger',
                        'target_free_space',
                        'delete_order',
                        ]:
            dict[option] = getattr(self, option)
            pass
        return dict

def create_volume_from_node(node, defaults, parent):
    """
    Create a volume from a node
    """
    vol = Volume()
    vol.configure_from_node(node, defaults, parent)
    return vol
    
def _depr_create_volume_from_node(node, defaults, parent):
    """
    Create a volume, using certain defaults as required.
    """

#     snapref = node.xpath("snapsetref/@name")
#     snapvaultref = node.xpath("snapvaultsetref/@name")
#     snapmirrorref = node.xpath("snapmirrorsetref/@name")
#     snapvaultmirrorref = node.xpath("snapvaultmirrorsetref/@name")

#     voloptions = [ x.text for x in node.xpath("option") ]

    # Default snap reserve to 20 unless specified otherwise
    # Default iscsi_snapspace to 0 unless specified otherwise
    iscsi_snapspace=0
    try:
        snapreserve = float(node.attrib['snapreserve'])
    except KeyError:
        #log.debug("No snapreserve specified.")
        if proto == 'iscsi':
            snapreserve = 0
            # iSCSI volumes need the ability to define space used for storing
            # snapshots, but without turning on snapreserve, which functions
            # differently. This is usable space allocated as overhead for
            # snapshots, because snapreserve is set to 0, but won't be used
            # by the LUNs, because they are files of fixed size created inside
            # the usable space.
            # This percentage value will be added to the raw space provided for
            # the volume.
            try:
                iscsi_snapspace = node.attrib['iscsi_snapspace']
            except KeyError:
                iscsi_snapspace = defaults.getint('volume', 'default_iscsi_snapspace')

        elif voltype in ['oraundo', 'oraarch', ]:
            snapreserve = defaults.getint('volume', 'default_highdelta_snapreserve')
        else:
            snapreserve = defaults.getint('volume', 'default_snapreserve')
            pass
        pass

    # See if we want to specify a particular amount of snapshot storage
    # This will override the snapreserve setting
    try:
        snapstorage = float(node.findall("snapstorage")[0].text)
        #log.info("snapstorage of %.2f GiB set", snapstorage)
        raw = usable + snapstorage
        #log.info("raw storage is now: %.2f", raw)

        # snapreserve is always an integer percentage, so round it            
        snapreserve = int(round(100 - ((usable / raw) * 100.0)))
        #log.info("snapreserve is: %s", snapreserve)

    except IndexError:
        snapstorage = None

    if snapstorage is not None:
        vol = Volume( volname, filer, aggr, usable, snapreserve, raw, type=voltype, proto=proto, voloptions=voloptions, volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref, iscsi_snapspace=iscsi_snapspace)
    else:
        vol = Volume( volname, filer, aggr, usable, snapreserve, type=voltype, proto=proto, voloptions=voloptions, volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref, iscsi_snapspace=iscsi_snapspace)

    # See if there is an autosize setting on either the volume, or the
    # containing aggregate. Use the first one we find.
    autosize = node.xpath('autosize | parent::*/autosize')
    if len(autosize) > 0:
        autosize = autosize[0]
        #log.debug("found autosize: %s", autosize)
        # Set autosize parameters
        vol.autosize = VolumeAutoSize(vol, autosize.attrib['max'], autosize.attrib['increment'])
        pass

    # See if there is an autodelete setting for snapshots
    autodelete = node.xpath('autodelete | parent::*/autodelete')
    if len(autodelete) > 0:
        autodelete = autodelete[0]
        #log.debug("found autodelete: %s", autodelete)
        # Set autodelete parameters
        vol.autodelete = VolumeAutoDelete(vol)
        vol.autodelete.configure_from_node(autodelete)
        pass

    volnum += 1
    return vol, volnum

