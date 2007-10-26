##

"""
Configuration of the Document Generator
"""
import re
import sys
import os
import textwrap

from lxml import etree

#from xml.parsers.expat import ParserCreate
#from xml.dom.minidom import Document, Text

import logging
import debug

log = logging.getLogger('docgen')

xinclude_re = re.compile(r'.*<xi:include href=[\'\"](?P<uri>.*)[\'\"].*')

FILER_TYPES = [
    'primary',
    'secondary',
    'nearstore',
    'dr_primary',
    'dr_secondary',
    'dr_nearstore',
    ]

class Revision:
    """
    A Revision is a particular revision of a document. A single
    document may have many revisions.
    """
    def __init__(self, majornum=0, minornum=0, date='', authorinitials='', revremark=''):
        self.majornum = majornum
        self.minornum = minornum
        self.date = date
        self.authorinitials = authorinitials
        self.revremark = revremark

        pass
    pass

class Host:
    """
    A host definition
    """
    def __init__(self, name, platform, os, location, storageip, description='', drhosts=[]):

        self.name = name
        self.platform = platform
        self.os = os
        self.location = location
        self.storageip = storageip
        self.description = description

        # drhosts is a reference to other hosts that will take on
        # this host's role in the event of a DR, and so they should
        # inherit the exports configuration for this host, but for the
        # DR targetvol of the snapmirrors for this host's volumes.
        self.drhosts = drhosts

        self.filesystems = []
        self.interfaces = []

        log.debug("Created host: %s, %s, %s", self.name, self.location, self.drhosts)

class Filesystem:

    def __init__(self, type, name):

        self.type = type
        self.name = name

class Interface:

    def __init__(self, switchname, switchport, vlan, ipaddress):

        self.switchname = switchname
        self.switchport = switchport
        self.vlan = vlan
        self.ipaddress = ipaddress

    def __repr__(self):
        return '<Interface %s:%s (vlan %s) %s>' % (self.switchname, self.switchport, self.vlan, self.ipaddress)

class NAS:

    def __init__(self, vlan, protocols=['NFS',]):

        self.vlan = vlan
        self.protocols = protocols
        self.filers = {}

class Filer:

    def __init__(self, name, type, site='primary'):
        self.name = name

        if type not in FILER_TYPES:
            raise ValueError("filer type '%s' not a known filer type", type)

        self.type = type
        self.site = site

        self.volumes = []
        self.vfilers = {}

        # If I am a secondary, who am I a secondary for?
        self.secondary_for = None

    def __str__(self):
        return '<Filer: %s (%s:%s)>' % (self.name, self.type, self.site)

    def as_string(self):
        """
        Dump out as a string.
        """
        retstr = '<Filer: %s (%s)' % ( self.name, self.type )

        if self.type == 'secondary':
            retstr += ' [secondary for %s]' % self.secondary_for
            pass

        retstr += '>\n'

        log.debug("vfilers: %s", self.vfilers)
        vfiler_strings = [ '  %s' % x.as_string() for x in self.vfilers.values() ]
        retstr += '\n'.join(vfiler_strings)
        return retstr

class VFiler:
    
    def __init__(self, filer, name, rootaggr, vlan, ipaddress, netmask, gateway):
        self.filer = filer
        self.name = name
        self.rootaggr = rootaggr
        self.vlan = vlan
        self.ipaddress = ipaddress
        self.netmask = netmask
        self.gateway = gateway
        self.volumes = []

        filer.vfilers[name] = self

    def as_string(self):
        """
        Dump vFiler config as a string
        """
        retstr = '<vFiler: %s, %s %s>' % (self.name, self.ipaddress, self.netmask)
        volume_strings = [ '  %s' % x for x in self.volumes ]
        return retstr

class Volume:

    def __init__(self, name, filer, aggr, usable, snapreserve=20, raw=None, type="fs", proto="nfs", voloptions=[], volnode=None, snapref=[], snapvaultref=[], snapmirrorref=[], snapvaultmirrorref=[]):
        self.name = name
        self.filer = filer
        self.type = type
        self.proto = proto
        self.aggregate = aggr
        self.usable = float(usable)

        if raw is None:
            raw = self.usable / ( (100 - float(snapreserve) )/100 )
        self.raw = raw

        self.snapreserve = snapreserve

        self.snapref = snapref
        self.snapvaultref = snapvaultref
        self.snapmirrorref = snapmirrorref
        self.snapvaultmirrorref = snapvaultmirrorref

        # Lists of the actual snapX objects, added when they're created
        self.snaps = []
        self.snapvaults = []
        self.snapmirrors = []

        self.qtrees = []

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
        
        #log.debug("Created: %s", self)

    def __str__(self):
        return '<Volume: %s:/vol/%s, %s, aggr: %s, size: %sg usable (%sg raw)>' % (self.filer.name, self.name, self.type, self.aggregate, self.usable, self.raw)

    def get_create_size(self):
        """
        Get the raw size in a format acceptable to the vol create command,
        ie: integer amounts, and the appropriate scale (0.02g == 20m)
        """
        # Figure out if the raw volume size is fractional.
        # NetApps won't accept fractional numbers for the vol create command,
        # so we convert it from the default gigabytes to megabytes.
        if 0 < float(self.raw) - int(self.raw) < 1:
            log.debug("Vol size %s is fractional gigabytes, using megabytes for create command", self.raw)
            # Note: This uses 1000 megabytes per gigabytes, which is not true.
            # It should be base 2, not base 10, == 1024, but most humans prefer base 10.
            size = round(self.raw * 1000)
            if size == 0:
                log.error("Volume size error: %s", self)
                raise ValueError("Attempting to create volume of size 0!")
            return '%dm' % size
        
        return '%dg' % round(self.raw)

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
    
class Qtree:

    def __init__(self, volume, qtree_name=None, security='unix', comment='', rwhostlist=[], rohostlist=[], mountoptions=[]):
        """
        NOTE: when creating the exportfs line, check to see if the host is in the rohostlist, and
        add a mountoption of 'ro' to its mountoptions list. Similar to the 'noac' specific thing
        for the Linux operating system, vs. Solaris.
        """
        self.volume = volume
        if qtree_name is None:
            qtree_name = 'data'
        
        self.name = qtree_name
        self.security = security
        self.comment = comment
        self.rwhostlist = rwhostlist
        self.rohostlist = rohostlist
        
        # Any additional mount options that may be required, over the base ones
        self.mountoptions = mountoptions

        log.debug("Created qtree: %s", self)

        self.volume.qtrees.append(self)

    def __str__(self):
        return '<Qtree: type: %s, %s, sec: %s, rw: %s, ro: %s>' % (self.name, self.volume.proto, self.security, self.rwhostlist, self.rohostlist)

class LUN:
    """
    A LUN lives in a Qtree and is used for iSCSI, predominantly.
    """

    lunid = 0

    def __init__(self, name, lunid, size, ostype, initlist, lunnode):

        self.name = name
        self.size = size
        self.ostype = ostype
        self.lunid = lunid
        self.lunnode = lunnode
        self.initlist = initlist
        
        self.igroup = None

        log.debug("Created lun: %s", self.name)

class Vlan:
    """
    A vlan defines the layer 2 network a vfiler belongs to, or a services vlan.
    """

    def __init__(self, number, gateway, site='primary', type='project', network='', netmask='', description='', node=None):

        self.site = site
        self.type = type
        self.number = number
        self.gateway = gateway
        self.network = network
        self.netmask = netmask
        self.description = description


        self.node = node

class iGroup:
    """
    An iGroup is a LUN mask for NetApp filers. It maps particular LUNs
    to the hosts (iSCSI initiators) that can access the LUNs.
    """

    def __init__(self, name, initlist=[], lunlist=[], type='windows'):
        self.name = name
        self.type = type
        self.initlist = initlist
        self.lunlist = lunlist

class Snapshot:
    """
    A Snapshot is a local snapshot backup.
    SnapVaults and SnapMirrors are different objects, defined below.
    """
    def __init__(self, sourcevol, numweekly, numdaily, hourly_schedule):
        self.sourcevol = sourcevol
        self.numweekly = numweekly
        self.numdaily = numdaily
        self.hourly_schedule = hourly_schedule

        self.sourcevol.snaps.append(self)

    def __str__(self):
        return '<Snapshot: %s -> %s, %s, %s>' % (self.sourcevol.namepath(),
                                                  self.targetvol.namepath(),
                                                  self.basename,
                                                  self.schedule,
                                                  )

