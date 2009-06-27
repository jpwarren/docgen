## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
NetApp Filer object
"""
from docgen.base import XMLConfigurable, DynamicNaming

import logging
import debug
log = logging.getLogger('docgen')

class Filer(XMLConfigurable, DynamicNaming):
    """
    A NetApp Filer
    """
    FILER_TYPES = [
        'filer',
        'nearstore',
        ]

    xmltag = 'filer'

    child_tags = [ 'vfiler',
                   'volume',
                   ]

    mandatory_attribs = [ 'name',
                          'type',
                          ]

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
        XMLConfigurable.configure_from_node(self, node, defaults, site)

        self.site = site

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
    
