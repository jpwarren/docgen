# $Id$
#

"""
DocGen Project definitions.

The <project/> node is the root of all DocGen projects,
and is used to dynamically configure and build the project
definition.
"""
from ConfigParser import NoSectionError, NoOptionError
from base import DynamicNamedXMLConfigurable

from lxml import etree

# FIXME: Doing it this way means we can't override this in
# a user defined plugin. Need the lookup table instead.
from volume import Volume

import debug
import logging
log = logging.getLogger('docgen')

class Project(DynamicNamedXMLConfigurable):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'project'
    child_tags = [ 'title', 'background', 'revision',
        'site', 'snapvaultset', 'snapmirrorset' ]

    mandatory_attribs = [ 'name', 'code' ]

    def populate_namespace(self, ns={}):
        """
        Add my namespace pieces to the namespace
        """
        ns['project_name'] = self.name
        ns['project_code'] = self.code
        return ns

    def get_hosts(self):
        """
        Find all the project hosts
        """
        objs = []
        for site in self.get_sites():
            objs.extend(site.get_hosts())
            pass
        return objs
    
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
        protos = []
        for site in self.get_sites():
            protos.extend( site.get_allowed_protocols() )
            pass
        return protos

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        #
        # Once the project is configured, set up some other bits and pieces
        #
        self.setup_exports()

    def setup_exports(self):
        """
        Set up all the exports for my sites using either manually
        configured exports, or appropriate defaults.
        """
        for site in self.get_sites():
            site.setup_exports()
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
