# $Id$
#

"""
DocGen Project definitions.

The <project/> node is the root of all DocGen projects,
and is used to dynamically configure and build the project
definition.
"""
from ConfigParser import NoSectionError, NoOptionError
from base import DynamicNamedXMLConfigurable, LunNumbering

from lxml import etree

# FIXME: Doing it this way means we can't override this in
# a user defined plugin. Need the lookup table instead.
from volume import Volume
from aggregate import Aggregate
from snapmirror import SnapMirror
from snapvault import SnapVault
from igroup import iGroup

import debug
import logging
log = logging.getLogger('docgen')

class Project(DynamicNamedXMLConfigurable, LunNumbering):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'project'
    child_tags = [
        'background',
        'revision',
        'site',
        'snapvaultset',
        'snapmirrorset',
        ]

    mandatory_attribs = [ 'name', 'code' ]

    optional_attribs = [
        'title',
        ]

    def __init__(self):
        self.current_lunid = 0

    def populate_namespace(self, ns={}):
        """
        Add my namespace pieces to the namespace
        """
        ns['project_name'] = self.name
        ns['project_code'] = self.code
        return ns

    def get_next_lunid(self, defaults):
        value = self.current_lunid
        self.current_lunid += 1
        return value

    def set_current_lunid(self, value, defaults):
        self.current_lunid = value        
    
    def get_hosts(self):
        """
        Find all the project hosts
        """
        objs = []
        for site in self.get_sites():
            objs.extend(site.get_hosts())
            pass
        return objs

    def get_host_byname(self, hostname):
        """
        Find a host using its name
        """
        try:
            host = [ x for x in self.get_hosts() if x.name == hostname ][0]
            return host
        except IndexError:
            raise KeyError("Host '%s' is not specified in definition" % hostname)

    def get_volumes(self):
        """
        Find all the project volumes
        """
        volumes = []
        for site in self.get_sites():
            volumes.extend(site.get_volumes())
            pass
        return volumes

    def get_luns(self):
        luns = []
        for vol in self.get_volumes():
            luns.extend( vol.get_luns() )
            pass
        return luns

    def get_filers(self):
        filers = []
        for site in self.get_sites():
            filers.extend(site.get_filers())
            pass
        return filers

    def get_latest_revision(self):
        revlist = [ ('%s.%s' % (x.majornumber, x.minornumber), x) for x in self.get_revisions() ]
        revlist.sort()
        #log.debug("Last revision is: %s", revlist[-1])
        try:
            return revlist[-1][1]
        except IndexError:
            raise KeyError("No project revisions have been defined!")

    def get_project_vlan(self, site):
        """
        Find the project vlan for the site
        """
        vlan = [ vlan for vlan in site.get_vlans() if vlan.type == 'project' ][0]
        return vlan

    def get_services_vlans(self, site=None):
        """
        Return a list of all vlans of type 'services'
        """
        if site is None:
            # In order to understand recursion, you must first understand recursion
            vlans = []
            for site in self.get_sites():
                vlans.extend( self.get_services_vlans(site) )
                pass
            return vlans
        else:
            return [ vlan for vlan in site.get_vlans() if vlan.type == 'service' ]

    def get_allowed_protocols(self):
        """
        Get all the protocols defined anywhere in the project
        """
        protolist = []
        for site in self.get_sites():
            for proto in site.get_allowed_protocols():
                if proto not in protolist:
                    protolist.append(proto)
                    pass
                pass
            pass
        return protolist

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        #
        # Once the project is configured, set up some other bits and pieces
        #
        self.setup_drhosts(defaults)
        
        self.setup_exports(defaults)

        self.setup_igroups(defaults)

        self.setup_snapmirrors(defaults)

        self.setup_snapvaults(defaults)

    def setup_drhosts(self, defaults):
        """
        Link hosts with their drhosts, if any are defined.
        drhosts are used for failover in the event of a DR.
        """
        for host in self.get_hosts():
            host.children['drhost'] = []
            for hostname in host.get_drhostnames():
                host.children['drhost'].append( self.get_host_byname(hostname) )
                pass
            pass
        
    def setup_exports(self, defaults):
        """
        Set up all the exports for my sites using either manually
        configured exports, or appropriate defaults.
        """
        for site in self.get_sites():
            site.setup_exports()
            pass

    def setup_igroups(self, defaults):
        """
        Set up iGroups for all filers/vfilers.
        If an iGroup has been manually defined, link to the host
        objects that the iGroup refers to as members.
        """
        igroups = []
        igroups.extend( self.setup_auto_igroups(defaults) )
        pass

    def setup_auto_igroups(self, defaults):
        """
        Automatically create iGroups for LUNs that need them
        This algorithm creates the minimum number of
        iGroups based on the way in which the storage is
        shared between servers. Servers that share the same
        set of LUNs are made part of the same iGroup.
        """
        log.debug("No manually defined igroups exist. Auto-generating them...")
        log.debug("There are %d luns to process", len(self.get_luns()) )

        igroups = []
        # Split the LUNs into per-site lists
        for site in self.get_sites():
            log.debug("siteluns: %d luns in %s: %s", len(site.get_luns()), site.type, site.get_luns())

            site_igroups = []
            for lun in site.get_luns():
                log.debug("Building iGroups for LUN: %s", lun)
                for ig in site_igroups:
                    log.debug("checking match of exportlist: %s with %s", ig.get_exports(), lun.get_exports())
                    pass

                # Check to see if the exports in both lists are equivalent
                # This means that all of the exports in the igroup exportlist
                # are to the same host/ip, with the same permissions as the
                # lun's exportlist.
                matchedgroups = []
                for ig in site_igroups:
                    match = True
                    for a, b in zip(ig.get_exports(), lun.get_exports()):
                        if a != b:
                            match = False
                            pass
                        pass
                    if match is True:
                        matchedgroups.append(ig)
                    pass

                #matchedgroups = [ ig for ig in site_igroups if [ a == b for a,b in zip(ig.exportlist, lun.exportlist)] ]
                if len(matchedgroups) == 0:
                    log.debug("exportlist %s has not had a group created for it yet", lun.get_exports())
                    igroup_number = len(site_igroups)
                    log.debug("site is: %s", site)
                    ns = site.populate_namespace()
                    ns['igroup_number'] = igroup_number
                    igroup_name = defaults.get('igroup', 'igroup_name') % ns

                    # Add a list of one LUN to a brand new iGroup with this LUN's exportlist
                    # The iGroup type defaults the same as the first LUN type that it contains.
                    xmldata = """<igroup name="%s"/>""" % igroup_name
                    
                    #group = iGroup(igroup_name, lun.qtree.volume.filer, lun.exportlist, [lun,], type=lun.ostype)
                    group = iGroup()
                    group.configure_from_node( etree.fromstring(xmldata), defaults, site)
                    group.luns.append(lun)
                    group.exports = lun.get_exports()
                    lun.igroup = group
                    site_igroups.append(group)

                else:
                    log.debug("Aha! An iGroup with this exportlist already exists!")
                    if len(matchedgroups) > 1:
                        log.warning("Multiple iGroups exist for the same exportlist! This is a bug!")
                        log.warning("groups are: %s", matchedgroups)
                    group = matchedgroups[0]
                    log.debug("Appending LUN to iGroup %s", group.name)
                    if group.type != lun.ostype:
                        log.error("LUN type of '%s' is incompatible with iGroup type '%s'", lun.ostype, igroup.type)
                    else:
                        lun.igroup = group
                        group.luns.append(lun)
                    pass
                pass
            igroups.extend( site_igroups )
            pass
        return igroups

    def setup_manual_igroups(self):
        pass
    
    def get_host_qtree_mountoptions(self, host, qtree):
        """
        Find the mountoptions for a host for a specific qtree.
        This allows the system to automatically determine the
        mount options that a given host should use when mounting
        a qtree.
        It returns the additional mount options that are special
        for this qtree. It assumes that standard mount options, such
        as 'hard', will not be included in this list.
        """
        mountoptions = []
        osname = host.operatingsystem

        # always add read/write or read-only mount options, because
        # they're really important.
        if host in [ export.tohost for export in qtree.get_rw_exports() ]:
            #log.debug("Read/Write host")
            mountoptions.append('rw')

        if host in [ export.tohost for export in qtree.get_ro_exports() ]:
            #log.debug("Read-only host")
            mountoptions.append('ro')
            pass
        
        # See if there are any manually defined mount options for
        # the qtree, or volume the qtree lives in. Most specific wins.
        # If you specify mountoptions manually, you have to specify *all*
        # of them, or you'd risk the computer guessing what you meant,
        # and they usually get that wrong.. and then you have to wrestle with
        # the damn thing to get it to do what you mean.
        if qtree.qtreenode is not None:
            mountoptions.extend( self.get_extra_mountoptions(qtree.qtreenode, host) )
        elif qtree.volume.volnode is not None:
            mountoptions.extend( self.get_extra_mountoptions(qtree.volume.volnode, host) )

        # If you don't manually define mount options, use some sensible defaults
        else:
            
            if qtree.volume.type in [ 'oracm', 'oradata', 'oraindx', 'oraundo', 'oraarch', 'oraredo' ]:

                if osname.lower().startswith('solaris'):
                    #log.debug("Solaris mount option required")
                    mountoptions.extend( [ 'forcedirectio', 'noac', 'nointr' ] )

                elif osname.lower().startswith('linux'):

                    #log.debug("Linux mount option required")
                    mountoptions.extend( [ 'actimeo=0', ] )
                    pass

                else:
                    log.error("Unknown operating system '%s', cannot set mountoptions.", osname)
                    pass
                pass

            # Non Oracle volume options for Solaris
            elif osname.lower().startswith('solaris'):
                mountoptions.extend([ 'intr', ])

            elif osname.lower().startswith('linux'):
                mountoptions.extend([ 'intr', ])
                pass
            pass
        
        #log.debug("mountoptions are: %s", mountoptions)
        return mountoptions

    def get_extra_mountoptions(self, node, host):
        """
        Find any mountoptions defined at a node for a specific host
        """
        nodes = node.xpath("ancestor-or-self::*/export[@to = '%s']/mountoption" % host.name)
        if len(nodes) > 0:
            log.debug("Found %d manually defined mountoptions: %s", len(nodes), nodes)
            pass
        
        mountoptions = [ x.text for x in nodes ]
