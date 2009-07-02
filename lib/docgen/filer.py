## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

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
                   ]

    mandatory_attribs = [ 'name',
                          'type',
                          ]

    optional_attribs = [
        ]

    def __init__(self):
        self.name = None
        self.type = None
        self.last_volnum = 0
    
    def _depr__init__(self, name, type, site):

        self.volumes = []
        self.vfilers = {}

        # If I am a secondary, who am I a secondary for?
        self.secondary_for = None

        # If I have a secondary, who is it?
        self.secondary_is = None

        # If I have a cluster partner, who is it?
        self.cluster_partner = None

    def configure_from_node(self, node, defaults, site):
        self.site = site
        
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, site)

        if self.type not in self.FILER_TYPES:
            raise ValueError("Filer type '%s' not a known Filer type" % self.type)

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
        
def create_filer_from_node(node, defaults, site):
    filer = Filer()
    filer.configure_from_node(node, defaults, site)
    return filer
