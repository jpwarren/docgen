## $Id$

"""
NetApp Qtree object
"""
from ConfigParser import NoSectionError, NoOptionError

from docgen.base import DynamicNamedXMLConfigurable

import logging
import debug
log = logging.getLogger('docgen')

class Qtree(DynamicNamedXMLConfigurable):

    xmltag = 'qtree'

    child_tags = [
        'lun',
        'export',
        'exportalias',
        ]

    mandatory_attribs = [
        ]
    
    optional_attribs = [
        'name',
        'description',
        'security',
        'comment',
        'oplocks',
        ]
    
    def _depr__init__(self, volume, qtree_name=None,
                 security='unix',
                 comment='',
                 rwexports=[],
                 roexports=[],
                 qtreenode=None,
                 oplocks=True,
                 aliases=[]):

        """
        A Qtree representation
        """
        self.volume = volume
        if qtree_name is None:
            qtree_name = 'data'
        
        self.name = qtree_name
        self.security = security
        self.comment = comment
        self.rwexports = rwexports
        self.roexports = roexports
        self.qtreenode = qtreenode

        self.oplocks = oplocks
        self.aliases = aliases
        
        self.luns = []
        
        log.debug("Created qtree: %s", self)
        
        self.volume.qtrees[self.name] = self
        #self.volume.qtrees.append(self)

    def __str__(self):
        #return '<Qtree: %s, %s, sec: %s, rw: %s, ro: %s>' % (self.full_path(), self.parent.protocol, self.security, [ str(x) for x in self.rwexports ], [ str(x) for x in self.roexports])
        return '<Qtree: %s, %s, sec: %s>' % (self.full_path(), self.parent.protocol, self.security)

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)
        self.volume = parent
        self.qtreenode = node

        self.children['exportalias'] = [ x.text for x in node.findall('exportalias') ]
            
    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)

        if getattr(self, 'security', None) is None:
            try:
                self.security = defaults.get('qtree', 'default_security')
            except (NoSectionError, NoOptionError):
                self.security = 'unix'

    def name_dynamically(self, defaults):
        if getattr(self, 'name', None) is None:
            ns = self.populate_namespace()
            naming_standard = defaults.get('qtree', 'qtree_name')
            self.name = naming_standard % ns

    def populate_namespace(self, ns={}):
        ns = self.parent.populate_namespace(ns)
        ns['qtree_name'] = getattr(self, 'name', None)
        ns['qtree_security'] = self.security
        return ns
    
    def full_path(self):
        """
        The full qtree path, including the volume prefix.
        """
        return '/vol/%s/%s' % (self.parent.name, self.name)

    def cifs_share_name(self, hidden=True):
        """
        Get the CIFS share name for the qtree.
        """
        retstr = '%s_%s' % (self.parent.name, self.name)
        if hidden:
            retstr += '$'
            pass
        return retstr

    def get_next_lunid(self):
        """
        Get the next available lunid for the volume
        """
        return self.parent.get_next_lunid()
    
    def get_iscsi_usable(self):
        return self.parent.get_iscsi_usable()

    def set_current_lunid(self, value):
        return self.parent.set_current_lunid(value)
    
    def add_to_lun_total(self, amount):
        return self.parent.add_to_lun_total(amount)

    def get_rw_exports(self):
        return [ x for x in self.get_exports() if x.type == 'rw' ]

    def get_ro_exports(self):
        return [ x for x in self.get_exports() if x.type == 'ro' ]
    
def create_qtree_from_node(node, defaults, volume):
    """
    Create a qtree from an XML definition
    """
    qtree = Qtree()
    qtree.configure_from_node(node, defaults, volume)
    return qtree
