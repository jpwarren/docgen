# $Id$
#

"""
DocGen Project definitions.

The <project/> node is the root of all DocGen projects,
and is used to dynamically configure and build the project
definition.
"""
from base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class Project(DynamicNamedXMLConfigurable):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'project'
    child_tags = [ 'title', 'background', 'revhistory',
        'site', 'snapvaultset', 'snapmirrorset' ]

    mandatory_attribs = [ 'prefix', 'code' ]

    def __init__(self):
        self.prefix = None
        self.code = None
        self.children = {}
        
    def populate_namespace(self, ns={}):
        """
        Add my namespace pieces to the namespace
        """
        ns['project_prefix'] = self.prefix
        ns['project_code'] = self.code
        return ns

    def get_volumes(self):
        """
        Find all the project volumes
        """
        volumes = []
        for site in self.get_sites():
            volumes.extend(site.get_volumes())
            pass
        return volumes
