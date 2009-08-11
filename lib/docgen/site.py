## $Id$

"""
Physical site and related design objects
"""

from ConfigParser import NoSectionError

from base import DynamicNamedXMLConfigurable, LunNumbering

import logging
import debug
log = logging.getLogger('docgen')

class Site(DynamicNamedXMLConfigurable, LunNumbering):
    """
    A site contains Filers, VLANS, etc.
    """
    xmltag = 'site'

    child_tags = [ 'vlan',
                   'host',
                   'filer',
                   'nameserver',
                   'winsserver',
                   ]
    
    mandatory_attribs = [ 'name',
                          'type',
                          ]

    optional_attribs = [ 'location',
                         ]

    def __init__(self):
        self.current_lunid = 0
    
    # Deprecated, as we use auto-config now.
    def _depr__init__(self, name, type, location='', nameservers=[], winsservers=[]):
        """
        @param type: type is one of ('primary' | 'secondary') and is unique for a project.
        @param location: a descriptive string for the site
        """
        self.name = name
        self.type = type
        self.location = location

        self.nameservers = nameservers
        self.winsservers = winsservers

        # IXMLConfigurable requirement
        self.children = {}
        
        # Hosts, keyed by hostname
        self.hosts = {}
        
        # Filers, keyed by unique name
        self.filers = {}

        # VLANs. This is a list, because the same VLAN number can be used
        # for different sites.
        self.vlans = []

        # Volumes, just a list
        self.volumes = []

        #log.debug("Added Site: %s", self)

    def __repr__(self):
        """
        String representation of a Site object
        """
        return '<Site: %s, type: %s, location: %s>' % (self.name, self.type, self.location)

    def populate_namespace(self, ns={}):
        ns = self.parent.populate_namespace(ns)
        ns['site_name'] = self.name
        ns['site_type'] = self.type
        return ns

    def name_dynamically(self, defaults):
        if getattr(self, 'location', None) is None:
            try:
                self.location = defaults.get('site_%s' % self.name, 'location')
            except NoSectionError:
                self.location = ''

    def get_volumes(self):
        volumes = []
        for filer in self.get_filers():
            volumes.extend(filer.get_volumes())
            pass
        return volumes

    def get_luns(self):
        luns = []
        for vol in self.get_volumes():
            luns.extend( vol.get_luns() )
            pass
        return luns
    
    def link_filer_clusters(self):
        """
        Once we've loaded all our children, link filer clusters
        together, if they've been marked as being clustered.
        """
        for filer in self.get_filers():
            if filer.partner is not None:
                # Find the partner by name
                try:
                    filer.cluster_partner = [ x for x in self.get_filers() if x.name == filer.partner ][0]
                except IndexError:
                    raise ValueError("Filer '%s' partner '%s' not defined!" % (filer.name, filer.partner) )
                pass
            pass
        pass
    
    def get_allowed_protocols(self):
        """
        Get all the protocols defined anywhere in the project
        """
        protos = []
        for filer in self.get_filers():
            protos.extend( filer.get_allowed_protocols() )
            pass
        return protos

    def setup_exports(self):
        """
        For all the filers at this site, set up the exports
        for all the volumes and qtrees on them.
        """
        for filer in self.get_filers():
            filer.setup_exports()
            pass
        
def create_site_from_node(node, defaults, parent):
    site = Site()
    site.configure_from_node(node, defaults, parent)
    return site
