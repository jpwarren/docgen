## $Id$

"""
NetApp Filer object
"""
from base import DynamicNamedXMLConfigurable

import logging
import debug
log = logging.getLogger('docgen')

class Filer(DynamicNamedXMLConfigurable):
    """
    A NetApp Filer
    """
    FILER_TYPES = [
        'filer',
        'nearstore',
        ]

    xmltag = 'filer'

    child_tags = [ 'vfiler',
                   'aggregate',
                   'igroup',
                   ]

    mandatory_attribs = [
        'name',
        ]

    optional_attribs = [
        'type',
        'partner',
        ]

    def __init__(self):
        self.last_volnum = 0

        # If I have a cluster partner, who is it?
        self.cluster_partner = None
        # Am I the active node?
        # This means I get the IP addresses, etc. for vFilers
        # and my partner gets configured ready for failover
        # FIXME: How to sanely cope with active/active on
        # both cluster nodes?
        self.is_active_node = True
        
    def configure_from_node(self, node, defaults, site):
        self.site = site
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, site)

    def configure_optional_attributes(self, node, defaults):
        """
        Do some extra parameter checking after configuring attributes
        """
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)
        # Default filer type to 'filer'
        if self.type is None:
            self.type = defaults.get('filer', 'default_type')

        # vfiler type must be one of the known types
        if self.type not in self.FILER_TYPES:
            raise ValueError("Filer '%s' type '%s' not valid" % ( self.name, self.type) )
            
    def __str__(self):
        return '<Filer: %s (site:%s/type:%s)>' % (self.name, self.site, self.type)

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

    def populate_namespace(self, ns={}):
        ns = self.site.populate_namespace(ns)
        ns['filer_name'] = self.name
        return ns

    def get_filer(self):
        return self

    def get_site(self):
        return self.parent
    
    def get_next_volnum(self):
        self.last_volnum += 1
        return self.last_volnum

    def set_volnum(self, num):
        self.last_volnum = num

    def get_volumes(self):
        """
        Get all volumes defined on me, and any vFilers I might have
        """
        volumes = []
        for vfiler in self.get_vfilers():
            volumes.extend(vfiler.get_volumes())
            pass
        return volumes

    def get_luns(self):
        luns = []
        for vol in self.get_volumes():
            luns.extend( vol.get_luns() )
            pass
        return luns

    def get_allowed_protocols(self):
        """
        Get all the protocols defined anywhere in the project
        """
        protos = []
        for vfiler in self.get_vfilers():
            protos.extend( vfiler.get_allowed_protocols() )
            pass
        return protos

    def get_igroups(self):
        """
        Get all the iGroups defined in myself or my vFilers
        """
        igroups = self.children['igroup']
        for vfiler in self.get_vfilers():
            igroups.extend( vfiler.get_igroups() )
            pass
        return igroups

    def setup_exports(self):
        """
        Set up the exports from myself and my vfilers
        """
        # Do my exports setup

        # Do vFiler exports setup
        for vfiler in self.get_vfilers():
            vfiler.setup_exports()
            pass
    
def create_filer_from_node(node, defaults, site):
    filer = Filer()
    filer.configure_from_node(node, defaults, site)
    return filer