class SnapVault:
    """
    A SnapVault is a special kind of snapshot that requires a baseline
    to be taken on the source volume, which is then transferred to a
    SnapVault secondary device at some later time.
    """

    def __init__(self, sourcevol, targetvol, basename, src_schedule, dst_schedule):

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

class SnapMirror:

    def __init__(self, sourcevol, targetvol, minute='*', hour='*', dayofmonth='*', dayofweek='*'):

        self.sourcevol = sourcevol
        self.targetvol = targetvol
        self.minute = minute
        self.hour = hour
        self.dayofmonth = dayofmonth
        self.dayofweek = dayofweek

        self.sourcevol.snapmirrors.append(self)
        self.targetvol.snapmirrors.append(self)

    def __str__(self):
        return '<SnapMirror: %s -> %s, %s>' % (self.sourcevol.namepath(),
                                                  self.targetvol.namepath(),
                                                  self.etc_snapmirror_conf_schedule(),
                                                  )
    def etc_snapmirror_conf_schedule(self):
        """
        Returns a string of the schedule part of the /etc/snapmirror.conf
        entry for this SnapMirror.
        """
        return '%s %s %s %s' % (self.minute, self.hour, self.dayofmonth, self.dayofweek)
        
class ProjectConfig:

    def __init__(self, configfile):
        """
        Create a ProjectConfig object based on a parsed configuration .xml definition file.

        This enables us to more easily represent the configuration as a set of objects,
        rather than an XML document.
        """
        self.tree = etree.parse(configfile)

        self.filers = {}
        self.volumes = []

        self.snapshots = []
        self.snapvaults = []
        self.snapmirrors = []
        self.allowed_protocols = []

        self.has_dr = False

        #self.verify_doc()

        self.load_project_details()

        # Define a series of attributes that a ProjectConfig can have.
        # These are all the things that are used by the documentation templates.

        self.primary_project_vlan = self.get_project_vlan('primary').number
        if self.has_dr:
            self.secondary_project_vlan = self.get_project_vlan('secondary').number

    def load_project_details(self):

        self.prefix = self.tree.xpath('//project/prefix')[0].text
        self.code = self.tree.xpath('//project/code')[0].text
        self.shortname = self.tree.xpath('//project/shortname')[0].text
        self.longname = self.tree.xpath('//project/longname')[0].text

        self.revlist = self.load_revisions()

        self.hosts = self.load_hosts()

        self.drhosts = []
        for host in self.hosts.values():
            for drhostname in host.drhosts:
                self.drhosts.append(self.hosts[drhostname])

        self.vlans = self.load_vlans()
                
        self.filers = self.load_filers()
        self.vfilers = self.load_vfilers()
        
        self.volumes = self.load_volumes()

        for vol in self.volumes:
            if vol.proto not in self.allowed_protocols and vol.proto is not None:
                self.allowed_protocols.append(vol.proto)

        self.qtrees = self.load_qtrees()



    def load_revisions(self):
        """
        Load all the document revisions into a list
        """
        revlist = []

        for element in self.tree.xpath('revhistory/revision'):
            majornumber = element.xpath('majornumber')[0].text
            minornumber = element.xpath('minornumber')[0].text
            date = element.xpath('date')[0].text
            authorinitials = element.xpath('authorinitials')[0].text
            remark = element.xpath('revremark')[0].text
            rev = Revision(majornumber, minornumber, date, authorinitials, remark)
            revlist.append(rev)

        return revlist

    def load_hosts(self):
        """
        Load all the hosts
        """
        hosts = {}
        hostnodes = self.tree.xpath('host')
        for node in hostnodes:

            # find some mandatory attributes
            hostname = node.attrib['name']
            
            host_attribs = {}
            for attrib in ['platform', 'operatingsystem', 'location']:
                try:
                    host_attribs[attrib] = node.find(attrib).text
                except AttributeError:
                    log.error("Cannot find host attribute '%s' for host '%s'", attrib, hostname)
                    raise

            try:
                storageip = node.find('storageip/ipaddr').text
            except AttributeError:
                log.error("Host has no defined storageip: %s", hostname)
                raise

            try:
                description = node.find('description')[0].text
            except IndexError:
                description = ''

            drhostnodes = node.findall('drhost')
            drhosts = [ host.attrib['name'] for host in drhostnodes ]
        
            hosts[hostname] = Host(hostname, platform=host_attribs['platform'],
                               os=host_attribs['operatingsystem'],
                               location=host_attribs['location'],
                               storageip=storageip,
                               description=description, drhosts=drhosts)
        return hosts

    def load_filers(self):
        """
        Create filer objects from configuration
        """
        filers = {}
        filernodes = self.tree.xpath("nas/site/filer")
        for node in filernodes:
            filername = node.attrib['name']
            sitetype = node.xpath("parent::*/@type")[0]

            if sitetype == 'secondary':
                self.has_dr = True

            filer = Filer(filername, node.attrib['type'], sitetype)
            filers[filername] = filer

            # figure out which filer this is a secondary for
            if filer.type == 'secondary':
                my_primary = node.xpath("preceding-sibling::filer")[0].attrib['name']
                filer.secondary_for = filers[my_primary]
            pass

        return filers

    def load_vfilers(self):
        """
        Create vfiler objects from configuration
        """
        vfilers = {}
        vfilernodes = self.tree.xpath("nas/site/filer/vfiler")
        for node in vfilernodes:
            try:
                name = node.attrib['name']
            except KeyError:
                name = self.shortname

            rootaggr = node.attrib['rootaggr']
                
            filername = node.xpath("parent::*/@name")[0]
            filer = self.filers[filername]
            try:
                vlan_num = node.xpath("ancestor::site/vlan/@number")[0]
                for v in self.vlans:
                    if v.type == 'project' and v.number == vlan_num and filer.site == v.site:
                        vlan = v
            except IndexError:
                log.error("Cannot find vlan number for %s" % filername )
                raise
            ipaddress = node.xpath("primaryip/ipaddr")[0].text
            netmask = node.xpath("primaryip/netmask")[0].text

            gateway = node.xpath("ancestor::site/vlan/@gateway")[0]

            vfilers[name] = VFiler(filer, name, rootaggr, vlan, ipaddress, netmask, gateway)
            
        return vfilers

    def load_volumes(self):
        """
        Create all the volumes in the configuration
        """

        volnodes = self.tree.xpath("nas/site/filer/vfiler/aggregate/volume | nas/site/filer/vfiler/aggregate/volumeset")

        # Add root volumes to the filers/vfilers
        self.add_root_volumes()

        # number volumes from 0
        volnum = 0
        for node in volnodes:
            if node.tag == 'volumeset':
                vols, volnum = self.create_volumeset(node, volnum)
                self.volumes.extend(vols)
            else:
                vol, volnum = self.create_volume(node, volnum)
                self.volumes.append(vol)
                
        # Add snapshots for those source volumes with snaprefs
        for vol in self.volumes:
            self.create_snapshot_for(vol)

        # Add snapmirror volumes for those source volumes with snapmirrorrefs
        for vol in [ x for x in self.volumes if len(x.snapmirrorref) > 0 ]:
            self.create_snapmirror_for(vol)

        # Add snapvault volumes for those source volumes with snapvaultrefs
        # This will snapvault the secondary root volumes to the secondary nearstore
        for vol in [ x for x in self.volumes if len(x.snapvaultref) > 0 ]:
            #log.debug("Adding snapvault for: %s", vol)
            self.create_snapvault_for(vol)

        return self.volumes

    def add_root_volumes(self):
        """
        Create root volumes for all filers.
        """
        # Create root volumes for defined vfilers

        # Always have a root volume on the primary filers
        for filer in [ x for x in self.filers.values() if x.type == 'primary' ]:
            for vfiler in filer.vfilers.values():
                log.debug("Adding root volume for vfiler '%s' on '%s'...", vfiler.name, filer.name)
                snapref = []
                # The expected name of the snapvault schedule for root volumes
                # is default_primary or default_secondary
                snapvaultref = ['default_%s' % filer.site]

                # We don't snapmirror root volumes
                snapmirrorref = []

                vol = Volume('%s_root' % self.shortname,
                             filer,
                             vfiler.rootaggr,
                             usable=0.02,
                             raw=0.02,
                             snapreserve=20,
                             snapref=snapref,
                             snapvaultref=snapvaultref,
                             snapmirrorref=snapmirrorref,
                             )
                self.volumes.append(vol)
                pass
        
        # Always have a root volume on the nearstores
        for filer in [ x for x in self.filers.values() if x.type == 'nearstore' ]:
            for vfiler in filer.vfilers.values():
                log.debug("Adding root volume for vfiler '%s' on '%s'...", vfiler.name, filer.name)

                snapref = []
                snapvaultref = []
                snapmirrorref = []

                vol = Volume('%s_root' % self.shortname,
                             filer,
                             vfiler.rootaggr,
                             usable=0.02,
                             raw=0.02,
                             snapreserve=20,
                             snapref=snapref,
                             snapvaultref=snapvaultref,
                             snapmirrorref=snapmirrorref,
                             )
                self.volumes.append(vol)
                pass
            pass
        pass
    
    def load_qtrees(self, site='primary'):
        """
        Build the qtrees for the configuration.
        """
        qtree_list = []
        vols = [ vol for vol in self.volumes if vol.filer.site == site and vol.type not in [ 'snapvaultdst', 'snapmirrordst' ] ]

        for vol in vols:

            # If no volnode exists for the volume, this is an automatically generated volume
            if vol.volnode is None:
                # If this is the root volume, don't create qtrees
                if vol.name.endswith('root'):
                    continue

                # otherwise, we only create 1 qtree per volume, by default
                # FIXME: include determination of qtree name due to databases
                else:
                    log.warn("No volume node available for: %s", vol)
                    qtree = Qtree(vol, rwhostlist=self.hosts.values() )
                    qtree_list.append(qtree)
                    pass
                pass
            else:
                # There is a volume node, so we use it to look for qtree
                # definitions, which must be a child-element of the <volume/> node.
                
                # If there are qtrees defined, use their definitions.
                # This allows for more than one qtree per volume, if required.
                qtree_nodes = vol.volnode.xpath("qtree")
                if len(qtree_nodes) > 0:
                    #log.debug("Processing qtree nodes: %s", qtree_nodes)
                    for qtree_node in qtree_nodes:
                        try:
                            name = qtree_node.xpath("@name")[0]
                            qtree_name = '%s' % name
                        
                        except IndexError:
                            log.info("Qtree has no name, using 'data'.")
                            qtree_name = 'data'

                        try:
                            qtree_security = qtree_node.xpath("@security")[0]
                        except IndexError:
                            qtree_security = 'unix'
                            pass

                        if qtree_node.text is None:
                            qtree_comment = ''
                        else:
                            qtree_comment = qtree_node.text

                        # Find any mount options we need
                        mountoptions = qtree_node.xpath("mountoption")

                        rwhostlist, rohostlist = self.get_export_hostlists(qtree_node)
                        
