# $Id$
#

"""
Aggregate object definition

"""
from docgen.base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class Aggregate(DynamicNamedXMLConfigurable):
    """
    A NetApp vFiler object
    """
    xmltag = 'aggregate'
    
    child_tags = [
        'volume',
        ]

    mandatory_attribs = [
        'name',
        ]

    optional_attribs = [
        'type',
        ]

    # A root aggregate tells us where to put the vfiler root volume
    # if it's not manually defined.
    known_types = [ 'root', 'data' ]

    def __init__(self):
        self.name = None

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)

        # Aggregate type defaults to 'data'
        if self.type is None:
            self.type = 'data'
        
    def populate_namespace(self, ns={}):
        ns = self.parent.populate_namespace(ns)
        ns['aggr_name'] = self.name
        return ns

    def get_filer(self):
        return self.parent.get_filer()

    def get_next_volnum(self):
        return self.parent.get_next_volnum()
    
def create_aggregate_from_node(node, defaults, parent):
    aggr = Aggregate()
    aggr.configure_from_node(node, defaults, parent)
    return aggr
