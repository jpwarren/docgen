## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
NetApp Qtree object
"""
from docgen.base import XMLConfigurable, DynamicNaming

import logging
import debug
log = logging.getLogger('docgen')

class Qtree(XMLConfigurable, DynamicNaming):
    def __init__(self, volume, qtree_name=None,
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
        return '<Qtree: %s, %s, sec: %s, rw: %s, ro: %s>' % (self.full_path(), self.volume.proto, self.security, [ str(x) for x in self.rwexports ], [ str(x) for x in self.roexports])

    def populate_namespace(self, ns={}):
        ns = self.volume.populate_namespace(ns)
        ns['qtree_name'] = self.name
        ns['qtree_security'] = self.security
        return ns
    
    def full_path(self):
        """
        The full qtree path, including the volume prefix.
        """
        return '/vol/%s/%s' % (self.volume.name, self.name)

    def cifs_share_name(self, hidden=True):
        """
        Get the CIFS share name for the qtree.
        """
        retstr = '%s_%s' % (self.volume.name, self.name)
        if hidden:
            retstr += '$'
            pass
        return retstr