##                         log.error("Host named '%s' not defined" % hostname)
##                         raise ValueError("Attempt to export qtree to non-existant host: '%s'" % hostname)

                        qtree = Qtree(vol, qtree_name, qtree_security, qtree_comment, rwhostlist, rohostlist)
                        qtree_list.append(qtree)

                else:
                    log.debug("No qtrees defined. Inventing them for this volume.")
                    
                    # If no qtrees are defined, invent one
                    if vol.type.startswith('ora'):
                        #log.info("Oracle volume type detected.")
                        # Build oracle qtrees

                        # We always number from 1
                        sid_id = 1

                        # Find the SID for the database this volume is for
                        # Oracle RAC quorum volume doesn't refer to a specific database
                        try:
                            sid=vol.volnode.xpath("@oracle")[0]

                            # Then find the list of hosts the database is on
                            onhost_nodes = self.tree.xpath("database[@id = '%s']/onhost" % sid)
                            rwhostlist = []
                            rohostlist = []
                            for hostname in [ x.text for x in onhost_nodes ]:
                                rwhostlist.append(self.hosts[hostname])
                                pass

                        except IndexError:
                            rwhostlist, rohostlist = self.get_export_hostlists(vol.volnode)

                        # If the hostlist is empty, assume qtrees are available to all hosts
                        if len(rwhostlist) == 0 and len(rohostlist) == 0:
                            rwhostlist = self.hosts.values()
                            
                        if vol.type == 'oraconfig':
                            qtree_name = 'ora_config'
                            qtree = Qtree(vol, qtree_name, 'unix', 'Oracle configuration qtree', rwhostlist=rwhostlist, rohostlist=rohostlist)
                            qtree.mountoptions = self.get_qtree_mountoptions(qtree)
                            qtree_list.append(qtree)

                        elif vol.type == 'oracm':
                            qtree_name = 'ora_cm'
                            qtree = Qtree(vol, qtree_name, 'unix', 'Oracle quorum qtree', rwhostlist=rwhostlist, rohostlist=rohostlist)
                            qtree.mountoptions = self.get_qtree_mountoptions(qtree)
                            qtree_list.append(qtree)

                        else:
                            # qtree name is the voltype with the 'ora' prefex stripped off
                            qtree_name = 'ora_%s_%s%02d' % ( sid, vol.type[3:], sid_id)
                            comment = 'Oracle %s qtree' % vol.type[3:]

                            qtree = Qtree(vol, qtree_name, 'unix', comment, rwhostlist=rwhostlist, rohostlist=rohostlist)
                            qtree.mountoptions = self.get_qtree_mountoptions(qtree)
                            qtree_list.append(qtree)

                            #
                            # If this is an oratemp volume, it contains both an ora_temp qtree
                            # and an ora_undo area to hold the undo (rollback) segment.
                            #
                            if vol.type == 'oratemp':
                                qtree_name = 'ora_%s_undo%02d' % ( sid, sid_id )
                                comment = 'Oracle undo (rollback) qtree'
                                qtree = Qtree(vol, qtree_name, 'unix', comment, rwhostlist=rwhostlist, rohostlist=rohostlist)
                                qtree.mountoptions = self.get_qtree_mountoptions(qtree)
                                qtree_list.append(qtree)

                    else:
                        # Figure out the hostlist by checking for volume based export definitions
                        rwhostlist, rohostlist = self.get_export_hostlists(vol.volnode)                        

                        qtree = Qtree(vol, rwhostlist=rwhostlist, rohostlist=rohostlist)
                        qtree.mountoptions = self.get_qtree_mountoptions(qtree)
                        qtree_list.append(qtree)
                    pass
                pass

            # Check to see if we need to export the DR copy of the qtrees to the
            # dr hosts.
            # If this volume is snapmirrored, give any drhosts the same export
            # permissions at the remote side as they do on the local side
            if len(vol.snapmirrors) > 0:

                for qtree in vol.qtrees:
                    dr_rwhostlist = []
                    dr_rohostlist = []

                    # Add rw drhosts for the qtree
                    for host in qtree.rwhostlist:
                        dr_rwhostlist.extend([ self.hosts[hostname] for hostname in host.drhosts ])
                        pass

                    for host in qtree.rohostlist:
                        dr_rohostlist.extend([ self.hosts[hostname] for hostname in host.drhosts ])
                        pass

                    # If either list is not empty, we need to create a Qtree on the
                    # snapmirror target volume with appropriate exports
                    if len(dr_rwhostlist) > 0 or len(dr_rohostlist) > 0:
                        log.debug("qtree '%s:%s' needs to be exported at DR", qtree.volume.name, qtree.name)

                        # Create one remote qtree for each snapmirror relationship
                        for snapmirror in vol.snapmirrors:
                            log.debug("Adding remote exported qtree on targetvol: %s", snapmirror.targetvol.name)
                            mirrored_qtree = Qtree( snapmirror.targetvol,
                                                    qtree.name,
                                                    qtree.security,
                                                    qtree.comment,
                                                    dr_rwhostlist,
                                                    dr_rohostlist,
                                                    qtree.mountoptions,
                                                    )
                            qtree_list.append(mirrored_qtree)
                            pass
                        pass
                    else:
                        log.debug("No hosts for qtree '%s' have corresponding DR hosts. Not exporting at DR.", qtree.name)
                    pass
                pass
            pass

        return qtree_list

    def get_qtree_mountoptions(self, qtree):
        """
        Figure out the automatically defined mount options for a qtree
        """
        mountoptions = []

        osname = qtree.rwhostlist[0].os
        
        if qtree.volume.type in ['oracm', ]:
            log.debug("Oracle quorum qtree detected.")
            if qtree.name == 'ora_cm':
                if osname.startswith('Solaris'):
                    log.debug("NOAC mount option added.")
                    mountoptions = [ 'forcedirectio', 'noac', 'nointr' ]
                    pass
                pass
            pass
        pass

        if qtree.volume.type in [ 'oradata', 'oraindx', 'oratemp', 'oraarch', 'oraredo' ]:

            if osname.startswith('Solaris'):
                #log.debug("Solaris mount option required")
                mountoptions = [ 'forcedirectio', 'noac', 'nointr' ]
                
            elif osname.startswith('Linux'):
                #log.debug("Linux mount option required")
                mountoptions = [ 'actimeo=0', ]
                pass

            else:
                log.error("Unknown operating system")
                mountoptions = []
                pass
            pass

        # Non Oracle volume options for Solaris
        elif osname.startswith('Solaris'):
            mountoptions = [ 'intr', ]

        elif osname.startswith('Linux'):
            mountoptions = [ 'intr', ]

        return mountoptions

    def load_vlans(self):
        """
        Load all the vlan definitions
        """
        vlans = []
        vlan_nodes = self.tree.xpath("nas/site/vlan")
        for node in vlan_nodes:

            site = node.xpath("ancestor::site/@type")[0]
            
            type = node.xpath("@type")[0]

            number = node.xpath("@number")[0]
            gateway = node.xpath("@gateway")[0]
            try:
                network = node.xpath("@network")[0]
            except IndexError:
                if type == 'project':
                    network = ''
                else:
                    log.error("Non project VLANs must have a network number defined.")
                    raise
                pass
            
            try:
                netmask = node.xpath("@netmask")[0]
            except IndexError:
                if type == 'project':
                    netmask = ''
                else:
                    log.error("Non project VLANs must have a netmask defined.")
                    raise
                pass

            # FIXME: Add the ability to add a description
            description = node.text
            if description is None:
                description = ''
            #site = 'primary'
            
            vlan = Vlan(number, gateway, site, type, network, netmask, description, node)
            vlans.append(vlan)
            pass

        return vlans

    def verify_doc(self, configdoc):
        """
        Make sure that the document satisfies certain rules.
        """
        # Check that the parent node is a <project> node.
        pass

    def get_volumes(self, site='primary', filertype='primary'):
        """
        Build a list of all the primary volumes for the project.
        """
        volumes = [ vol for vol in self.volumes if vol.filer.site == site and vol.filer.type == filertype ]
        log.debug("Found %d volumes for %s/%s", len(volumes), site, filertype)
        return volumes

    def create_volume(self, node, volnum):
        """
        Create a volume, using certain defaults as required.
        """
        # Find out which filer the volume is on
        filername = node.xpath("ancestor::filer/@name")[0]

        # Work out the volume name
        try:
            # If the volume has an explicit name set, use that
            volname = node.xpath("@name")[0]
        except IndexError:

            # otherwise, invent one

            # Try to find a volume prefix
            try:
                volprefix = node.xpath("@prefix")[0]
            except IndexError:
                volprefix = self.shortname
                pass

            # Try to find a volume suffix
            try:
                volsuffix = node.xpath("@suffix")[0]
            except IndexError:
                volsuffix = ''
                pass

            volname = '%s_vol%02d%s' % (volprefix, volnum, volsuffix)

        # aggregate is this one, or the same as the previous volume
        aggr = node.xpath("ancestor::aggregate/@name | preceding-sibling/ancestor::aggregate/@name")[0]

        snapref = node.xpath("snapsetref/@name")
        snapvaultref = node.xpath("snapvaultsetref/@name")
        snapmirrorref = node.xpath("snapmirrorsetref/@name")
        snapvaultmirrorref = node.xpath("snapvaultmirrorsetref/@name")

        try:
            usable = node.xpath("usablestorage")[0].text
        except IndexError:
            log.warn("No usable size specified for volume number '%02d'. Assuming minimum of 100 GiB usable.", volnum)
            usable = 100
            pass
        
        voloptions = [ x.text for x in node.xpath("option") ]

        try:
            proto = node.xpath("@proto")[0]
        except IndexError:
            proto = 'nfs'

        try:
            voltype = node.xpath("@type")[0]
        except IndexError:
            voltype = 'fs'

        # Default snap reserve to 20 unless specified otherwise
        try:
            snapreserve = node.xpath("@snapreserve")[0]
        except IndexError:
            #log.debug("No snapreserve specified.")
            if voltype == 'iscsi':
                snapreserve = 0
            elif voltype in ['oratemp', 'oraarch', ]:
                snapreserve = 50
            else:
                snapreserve = 20
                pass
            pass
            
        vol = Volume( volname, self.filers[filername], aggr, usable, snapreserve, type=voltype, proto=proto, voloptions=voloptions, volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref)
        volnum += 1
        return vol, volnum
    
    def create_volumeset(self, node, volnum):
        """
        Given a volumeset node, create a list of volumes from it.
        """
        vols = []

        filername = node.xpath("ancestor::filer/@name")[0]
        vol_filer = self.filers[filername]
        # aggregate is this one, or the same as the previous volume
        aggr = node.xpath("ancestor::aggregate/@name | preceding-sibling/ancestor::aggregate/@name")[0]

        snapref = node.xpath("snapsetref[not(@archivelogs)]/@name")
        snapvaultref = node.xpath("snapvaultsetref[not(@archivelogs)]/@name")
        snapmirrorref = node.xpath("snapmirrorsetref[not(@archivelogs)]/@name")
        snapvaultmirrorref = node.xpath("snapvaultmirrorsetref[not(@archivelogs)]/@name")

        if node.attrib.has_key('oracle'):

            #
            # Automated Oracle volume allocation is based on the following rules:
            # - The amount of usable storage for the volumeset is the total
            #   amount of usable storage for all the volumes. If 100g usable
            #   is specified, this equates to 20g data, 20g index, 10g archive, etc.
            #   depending on the percentage per volume in effect at the time.
            # - Each volume in the volumeset is sized as a percentage of the total
            #   usable storage. The data volume is 30% of total, for example, and
            #   the archive is 15% of total.
            # - The snap reserve for each volume may be different, since the
            #   archive data is likely to change a great deal, whereas the data isn't
            #   as likely to change.

            #
            # Because of the way backups work with Oracle, we often want to
            # backup the archivelogs after we backup the main data. This code
            # detects a special kind of snap/vault/mirror reference for the
            # archivelogs, if we want one. If we don't, the archivelogs volume
            # will just use the same ones as the other volumes.
            #
            #arch_snapref = node.xpath("snapsetref[@archivelogs]/@name")

            arch_snapvaultref = node.xpath("snapvaultsetref[@archivelogs]/@name")
            if len(arch_snapvaultref) == 0:
                arch_snapvaultref = snapvaultref
                # Warn the user if they aren't specifying an archivelog specific schedule.
                if len(snapvaultref) > 0:
                    log.warn("No archivelog specific snapvault defined for database '%s'.", node.attrib['oracle'])
            
            #arch_snapmirrorref = node.xpath("snapmirrorsetref[@archivelogs]/@name")

            sid = node.attrib['oracle']

            #
            # Find how much usable storage we want for the database.
            # We can do this in a couple of ways:
            # 1. We can use the total usable storage method, in which we define
            #    how much storage in total we wish to use, and it gets split up
            #    using a standard percentage for each volume, or
            # 2. We use the datastorage method, which takes the amount of storage
            #    required for the data volume, and figures out how much is
            #    needed for the index, archive, etc. based on standard percentages.

            try:
                datastorage = float(node.xpath("datastorage")[0].text)
                usable = datastorage * (1/0.4)
                #log.info("Total usable database storage: %s", usable)

            except IndexError:
                usable = float(node.xpath("usablestorage")[0].text)                

            # config and quorum volume
            # This is shared between all databases for the project, and is a constant size
