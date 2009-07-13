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
            
