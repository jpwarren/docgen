# $Id$
#

"""
DocGen Project definitions.

The <project/> node is the root of all DocGen projects,
and is used to dynamically configure and build the project
definition.
"""
from docgen.base import XMLConfigurable, DynamicNaming

import debug
import logging
log = logging.getLogger('docgen')

class Project(XMLConfigurable, DynamicNaming):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'project'
    child_tags = [ 'title', 'background', 'revhistory',
        'site', 'snapvaultset', 'snapmirrorset' ]

    mandatory_attribs = [ 'prefix', 'code' ]

    def __init__(self):
        self.name = ''
        self.children = {}
        
        