##             volname = '%s_vol%02d' % ( self.shortname, volnum )
##             vol = Volume( volname, vol_filer, aggr, 100, 20, type='oraconfig', volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref)
##             vols.append(vol)
##             volnum += 1

            # data volume, 40% of total
            volname = '%s_vol%02d' % ( self.shortname, volnum )
            vol = Volume( volname, vol_filer, aggr, usable * 0.4, 20, type='oradata', volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref)
            vols.append(vol)
            volnum += 1

            # index volume, 20% of total
            volname = '%s_vol%02d' % ( self.shortname, volnum )
            vol = Volume( volname, vol_filer, aggr, usable * 0.2, 20, type='oraindx', volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref)
            vols.append(vol)
            volnum += 1

            # redo volume, constant size, no snapreserve
            volname = '%s_vol%02d' % ( self.shortname, volnum )
            vol = Volume( volname, vol_filer, aggr, usable * 0.05, 0, type='oraredo', volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref)
            vols.append(vol)
            volnum += 1

            # temp volume, 5% of total, no snapreserve
            volname = '%s_vol%02d' % ( self.shortname, volnum )
            vol = Volume( volname, vol_filer, aggr, usable * 0.20, 0, type='oratemp', volnode=node, snapref=snapref, snapvaultref=snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref)
            vols.append(vol)
            volnum += 1

            # archive volume, 35% of total
            volname = '%s_vol%02d' % ( self.shortname, volnum )
            vol = Volume( volname, vol_filer, aggr, usable * 0.35, 50, type='oraarch', volnode=node, snapref=snapref, snapvaultref=arch_snapvaultref, snapmirrorref=snapmirrorref, snapvaultmirrorref=snapvaultmirrorref)
            vols.append(vol)
            volnum += 1

        return vols, volnum

    def get_volume_totals(self, vol_list):
        usable_total = sum( [ vol.usable for vol in vol_list ])
        raw_total = sum( [ vol.raw for vol in vol_list ])
        return usable_total, raw_total

    def get_nearstore_volumes(self, ns, site='primary'):
        """
        Fetch all the nearstore volumes at site 'site'
        """
        volumes = [ vol for vol in self.volumes if vol.filer.site == site and vol.filer.type == 'nearstore' ]
        log.debug("nearstore volumes: %s", volumes)

        return volumes
    
    def get_dr_volumes(self, ns, source='primary'):
        """
        Automatically determine the DR site volume setup.
        This handles both DR of primary volumes, and also of NearStore volumes,
        as both are copied to the remote site via SnapMirror.
        FIXME: If there are any special differences in offsiting of
        volumes for DR or offsite backup, they will need to be catered for here.
        """
        volumes = [ vol for vol in self.volumes if vol.filer.site == 'secondary' and vol.filer.type == 'primary' ]
        log.debug("dr volumes: %s", volumes)
        return volumes

    def get_site_qtrees(self, ns, site='primary'):
        """
        Fetch the list of qtrees for a given site. These will be linked
        to the specific volume they are on.
        """
        qtrees = [ x for x in self.qtrees if x.volume.filer.site == site ]
        return qtrees

    def get_site_iscsi_igroups(self, ns, site='primary'):
        """
        Fetch the iSCSI iGroups for a site
        """
        if hasattr(self, 'igroups'):
            return self.igroups
        
        igroups = []
        lunlist = []
        
        vols = [ x for x in self.get_volumes(site, 'primary') if x.type == 'iscsi' ]
        for vol in vols:
            log.debug("iSCSI vol: %s", vol)

            # If a volume has multiple LUNs defined, put each one in its own
            # qtree, unless they are defined within qtrees, in which case,
            # use the exact layout that is specified in the config file.

            # check to see if any LUN nodes are defined.
            luns = vol.volnode.xpath("descendant-or-self::lun")

            if len(luns) > 0:
                log.debug("found lun nodes: %s", luns)

                # If you specify LUN sizes, the system will use exactly
                # what you define in the config file.
                # If you don't specify the LUN size, then the system will
                # divide up however much storage is left in the volume evenly
                # between the number of LUNs that don't have a size specified.

                lun_total = 0
                
                # Define all the LUNs that have sizes specified
                for lunnode in vol.volnode.xpath("descendant-or-self::lun[@size]"):
                    lunsize = float(lunnode.xpath("@size")[0])
                    log.info("Allocating %sg storage to LUN", lunsize)
                    lun_total += lunsize

                    lunid = len(lunlist)

                    initlist = self.get_iscsi_initiators(lunnode)

                    # We use the hostname component of the first entry in the initiator list
                    # to name the lun if a lun name is not specified.
                    try:
                        lunname = lunnode.xpath("@name")[0]
                    except IndexError:
                        lunname = '%s_%s_lun%02d.lun' % (ns['vfiler_name'], initlist[0][0], lunid)

                    # The LUN ostype defaults to the same type as the first one in its initiator list
                    lunlist.append( LUN( lunname, lunid, lunsize, initlist[0][2], initlist, lunnode) )

                for lunnode in vol.volnode.xpath("descendant-or-self::lun[not(@size)]"):
                    lunsize = ( vol.usable - lun_total) / len(vol.volnode.xpath("descendant-or-self::lun[not(@size)]"))
                    log.info("calculated lun size of: %s", lunsize)

                    lunid = len(lunlist)
                    
                    initlist = self.get_iscsi_initiators(lunnode)

                    try:
                        lunname = lunnode.xpath("@name")[0]
                    except IndexError:
                        lunname = '%s_%s_lun%02d.lun' % (ns['vfiler_name'], initlist[0][0], lunid)

                    lunlist.append( LUN( lunname, lunid, lunsize, initlist[0][2], initlist, lunnode) )
                pass

            pass

        # For each LUN in the lunlist, create an iGroup for its initlist.
        # If multiple LUNs are exported to the same initlist, they are
        # exported to the same iGroup, so a new one is not created.

        self.lunlist = lunlist

        for lun in lunlist:
            if lun.initlist not in [ x.initlist for x in igroups ]:
                log.debug("initlist %s has not had a group created for it yet", lun.initlist)
                igroup_name = '%s_%s_igroup%02d' % ( ns['vfiler_name'], lun.initlist[0][0], len(igroups) )

                # Add a list of one LUN to a brand new iGroup with this LUN's initlist
                # The iGroup type defaults the same as the first LUN type that it contains.
                group = iGroup(igroup_name, lun.initlist, [lun,], type=lun.ostype)
                lun.igroup = group
                igroups.append(group)
                
            else:
                log.debug("Aha! An iGroup with this initlist already exists!")
                for group in igroups:
                    if group.initlist == lun.initlist:
                        log.info("Appending LUN to iGroup %s", group.name)
                        if group.type != lun.ostype:
                            log.error("LUN type of '%s' is incompatible with iGroup type '%s'", lun.ostype, igroup.type)
                        else:
                            lun.igroup = group
                            group.lunlist.append(lun)
                        break
                    pass
                pass
            pass

        self.igroups = igroups
        return igroups

    def get_iscsi_initiators(self, node):
        """
        Given a node, look for <export to=/> nodes and then look up
        the initiator name for the given host that is listed as
        the export destination for the iSCSI LUN.
        The node may be a volume, qtree or LUN; this is used to group
        all export definitions at the same level into the same iGroup.

        If no export definitions exist as a descendent node, find any
        ancestor nodes that have an export definition.
        """
        log.debug("finding initiators for LUN: %s", node.xpath("@name"))
        initlist = []
        exports = self.get_export_nodes(node)

        for export in exports:
            hostname = export.xpath("@to")[0]
            initname = self.tree.xpath("host[@name = '%s']/iscsi_initiator" % hostname)[0].text
            operatingsystem = self.tree.xpath("host[@name = '%s']/operatingsystem" % hostname)[0].text
            if operatingsystem.startswith('Solaris'):
                ostype = 'Solaris'
            elif operatingsystem.startswith('Windows'):
                ostype = 'Windows'
            else:
                log.error("Operating system '%s' is not supported for iSCSI", operatingsystem)

            initlist.append((hostname,initname,ostype))
            pass

        log.debug("initators: %s", initlist)        
        return initlist

    def get_export_nodes(self, node):
        """
        Find export nodes that are children of the current node.
        This recurses upwards to the parent node if it can't find any exports.
        """
        exports = node.xpath("export")
        if len(exports) == 0:
            log.info("No export definitions for this node %s. Using parent exports.", node)
            try:
                parent_node = node.xpath("parent::*")[0]
            except IndexError:
                return []
            return self.get_export_nodes(parent_node)
        else:
            log.debug("found exports: %s", [x.xpath("@to")[0] for x in exports ])
            return exports

    def get_export_hostlists(self, node):
        """
        Find the list of hosts for read/write and readonly mode based
        on the particular qtree or volume node supplied.
        """
        rohostnames = node.xpath("ancestor-or-self::*/export[@ro = 'yes']/@to")
        log.debug("rohostnames for %s: %s", node, rohostnames)

        rwhostnames = node.xpath("ancestor-or-self::*/export[@ro != 'yes']/@to | ancestor-or-self::*/export[not(@ro)]/@to")
        log.debug("rwhostnames for %s: %s", node, rwhostnames)

        rwhostlist = [ self.hosts[hostname] for hostname in rwhostnames ]
        rohostlist = [ self.hosts[hostname] for hostname in rohostnames ]

        # If both lists are empty, default to exporting read/write to all hosts
        if len(rwhostlist) == 0 and len(rohostlist) == 0:
            rwhostlist = self.hosts.values()
        
        return rwhostlist, rohostlist

    def get_cifs_exports(self):
        """
        Find the CIFS exports for the project.
        """
        return []

    def create_snapshot_for(self, srcvol):
        """
        Create snapshot definitions for volumes, if they have a snapref.
        root volumes have a default snapshot schedule added if they have
        no snapref.
        """
        if len(srcvol.snapref) > 0:
            log.warn("Snapref addition not supported yet.")
            raise NotImplementedError("Snaprefs not yet supported.")

        # Add default snapshot schedule for root volumes
        elif srcvol.name.endswith('root'):
            self.snapshots.append( Snapshot( srcvol, 0, 0, '6@8,12,16,20') )

    def create_snapvault_for(self, srcvol):
        """
        Create snapvault volumes for a source volume.
        """
        #log.debug("Adding snapvaults for %s", srcvol)
        # get the snapvaultset for the volume

        # If the volume is of certain types, don't back them up
        if srcvol.type in ['oratemp', 'oraredo', 'oracm' ]:
            log.info("Not backing up volume '%s' of type '%s'", srcvol.name, srcvol.type)
            return
        
        for ref in srcvol.snapvaultref:
            try:
                set_node = self.tree.xpath("snapvaultset[@id = '%s']" % ref)[0]
            except IndexError:
                log.error("Cannot find snapvaultset definition '%s'" % ref)
                raise ValueError("snapvaultset not defined: '%s'" % ref)

            try:
                target_filername = set_node.attrib['targetfiler']
            except KeyError:
                # No target filer specified, so use the first nearstore at the same site as the primary
                target_filername = self.tree.xpath("nas/site[@type = '%s']/filer[@type = 'nearstore']/@name" % srcvol.filer.site)[0]
                pass

            try:
                target_filer = self.filers[target_filername]
            except KeyError:
                log.error("Snapvault target is an unknown filer name: '%s'", target_filername)
                raise
                
            try:
                targetaggr = set_node.attrib['targetaggregate']
            except:
                try:
                    targetaggr = self.tree.xpath("nas/site/filer[@name = '%s']/aggregate/@name" % target_filername)[0]
                except:
                    # No aggregates are specified on the target filer, so use the same one as the source volume
                    targetaggr = srcvol.aggregate
                    pass
                pass

            # target volume name is the src volume name with a 'b' suffix
            targetvol = Volume( '%sb' % srcvol.name,
                                self.filers[target_filername],
                                targetaggr,
                                srcvol.usable * 2.5,
                                snapreserve=0,
                                type='snapvaultdst',
                                proto=None,
                                snapmirrorref=srcvol.snapvaultmirrorref,
                                )
            self.volumes.append(targetvol)
            #log.debug("target volume filer type: %s", targetvol.filer.type)
            
            for svnode in set_node.findall("snapvault"):
                basename = svnode.attrib['basename']
                snapsched = svnode.find('snapschedule')
                svsched = svnode.find('snapvaultschedule')

                sv = SnapVault(srcvol, targetvol, basename, snapsched.text, svsched.text)
                self.snapvaults.append(sv)
                #log.debug("Added snapvault: %s", sv)

            # Add snapmirrors of the snapvaults if the source volume has snapvaultmirrorrefs set
            self.create_snapmirror_for(targetvol)

    def create_snapmirror_for(self, srcvol):
        """
        Create snapmirror volumes for a source volume.
        """
        # If the volume is of certain types, don't back them up
        if srcvol.type in [ 'oracm' ]:
            log.info("Not snapmirroring volume '%s' of type '%s'", srcvol.name, srcvol.type)
            return

        # get the snapmirrorset for the volume
        for ref in srcvol.snapmirrorref:
            try:
                set_node = self.tree.xpath("snapmirrorset[@id = '%s']" % ref)[0]
            except IndexError:
                log.error("Cannot find snapmirrorset definition '%s'" % ref)
                raise ValueError("snapmirrorset not defined: '%s'" % ref)

            try:
                target_filername = set_node.attrib['targetfiler']
                
            except KeyError:
                # No target filer specified, so use the first primary at a site other than the source
                # This auto-created DR snapmirrors, but may not be what you mean.
                target_filername = self.tree.xpath("nas/site[not(@type = '%s')]/filer[@type = 'primary']/@name" % srcvol.filer.site)[0]
                log.warn("No destination for snapmirror provided, using '%s'" % target_filername)
                pass

            try:
                target_filer = self.filers[target_filername]
                
            except KeyError:
                log.error("Snapmirror target is an unknown filer name: '%s'", target_filername)
                raise
                
            try:
                targetaggr = set_node.attrib['targetaggregate']
            except:
                try:
                    targetaggr = self.tree.xpath("nas/site/filer[@name = '%s']/aggregate/@name" % target_filername)[0]
                except:
                    # No aggregates are specified on the target filer, so use the same one as the source volume
                    targetaggr = srcvol.aggregate
                    pass
                pass

            # target volume name is the src volume name with a 'r' suffix
            targetvol = Volume( '%sr' % srcvol.name,
                                self.filers[target_filername],
                                targetaggr,
                                srcvol.usable,
                                snapreserve=srcvol.snapreserve,
                                raw=srcvol.raw,
                                type='snapmirrordst',
                                proto=srcvol.proto,
                                voloptions=srcvol.voloptions,
                                )
            self.volumes.append(targetvol)
            
            snapmirror_schedule = {}
            for svnode in set_node.findall("snapmirror"):

                # Find the parameters for snapmirror schedules, defaulting to '*'
                # if a parameter is not set.
                for nodename in ['minute', 'hour', 'dayofmonth', 'dayofweek']:
                    node = svnode.find(nodename)
                    try:
                        snapmirror_schedule[nodename] = node.text
                    except AttributeError, e:
                        snapmirror_schedule[nodename] = '*'
                    
                sm = SnapMirror(srcvol, targetvol,
                                snapmirror_schedule['minute'],
                                snapmirror_schedule['hour'],
                                snapmirror_schedule['dayofmonth'],
                                snapmirror_schedule['dayofweek'],
                                )
                
                self.snapmirrors.append(sm)

    def get_snapvaults(self, ns):
        """
        Fetch the snapvault definitions for the configuration.
        """
        return self.snapvaults

    def get_snapmirrors(self, ns):
        """
        Fetch the snapmirror definitions for the configuration.
        """
        return self.snapmirrors

    #
    # A bunch of handy function to provide the commands that can be used to implement
    # the various aspects of the configuration
    #
    def filer_vol_create_commands(self, filer):
        """
        Build the filer vol create and options commands for a filer at a certain site and type.
        """
        cmdset = []

        for vol in filer.volumes:
            
            # volume creation
            cmd = "vol create %s %s %s" % (vol.name, vol.aggregate, vol.get_create_size())
            cmdset.append(cmd)

            # volume options
            for opt in vol.voloptions:
                opt = opt.replace('=', ' ')
                cmd = "vol options %s %s" % (vol.name, opt)
                cmdset.append(cmd)
                pass
            pass
        return cmdset

    def filer_vol_size_commands(self, filer):
        """
        The volume size commands. Useful for doing volume resizing.
        """
        cmdset = []

        for vol in filer.volumes:
            
            # volume creation
            cmd = "vol size %s %s" % (vol.name, vol.get_create_size())
            cmdset.append(cmd)

        return cmdset

    def filer_qtree_create_commands(self, filer):
        """
        Build the qtree creation commands for qtrees on volumes on filers at site and type.
        """
        cmdset = []
        for vol in filer.volumes:
            for qtree in vol.qtrees:
                cmdset.append( "qtree create /vol/%s/%s" % (qtree.volume.name, qtree.name) )
                cmdset.append( "qtree security /vol/%s/%s %s" % (qtree.volume.name, qtree.name, qtree.security) )
                pass
            pass
        return cmdset

    def vlan_create_commands(self, filer):
        """
        Find the project VLAN for the filer's site,
        and return the command for how to create it.
        """
        cmdset = []
        vlan = self.get_project_vlan(filer.site)
        cmdset.append("vlan add svif0 %s" % vlan.number)
        return cmdset

    def ipspace_create_commands(self, filer, ns):
        """
        Determine how to create the ipspace for the filer.
        """
        cmdset = []
        vlan = self.get_project_vlan(filer.site)
        cmdset.append("ipspace create ips-%s" % self.shortname)
        cmdset.append("ipspace assign ips-%s svif0-%s" % (self.shortname, vlan.number) )
        return cmdset

    def vfiler_create_commands(self, filer, vfiler, ns):
        cmdset = []
        cmdset.append("vfiler create %s -n -s ips-%s -i %s /vol/%s_root" % (vfiler.name,
                                                                            vfiler.name,
                                                                            vfiler.ipaddress,
                                                                            vfiler.name,
                                                                            ) )
        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_add_volume_commands(self, filer, ns):
        cmdset = []
        for vol in filer.volumes:

            # Skip the root volume, because it's already part of the vfiler
            if vol.name.endswith("root"):
                continue
            
            cmdset.append("vfiler add %s /vol/%s" % (self.shortname, vol.name))
            pass
        
        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_add_storage_interface_commands(self, filer, vfiler):
        cmdset = []

        if filer.type == 'secondary':
            cmd = "ifconfig svif0-%s 0.0.0.0 netmask %s mtusize 9000 up" % ( vfiler.vlan.number, vfiler.netmask)

        else:
            cmd = "ifconfig svif0-%s %s netmask %s mtusize 9000 up" % (vfiler.vlan.number,
                                                                   vfiler.ipaddress,
                                                                   vfiler.netmask)

        # Add partner clause if this is a primary or secondary filer
        if filer.type in [ 'primary', 'secondary' ]:
            cmd += " partner svif0-%s" % self.get_project_vlan(filer.site).number
        cmdset.append(cmd)

        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_add_inter_project_routing(self, vfiler):
        """
        Provide the routing commands required to route to services VLANs
        FIXME: Look at the services VLANs in the configuration. Add to vfiler?
        """
        cmdset = []        

        # Add inter-project route if required?
        cmdset.append("vfiler run %s route add default %s 1" % (vfiler.vlan.number,
                                                                vfiler.gateway) )

        return cmdset

    def get_project_vlan(self, site='primary'):
        """
        Find the project vlan for the site
        """
        for vlan in self.vlans:
            if vlan.site == site and vlan.type == 'project':
                return vlan

    def get_services_vlans(self, site='primary'):
        """
        Return a list of all vlans of type 'services'
        """
        return [ vlan for vlan in self.vlans if vlan.type == 'services' and vlan.site == site ]
            
    def services_vlan_route_commands(self, site, vfiler):
        """
        Return commands for configuring the services vlan routes
        """
        cmdset = []

        for vlan in self.get_services_vlans(site):
            cmdset.append("vfiler run %s route add net %s/%s %s 1" % (vfiler.name, vlan.network, vlan.netmask, vlan.gateway) )
            pass
        
        return cmdset
    
    def vfiler_set_allowed_protocols_commands(self, vfiler, ns):
        cmdset = []

        # first, disallow everything
        cmdset.append("vfiler disallow %s proto=rsh proto=http proto=ftp proto=iscsi proto=nfs proto=cifs" % vfiler.name)

        # then, allow the ones we want
        for proto in self.allowed_protocols:
            cmdset.append("vfiler allow %s proto=%s" % (vfiler.name, proto) )

        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_setup_secureadmin_ssh_commands(self, vfiler):
        """
        Setup the vfiler for secure administration.
        """
        cmdset = []
        cmdset.append('vfiler run %s secureadmin setup -q ssh 768 512 768' % vfiler.name)
        return cmdset

    def vfiler_set_options_commands(self, vfiler, ns):
        cmdset = []

        options = [
            # not required, since we snapvault in vfiler0
            #'snapvault.enable on',
            'nfs.tcp.recvwindowsize 65536',
            'nfs.tcp.xfersize 65536',
            'cifs.tcp_window_size 64240',
            'cifs.neg_buf_size 33028',
            'iscsi.max_ios_per_session 256',
            'nfs.udp.enable off',
            ]

        for vol in vfiler.volumes:
            if len(vol.snapmirrors) > 0:
                options.append('snapmirror.enable on')
                break

        for opt in options:
            cmdset.append("vfiler run %s options %s" % (vfiler.name, opt) )
            pass
        
        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_quotas_file_contents(self, filer, vfiler, ns):
        """
        Generate the /etc/quotas file contents for the vfiler
        """
        quota_file = """#
# Quotas for %s
#
""" % vfiler.name

        for vol in filer.volumes:
            if not vol.name.endswith('root'):
                quota_file += '*    tree@/vol/%s    -    -    -    -    -\n' % vol.name
                pass
            pass

        #log.debug(quota_file)
        return quota_file

    def vfiler_quotas_add_commands(self, filer, vfiler, ns):
        """
        Return a list of commands that can be used to activate the quotas
        """
        cmdset = []
        file_contents = self.vfiler_quotas_file_contents(filer, vfiler, ns)
        for line in file_contents.split('\n'):
            if len(line) == 0:
                continue
            line = line.replace('#', '##')

            cmdset.append('wrfile -a /vol/%s_root/etc/quotas "%s"' % (vfiler.name, line))
            pass

        return cmdset
        
    def vfiler_quota_enable_commands(self, filer, vfiler):
        cmdset = []
        for vol in filer.volumes:
            if not vol.name.endswith('root'):
                cmdset.append("vfiler run %s quota on %s" % (vfiler.name, vol.name))
                pass
            pass
        return cmdset
    
    def vfiler_nfs_exports_commands(self, filer, vfiler, ns):
        """
        Provide a list of nfs export commands.
        We need to change into the vfiler context to run these commands.
        """
        cmdset = []
        #cmdset.append("vfiler context %s" % vfiler.name)
        #log.debug("Finding NFS exports for filer: %s", filer.name)
        for vol in [ x for x in filer.volumes if x.proto == 'nfs' ]:
            #log.debug("Found volume: %s", vol)
            for qtree in vol.qtrees:
                #log.debug("exporting qtree: %s", qtree)

                # Find read/write exports
                rw_export_to = []
                for host in qtree.rwhostlist:
                    try:
                        rw_export_to.append('%s' % host.storageip)
                    except IndexError:
                        log.error("Host %s has no storage IP address!" % hostnode.attrib['name'])
                        raise ValueError("Host %s has no storage IP address!" % hostnode.attrib['name'])
                    pass

                # Find read-only exports
                ro_export_to = []
                for host in qtree.rohostlist:
                    try:
                        ro_export_to.append('%s' % host.storageip)
                    except IndexError:
                        log.error("Host %s has no storage IP address!" % hostnode.attrib['name'])
                        raise ValueError("Host %s has no storage IP address!" % hostnode.attrib['name'])
                    pass

                if len(ro_export_to) > 0:
                    log.debug("Read only exports required!")
                    ro_export_str = "ro=%s," % ':'.join(ro_export_to)
                else:
                    ro_export_str = ''

                if len(rw_export_to) > 0:
                    rw_export_str = "rw=%s," % ':'.join(rw_export_to)
                else:
                    rw_export_str = ''

                # allow root mount of both rw and ro hosts
                root_exports = rw_export_to + ro_export_to
                
                export_line = "vfiler run %s exportfs -p %s%sroot=%s /vol/%s/%s" % (
                    vfiler.name,
                    rw_export_str,
                    ro_export_str,
                    ':'.join(root_exports),
                    vol.name, qtree.name,
                    )

                # Manual linewrap setup
                if len(export_line) > 90:
                    wraplines = textwrap.wrap(export_line, 90)
                    cmdset.append( '\\\n'.join(wraplines))
            pass
        #log.debug('\n'.join(cmdset))
        #cmdset.append("vfiler context vfiler0")
        return cmdset

    def filer_snapreserve_commands(self, filer, ns):
        cmdset = []

        for vol in filer.volumes:
            cmdset.append("snap reserve %s %s" % ( vol.name, vol.snapreserve ) )
            pass

        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapshot_commands(self, filer, ns):
        """
        Filer snapshot configuration commands for the project
        """
        cmdset = []

        for vol in filer.volumes:
            # Do snapshot schedules
            if len(vol.snaps) > 0:
                for snap in vol.snaps:
                    cmdset.append("snap sched %s %s %s %s" % (vol.name, snap.numweekly, snap.numdaily, snap.hourly_schedule))
                pass
            else:
                cmdset.append("snap sched %s 0 0 0" % (vol.name) )
                pass
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapvault_commands(self, filer, ns):
        cmdset = []
        for vol in filer.volumes:
            if len(vol.snapvaults) > 0:
                for snap in vol.snapvaults:
                    # If the snapvault sourcevol == the volume, this is a source snapvault schedule
                    if snap.sourcevol == vol:
                        cmdset.append("snapvault snap sched %s %s %s" % (vol.name, snap.basename, snap.src_schedule))
                        
                    elif snap.targetvol == vol:
                        # Use a transfer schedule
                        cmdset.append("snapvault snap sched -x %s %s %s" % (vol.name, snap.basename, snap.dst_schedule))
                    else:
                        log.error("snapvault target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            else:
                # No command to set up a blank schedule required.
                #cmdset.append("snapvault snap sched %s 0" % (vol.name) )
                pass
            
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapvault_init_commands(self, filer, ns):
        """
        Commands used to initialise the snapvaults.
        We need to make sure we only attempt to initilise each
        snapvault once: One snapvault relationship per qtree, regardless
        of how many schedules it may have.
        """
        cmdset = []
        donelist = []
        for vol in filer.volumes:
            if len(vol.snapvaults) > 0:
                for snap in vol.snapvaults:
                    # If the snapvault sourcevol == the volume, this is a source snapvault schedule
                    if snap.sourcevol == vol:
                        log.error("You cannot initialise the snapvaults from the source filer.")
                        
                    elif snap.targetvol == vol:
                        if snap.sourcevol.name.endswith('root'):
                            if (snap.sourcevol.filer, snap.sourcevol, 'root') not in donelist:
                                cmdset.append("snapvault start -S %s-svif0-2000:/vol/%s/- /vol/%s/%s" % (snap.sourcevol.filer.name, snap.sourcevol.name, snap.targetvol.name, snap.sourcevol.name ))
                                
                                donelist.append( (snap.sourcevol.filer, snap.sourcevol, 'root') )

                        # Snapvault relationships are done at the qtree level
                        for qtree in snap.sourcevol.qtrees:
                            if (snap.sourcevol.filer, snap.sourcevol, qtree) not in donelist:
                                cmdset.append("snapvault start -S %s-svif0-2000:/vol/%s/%s /vol/%s/%s" % (snap.sourcevol.filer.name, snap.sourcevol.name, qtree.name, snap.targetvol.name, qtree.name ))
                                donelist.append( (snap.sourcevol.filer, snap.sourcevol, qtree) )
                            else:
                                log.debug("Skipping duplicate snapvault initialisation for %s:/vol/%s/%s", snap.sourcevol.filer.name, snap.sourcevol.name, qtree.name)
                    else:
                        log.error("snapvault target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapmirror_init_commands(self, filer):
        """
        Commands used to initialise the snapmirrors.
        We need to make sure we only attempt to initilise each
        snapmirror once: One snapmirror relationship per volume, regardless
        of how many schedules it may have.
        """
        cmdset = []
        donelist = []
        for vol in filer.volumes:
            if len(vol.snapmirrors) > 0:
                for snap in vol.snapmirrors:
                    # If the sourcevol == the volume, this is a source snapmirror schedule
                    if snap.sourcevol == vol:
                        log.error("You cannot initialise the snapmirror from the source filer.")
                        
                    elif snap.targetvol == vol:
                        if (snap.sourcevol, snap.targetvol) not in donelist:
                            cmdset.append("vol restrict %s" % snap.targetvol.name)
                            cmdset.append("snapmirror initialize -S %s-svif0-2000:%s %s" % (snap.sourcevol.filer.name, snap.sourcevol.name, snap.targetvol.name))
                                
                            donelist.append( (snap.sourcevol, snap.targetvol) )
                    else:
                        log.error("snapmirror target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_etc_snapmirror_contents(self, filer):
        """
        Returns the lines to append to the /etc/snapmirror file
        on the filer for this project.
        """
        cmdset = []
        cmdset.append("#")
        for vol in filer.volumes:
            if len(vol.snapmirrors) > 0:
                for snap in vol.snapmirrors:
                    # If the sourcevol == the volume, this is the source side, so ignore it
                    if snap.sourcevol == vol:
                        log.warn("/etc/snapmirror not used on the source filer.")
                        
                    elif snap.targetvol == vol:
                        # Use a transfer schedule
                        cmdset.append("%s-svif0-2000:%s %s:%s %s" % (snap.sourcevol.filer.name, snap.sourcevol.name, snap.targetvol.filer.name, snap.targetvol.name, snap.etc_snapmirror_conf_schedule()))
                    else:
                        log.error("snapmirror target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_etc_snapmirror_conf_commands(self, filer):
        """
        Returns a list of commands that can be used to append to
        the /etc/snapmirror file on the filer for this project.
        """
        cmdset = []
        file_contents = self.filer_etc_snapmirror_contents(filer)
        for line in file_contents:
            if len(line) == 0:
                continue
            line = line.replace('#', '##')

            cmdset.append('wrfile -a /etc/snapmirror.conf "%s"' % (line))
            pass

        return cmdset

    def vfiler_etc_hosts_contents(self, filer, vfiler):
        """
        Generate the additions for the /etc/hosts file on the
        vfiler that are specific to this project.
        """
        file = """#
# %s
#
%s %s-svif0-%s
""" % (vfiler.name, vfiler.ipaddress, filer.name, vfiler.vlan.number )

        return file

    def vfiler_etc_hosts_commands(self, filer, vfiler):
        """
        Returns a list of commands that can be used to create the /etc/hosts
        file within a particular vfiler for the project.
        """
        cmdset = []
        file_contents = self.vfiler_etc_hosts_contents(filer, vfiler)
        for line in file_contents.split('\n'):
            if len(line) == 0:
                continue
            line = line.replace('#', '##')

            cmdset.append('wrfile -a /vol/%s_root/etc/hosts "%s"' % (vfiler.name, line))
            pass

        return cmdset

    def filer_etc_rc_commands(self, filer, vfiler):
        """
        Returns a list of commands that can be used to add the /etc/rc
        entries to the filer.
        """
        cmdset = []
        cmds = [ '#', '# %s' % vfiler.name, '#' ] 
        cmds += self.vlan_create_commands(filer)
        cmds += self.vfiler_add_storage_interface_commands(filer, vfiler)
        if filer.type in ['primary', 'nearstore']:
            cmds += self.services_vlan_route_commands(filer.site, vfiler)

        for line in cmds:
            if len(line) == 0:
                continue
            line = line.replace('#', '##')
            cmdset.append('wrfile -a /vol/vol0/etc/rc "%s"' % line)

        return cmdset

if __name__ == '__main__':

    log.setLevel(logging.DEBUG)

    configfile = sys.argv[1]

    try:
        doc = etree.parse(configfile)
        proj = ProjectConfig(doc)
    except:
        log.error("Cannot load configuration. Aborting.")
        import traceback
        traceback.print_exc()
        sys.exit(1)

