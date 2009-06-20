## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Physical site and related design objects
"""

import ConfigParser
from base import XMLConfigurable, DynamicNaming

import logging
import debug
log = logging.getLogger('docgen')

class Site(XMLConfigurable, DynamicNaming):
    """
    A site contains Filers, VLANS, etc.
    """
    xmltag = 'site'
    
    def __init__(self, name, type, location='', nameservers=[], winsservers=[]):
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
        ns['site_name'] = self.name
        ns['site_type'] = self.type
        return ns

def create_site_from_node(node, defaults, parent):
    
    # Site name is a new attribute, so allow a kind of backwards compatibility for now
    try:
        site_name = node.attrib['name']
    except KeyError:
        # FIXME: You can only guess the site name if it's
        # involved somehow in your filer naming convention.
        raise KeyError("Site name not set.")

    # Get the site type from the defaults if it isn't set
    try:
        site_type = node.attrib['type']

    except KeyError:
        site_type = defaults.get(site_name, 'type')

    # Get the site location from the defaults if it isn't set                
    try:
        site_location = node.attrib['location']
    except KeyError:
        site_location = defaults.get('site_%s' % site_name, 'location')
        pass

    # Add default site servers for CIFS
    # This should be added the DTD to allow manual override
    try:
        nameservers = defaults.get('site_%s' % site_name, 'nameservers').split()
    except ConfigParser.NoSectionError:
        nameservers = []
    try:
        winsservers = defaults.get('site_%s' % site_name, 'nameservers').split()
    except ConfigParser.NoSectionError:
        winsservers = []

    site = Site(site_name, site_type, site_location, nameservers, winsservers)

    # configure child elements
    site.configure_from_node(node, defaults, parent)
    
    return site
