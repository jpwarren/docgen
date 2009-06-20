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
    
    def __init__(self, number, site, type='project', description='', mtu=9000, node=None):

        self.description = description
        self.site = site
        self.sitetype = site
        self.type = type
        self.number = number

        self.mtu = mtu
        self.node = node

        self.children = {}

        #log.debug("Created vlan: %s", self)

    def __repr__(self):
        return '<Vlan: %s, %s/%s: %s>' % (self.number, self.site, self.type, self.networks)

    def get_networks(self):
        try:
            return self.children['network']
        except KeyError:
            return []

def create_vlan_from_node(node, defaults, site):
    """
    Given a VLAN node, create the VLAN
    """
    try:
        number = int(node.attrib['number'])
    except KeyError:
        raise KeyError("Vlan node has no number attribute")

    try:
        type = node.attrib['type']
    except KeyError:
        raise KeyError("Vlan '%d' has no type attribute" % number)

    description = node.text
    if description is None:
        description = ''
        pass
    
    try:
        mtu = int(node.attrib['mtu'])
    except KeyError:
        mtu = defaults.get('vlan', 'default_mtu')
        pass

    vlanobj = Vlan(number, site, type, description, mtu, node)
    vlanobj.configure_from_node(node, defaults, site)

    return vlanobj
