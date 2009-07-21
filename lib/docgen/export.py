## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Storage export object
"""
from ConfigParser import NoSectionError, NoOptionError

from docgen.base import DynamicNamedXMLConfigurable

import logging
import debug
log = logging.getLogger('docgen')

class Export(DynamicNamedXMLConfigurable):
    """
    An encapsulation of a storage export to a specific host/IP
    """
    xmltag = 'export'

    child_tags = [
        ]

    mandatory_attribs = [
        ]
    
    optional_attribs = [
        'type',
        'to',
        'from'
        #'ro',
        'toip',
        ]
    
    def __init__(self, type='rw', tohost=None, fromip=None, toip=None):
        """
        An export to a given host, from a particular address
        """
        self.type = type
        self.tohost = tohost
        self.fromip = fromip
        self.toip = toip

    def __eq__(self, export):
        if export.type == self.type and export.tohost == self.tohost and \
           export.fromip == self.fromip and export.toip == self.toip:
            return True
        
        return False

    def __ne__(self, export):
        if self == export:
            return False
        return True

    def __str__(self):
        return '<Export: %s, to: %s[%s], from: %s>' % ( self.type, self.tohost, self.toip, self.fromip )

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)

        # Type defaults to 'rw' if a default isn't set and it isn't manually set
        if self.type is None:
            try:
                self.type = defaults.get('export', 'default_export_type')
            except (NoSectionError, NoOptionError):
                self.type = 'rw'
                pass
            pass


def create_export_from_node(node, defaults, parent):
    """
    Create an Export from an XML definition
    """
    obj = Export()
    obj.configure_from_node(node, defaults, volume)
    return obj
