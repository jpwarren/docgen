## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Networking related design objects
"""
import logging
import debug
log = logging.getLogger('docgen')

from docgen.base import XMLConfigurable, DynamicNaming
from docgen import network

class Vlan(XMLConfigurable, DynamicNaming):
    """
    A vlan defines the layer 2 network a vfiler belongs to, or a services vlan.
    """
    xmltag = 'vlan'

    child_tags = [
        'network',
        ]
    
    mandatory_attribs = [
        'number',
        ]

    optional_attribs = [
        'type',
        'description',
        'mtu',
        ]
    
    def __init__(self, number=None, site=None, type='project', description='', mtu=9000, node=None):
        
        self.description = description
        self.site = site
        self.sitetype = site
        self.type = type
        self.number = number

        self.mtu = mtu
        self.node = node

        #log.debug("Created vlan: %s", self)

    def __repr__(self):
        return '<Vlan: %s, %s/%s>' % (self.number, self.site, self.type)

    def configure_from_node(self, node, defaults, site):
        self.site = site
        XMLConfigurable.configure_from_node(self, node, defaults, site)

        self.number = int(self.number)
        self.mtu = int(self.mtu)

def create_vlan_from_node(node, defaults, site):
    """
    Given a VLAN node, create the VLAN
    """
    vlanobj = Vlan()
    vlanobj.configure_from_node(node, defaults, site)
    return vlanobj
    