#        log.debug("returning mountoptions: %s", mountoptions)
        return mountoptions

    def get_iscsi_chap_password(self, prefix='docgen'):
        """
        Create the iSCSI CHAP password to use.
        """
        chap_password = '%s%s123' % (prefix, self.name)
        # The password has to be longer than 12 characters. If it isn't pad it with zeros
        if len(chap_password) < 12:
            chap_password  = chap_password + ( '0' * (12 - len(chap_password)) )

        # The password also has to be no longer than 16 characters. If it's shorter,
        # that's fine, this will still work.
        chap_password = chap_password[:16]
            
        return chap_password

    def setup_snapshots(self):
        """
        Set up the snapshots for all volumes that need them
        """
        pass

    def setup_snapmirrors(self, defaults):
        """
        Set up the snapmirrors for the volumes that need them
        """
        self.snapmirrors = []
        # Add snapmirror volumes for those source volumes with snapmirrorrefs
        for vol in self.get_volumes():
            self.create_snapmirrors_for(vol, defaults)
            pass

    def create_snapmirrors_for(self, srcvol, defaults):
        """
        Create snapmirror volumes for a source volume.
        """
        log.debug("Attempting to create snapmirror for srcvol: %s", srcvol)
        # get the snapmirrorset for the volume
        for ref in srcvol.get_snapmirror_setrefs():
            log.debug("Found reference: %s", ref)

            # Check that the reference refers to a defined snapmirrorset
            try:
                setobj = [ x for x in self.get_snapmirrorsets() if x.name == ref.name ][0]
            except IndexError:
                log.error("Cannot find snapmirrorset definition '%s'" % ref)
                raise KeyError("snapmirrorset not defined: '%s'" % ref)

            target_filername = setobj.targetfiler
            if target_filername is None:
                # No target filer specified, so use the first primary at a site other than the source
                # This auto-created DR snapmirrors, but may not be what you mean.
                target_filername = self.tree.xpath("site[not(@type = '%s')]/filer[@type = 'primary']/@name" % srcvol.filer.site.type)[0]
                log.warn("No destination for snapmirror provided, using '%s'" % target_filername)
                pass

            try:
                target_filer = [x for x in self.get_filers() if x.name == target_filername ][0]
                
            except IndexError:
                raise KeyError("Snapmirror target is an unknown filer name: '%s'" % target_filername)

            # Find the target aggregate.
            targetaggr = self.find_target_aggr(target_filer, setobj.targetaggregate, defaults)

            # target volume name is the src volume name with a 'r' suffix
            xmldata = """
<volume name="%s%s" type="snapmirrordst"
        usable="%s"
        raw="%s"
        snapreserve="%s"
        protocol="%s" />""" % ( srcvol.name,
                                setobj.targetsuffix,
                                srcvol.usable,
                                srcvol.raw,
                                srcvol.snapreserve,
                                srcvol.protocol,
                                )

            node = etree.fromstring(xmldata)
            targetvol = Volume()
            targetvol.configure_from_node(node, defaults, targetaggr)
            targetaggr.add_child(targetvol)
        
            log.debug("Created snapmirror targetvol: %s", targetvol)
            
            for sched in setobj.get_snapmirrorschedules():

                sm = SnapMirror(srcvol, targetvol,
                                sched.minute,
                                sched.hour,
                                sched.dayofmonth,
                                sched.dayofweek,
                                )
                
                self.snapmirrors.append(sm)
                log.debug("added snapmirror: %s", sm)
                pass

    def setup_snapvaults(self, defaults):
        """
        Set up the snapvaults for the volumes that need them
        """
        self.snapvaults = []
        # Add snapvault volumes for those source volumes with snapvaultrefs
        for vol in self.get_volumes():
            self.create_snapvaults_for(vol, defaults)
            pass

    def create_snapvaults_for(self, srcvol, defaults):
        """
        Create snapvault volumes for a source volume.
        """
        log.debug("Attempting to create snapvault for srcvol: %s", srcvol)
        # get the snapvaultset for the volume

        # If the volume is of certain types, don't back them up
