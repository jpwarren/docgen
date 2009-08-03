## $Id$

"""
NetApp iGroup object
"""
from base import DynamicNamedXMLConfigurable

import logging
import debug
log = logging.getLogger('docgen')

class iGroup(DynamicNamedXMLConfigurable):
    """
    A Filer iGroup
    """
    xmltag = 'igroup'

    child_tags = [
        ]

    mandatory_attribs = [
        'name',
        ]

    optional_attribs = [
        'type',
        'number',
        'prefix',
        'suffix',
        ]

    def __init__(self):
        self.luns = []
        self.exports = []

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        # Find igroup members
        self.children['member'] = node.findall('member')

    def get_luns(self):
        return self.luns
        
    def get_exports(self):
        return self.exports

def create_igroup_from_node(node, defaults, parent):
    obj = iGroup()
    obj.configure_from_node(node, defaults, parent)
    return obj
