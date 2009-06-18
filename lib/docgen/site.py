## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Physical site and related design objects
"""

import logging
import debug
log = logging.getLogger('docgen')

class Site:
    """
    A site contains Filers, VLANS, etc.
    """
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

        # Hosts, keyed by hostname
        self.hosts = {}
        
        # Filers, keyed by unique name
        self.filers = {}

        # VLANs. This is a list, because the same VLAN number can be used
        # for different sites.
        self.vlans = []

        # Volumes, just a list
        self.volumes = []

        log.debug("Added Site: %s", self)

    def __repr__(self):
        """
        String representation of a Site object
        """
        return '<Site: %s, type: %s, location: %s>' % (self.name, self.type, self.location)