#         if srcvol.type in ['oraredo', 'oracm' ]:
#             log.info("Not backing up volume '%s' of type '%s'", srcvol.name, srcvol.type)
#             return

        # Create target volumes based on the snapvault definition
        for ref in srcvol.get_snapvault_setrefs():
            log.debug("Found reference: %s", ref.name)
            try:
                log.debug("snapvaultsets: %s", [x.name for x in self.get_snapvaultsets()] )
                setobj = [ x for x in self.get_snapvaultsets() if x.name == ref.name ][0]
            except IndexError:
                raise KeyError("Cannot find snapvaultset definition '%s'" % ref.name)

            # If a target volume has been pre-defined, we'll use that.
            # Otherwise, we'll invent one based on certain rules and settings.
            target_filername = setobj.targetfiler
            try:
                target_filer = [x for x in self.get_filers() if x.name == target_filername ][0]
                
            except IndexError:
                raise KeyError("SnapVault target is an unknown filer name: '%s'" % target_filername)

            # If the target volume name is specified, use that
            if setobj.targetvolume is not None:
                try:
                    targetvol = [ x for x in target_filer.get_volumes() if x.name == setobj.targetvolume ][0]
                except IndexError:
                    raise KeyError("SnapVault targetvolume '%s' does not exist" % setobj.targetvolume)
                log.debug("Found specific volume: %s", targetvol)

                # Set the type of the volume to be a snapvault destination
                targetvol.type='snapvaultdst'
                pass
            
            # otherwise, invent a target volume, and use that instead
            else:
                # Find the target aggregate for the snapvault
                targetaggr = self.find_target_aggr(target_filer, setobj.targetaggregate, defaults)

                # Figure out how much usable storage to allocate to the target volume
                if setobj.targetusable is None:
                    # iSCSI is special, again. Grr.
                    if srcvol.protocol == 'iscsi':
                        setobj.targetusable = srcvol.iscsi_usable * setobj.multiplier
                    else:
                        log.debug("usable: %f", srcvol.usable)
                        log.debug("multiplier: %f", setobj.multiplier)
                        setobj.targetusable = srcvol.usable * setobj.multiplier
                    pass
                
                # target volume name is the src volume name with a 'b' suffix
                xmldata = """
<volume name="%s%s" type="snapvaultdst"
        usable="%s"
        raw="%s"
        snapreserve="%s"
        protocol="%s" />""" % ( srcvol.name,
                                setobj.targetsuffix,
                                setobj.targetusable,
                                setobj.targetusable,
                                0,
                                srcvol.protocol,
                                )
        
            node = etree.fromstring(xmldata)
            targetvol = Volume()
            targetvol.configure_from_node(node, defaults, targetaggr)
            targetaggr.add_child(targetvol)
            # end determination of target volume
            log.debug("Created snapvault targetvol: %s", targetvol)

            # If the target volume or aggregate are actually defined in
            # the XML, and use those settings for autosize and autodelete.
            #targetvol = self.set_volume_autosize(targetvol, targetvol.filer.name, targetvol.aggregate)
            #targetvol = self.set_volume_autodelete(targetvol, targetvol.filer.name, targetvol.aggregate)

            # Add the snapvaults themselves
            if len(setobj.get_snapvaultdefs()) == 0:
                log.warn("No snapvault defininitions provided for snapvaultset")
                pass
            
            log.debug("snapdefs: %s", setobj.get_snapvaultdefs() )
            for svdef in setobj.get_snapvaultdefs():

                sv = SnapVault(srcvol, targetvol,
                               svdef.basename,
                               svdef.snapschedule,
                               svdef.snapvaultschedule,
                               )
                #srcvol.snapvaults.append(sv)
                #targetvol.snapvaults.append(sv)                
                log.debug("Added snapvault: %s", sv)

            # Add snapmirrors of the snapvaults if the source volume has snapvaultmirrorrefs set
            #self.create_snapmirrors_for(targetvol)

    def find_target_aggr(self, targetfiler, aggrname, defaults):
        """
        Given a name, find the target aggregate in the config,
        or create a reference object if we just have a name
        """
        log.debug("Finding target aggregates...")
        try:
            targetaggr = [ x for x in targetfiler.get_aggregates() if x.name == aggrname ][0]
        except IndexError:
            # An indexerror means the aggregate isn't defined in the
            # project XML, which is ok. We invent an aggregate and
            # add it to the target filer.
            xmldata = """<aggregate name="%s" />""" % aggrname
            node = etree.fromstring(xmldata)
            targetaggr = Aggregate()
            targetaggr.configure_from_node(node, defaults, targetfiler)
            targetfiler.add_child(targetaggr)
            pass

        log.debug("Added a placeholder aggregate to project: %s", targetaggr)
        log.debug("%s", targetfiler.get_aggregates())
        return targetaggr
            
    def get_snapvaults(self):
        """
        Fetch all the snapvault relationships defined in the project.
        """
        return self.snapvaults

    def get_snapmirrors(self):
        """
        Fetch all the snapmirror relationships defined in the project.
        """
        return self.snapmirrors
