## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
NetApp Volumes
"""


class Volume:

    def __init__(self, name, filer, aggr, usable, snapreserve=20, raw=None, type="fs", proto="nfs", voloptions=[], volnode=None, snapref=[], snapvaultref=[], snapmirrorref=[], snapvaultmirrorref=[], iscsi_snapspace=0):
        self.name = name
        self.filer = filer
        self.type = type
        self.proto = proto
        self.aggregate = aggr
        self.usable = float(usable)

        # A special kind of usable that is used for the actual iscsi LUN space
        # iSCSI really is a pain to allocate on WAFL
        self.iscsi_usable = self.usable
        self.iscsi_snapspace = iscsi_snapspace

        # Check that the filer doesn't already have a volume of this name on it
        if len([ vol for vol in self.filer.volumes if vol.name == self.name ]) > 0:
            raise ValueError("Filer '%s' already has a volume named '%s'" % (filer.name, self.name))

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

        if proto == 'iscsi':
            log.debug("volume proto is iscsi")
            # If snapshots are configured, double the usable storage to allow for 50% 'snapreserve'
##             log.debug("snapref: %s", snapref)
##             log.debug("snapvaultref: %s", snapvaultref)
##             log.debug("snapvaultmirrorref: %s", snapvaultmirrorref)
##             log.debug("snapmirrorref: %s", snapmirrorref)
            if len(snapref) > 0 or len(snapvaultref) > 0 or len(snapmirrorref) > 0 or len(snapvaultmirrorref) > 0:
                log.debug("snapshots present. doubling usable space of %s GiB for iscsi volume", self.usable)
                #snapdiv = (100 - float(iscsi_snapspace))/100
                snapspace = self.usable * ( float(iscsi_snapspace)/100 )
                log.debug("Adding iscsi_snapspace (%s%%) of %s GiB", iscsi_snapspace, snapspace)
                self.usable = (self.usable * 2.0) + snapspace
                log.debug("usable is now: %s GiB, iscsi_usable is: %s GiB", self.usable, self.iscsi_usable)
            else:
                # If no snapshots are configured, make the raw slightly more than usable
                log.debug("No snapshots, adding 1 GiB usable to volume size.")
                raw = self.usable + 1

        if raw is None:
            try:
                raw = self.usable / ( (100 - float(snapreserve) )/100 )
            except ZeroDivisionError, e:
                log.critical("snapreserve of 100% is not a valid value. You probably mean 50%.")
                raise ConfigInvalid(e)
            
        self.raw = raw

        self.snapreserve = int(round(snapreserve))

        self.snapref = snapref
        self.snapvaultref = snapvaultref
        self.snapmirrorref = snapmirrorref
        self.snapvaultmirrorref = snapvaultmirrorref

        # Lists of the actual snapX objects, added when they're created
        self.snaps = []
        self.snapvaults = []
        self.snapmirrors = []

        self.qtrees = {}

        # Set default volume options
        if len(voloptions) == 0:
            voloptions = [ 'nvfail=on',
                           'create_ucode=on',
                           'convert_ucode=on',
                           ]
        self.voloptions = voloptions
        self.volnode = volnode

        if self.name.endswith("root"):
            self.filer.volumes.insert(0, self)
        else:
            self.filer.volumes.append(self)
            pass

        self.filer.site.volumes.append(self)

        self.autosize = None
        self.autodelete = None

        # Default volume space guarantee setting is 'volume',
        # but for NearStores we want the space guarantee to be 'none',
        # unless overridden in the node definition
        if self.volnode is not None and self.volnode.attrib.has_key('space_guarantee'):
            log.debug("vol %s has space_guarantee set!", self)
            self.space_guarantee(self.volnode.attrib['space_guarantee'])
        else:
            log.debug("space_guarantee not set. Using default.")
            if self.filer.type == 'nearstore':
                # Default for NearStore volumes
                self.space_guarantee('none')
            else:
                # General default
                self.vol_space_guarantee = 'volume'
                pass
            pass
        
        log.debug("Created: %s", self)

    def __str__(self):
        return '<Volume: %s:/vol/%s, %s, aggr: %s, size: %sg usable (%sg raw)>' % (self.filer.name, self.name, self.type, self.aggregate, self.usable, self.raw)

    def get_create_size(self):
        """
        Get the raw size in a format acceptable to the vol create command,
        ie: integer amounts, and the appropriate scale (0.02g == 20m)
        """
        return get_create_size(self.raw)

    def shortpath(self):
        """
        The short path for the volume, eg: /vol/myproj_vol03
        """
        return '/vol/%s' % self.name
    
    def namepath(self):
        """
        The name path to the filer/volume, eg: exip-nas-02:/vol/myproj_vol03
        """
        return '%s:%s' % ( self.filer.name, self.shortpath() )
    
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

    def space_guarantee(self, value=None):
        """
        Set the volume space guarantee value, or fetch
        the current setting if no value is passed in
        """
        if value is not None:
            # check it's a valid value
            value = value.lower()
##             if value not in [ 'none', 'volume' ]:
##                 raise ValueError("Unsupported space guarantee value of '%s' for volume '%s'" % (value, self))
            self.vol_space_guarantee = value
            pass
        return self.vol_space_guarantee

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

