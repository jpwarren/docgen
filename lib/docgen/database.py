## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Databases
"""

import logging
import debug
log = logging.getLogger('docgen')

class Database:

    def __init__(self, name, type, onhosts=[]):
        self.name = name
        self.type = type
        self.onhosts = []
        log.debug("Created: %s", self)

    def __str__(self):
        return '<Database: %s:%s>' % (self.name, self.type)

class OracleDatabase(Database):
    
    def __init__(self, name, onhosts=[]):
        
        Database.__init__(self, name, type='oracle', onhosts=onhosts)
