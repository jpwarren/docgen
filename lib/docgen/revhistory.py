# $Id$
#

"""
RevHistory

A collection of Revision nodes.
"""
from docgen.base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class RevHistory(DynamicNamedXMLConfigurable):
    """
    A collection of revision history nodes
    """
    xmltag = 'revhistory'

def create_revhistory_from_node(node, defaults, parent):
    rh = RevHistory()
    return rh.configure_from_node(node, defaults, parent)
        
