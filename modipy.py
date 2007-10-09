#
# $Id$
# This module defines a document generator for creating ModiPY templates
# that can implement a given design.
# ModiPY is a Python based framework for executing commands on remote devices
# to implement a series of changes. http://modipy.seafelt.com
#

import zope.interface
import logging
import debug

log = logging.getLogger('docgen')

from docgen import IDocumentGenerator

class ModiPYGenerator:
    """
    An abstract base class that implements some commonly used functions.
    """
    zope.interface.implements(IDocumentGenerator)

    def __init__(self, conf):
        self.conf = conf

class IPSANModiPYGenerator(ModiPYGenerator):
    """
    A generator for creating ModiPY templates to implement an IPSAN design.
    """

    def emit(self, outfile=None, ns={}):
        log.error("No output yet.")
        
        log.debug("My configuration: %s", self.conf)

        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'primary' ]:
            log.debug("Creation commands for %s", filer.name)
            
            cmds = self.conf.filer_vol_create_commands(filer)
