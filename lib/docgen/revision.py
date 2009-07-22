# $Id$
#

"""
DocGen project revisions object
"""
from base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class Revision(DynamicNamedXMLConfigurable):
    """
    A project revision
    """
    xmltag = 'revision'
    child_tags = [
        #'revremark',
        ]

    mandatory_attribs = [
        'majornumber',
        'minornumber',
        'date',
        'author',
        ]

    optional_attribs = [
        'reviewer',
        'reviewdate',
        'revremark',
        ]

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        comment = node.find('revremark')
        if comment is not None:
            self.revremark = comment.text

def create_revision_from_node(node, defaults, parent):
    rev = Revision()
    rev.configure_from_node(node, defaults, parent)
    return rev
