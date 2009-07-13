## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
DocGen IPAddress object
"""
from docgen.base import DynamicNamedXMLConfigurable
from docgen import network

import logging
import debug
log = logging.getLogger('docgen')

class IPAddress(DynamicNamedXMLConfigurable):
    """
    An IPAddress is just what it says on the tin
    """
    xmltag = 'ipaddress'

    child_tags = [
        ]
    
    mandatory_attribs = [
        'type',
        'ip',
        ]

    optional_attribs = [
        'description',
        'netmask',
        'vlan_number',
        ]

    known_types = [
        'primary',
        'alias',
        'service',
        ]

    def __init__(self):

        self.vlan = None
    
    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        # The vlan I belong to is my parent's VLAN
        self.vlan = parent.get_vlan()
        # If this is a service IP, it must have a vlan number defined
        if self.type == 'service':
            if self.vlan_number is None:
                raise KeyError("Service IP address '%s' defined with no vlan_number attribute." % self.ip)
            else:
                self.vlan_number = int(self.vlan_number)

    def configure_mandatory_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_mandatory_attributes(self, node, defaults)
        if self.type not in self.known_types:
            raise ValueError("IPaddress type '%s' is not a valid type" % self.type)

def create_ipaddress_from_node(node, defaults, site):
    """
    Create an IPaddress from an XML node
    """
    obj = IPAddress()
    obj.configure_from_node(node, defaults, site)
    return obj
    
