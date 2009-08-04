## $Id$

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
        'ip',
        ]

    optional_attribs = [
        'type',
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

        # If I have a vlan_number set, my VLAN is the vlan
        # my parent has that has the same vlan number
        if self.vlan_number is not None:
            self.vlan_number = int(self.vlan_number)
            log.debug("vlan number: %s, %s", self.vlan_number, parent.site.get_vlans() )
            self.vlan = [x for x in parent.site.get_vlans() if x.number == self.vlan_number][0]
        else:
            # The vlan I belong to is my parent's VLAN
            self.vlan = parent.get_vlan()
            pass
        
        if self.vlan is None:
            raise KeyError("No VLAN defined for parent of IP address %s" % self.ip)

        # If this is a service IP, it must have a vlan number defined
        if self.type == 'service':
            if self.vlan_number is None:
                raise KeyError("Service IP address '%s' defined with no vlan_number attribute." % self.ip)
                pass
            pass

        # if the netmask isn't set, make it the same as the first
        # network in the vlan the IP is in.
        if self.netmask is None:
            try:
                network = self.vlan.get_networks()[0]
            except IndexError:
                raise IndexError("VLAN %s has no networks defined" % self.vlan.number)
            self.netmask = network.netmask
                
    def configure_mandatory_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_mandatory_attributes(self, node, defaults)

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)
        if self.type is None:
            self.type = 'primary'
            pass
        
        if self.type not in self.known_types:
            raise ValueError("IPaddress type '%s' is not a valid type" % self.type)

def create_ipaddress_from_node(node, defaults, site):
    """
    Create an IPaddress from an XML node
    """
    obj = IPAddress()
    obj.configure_from_node(node, defaults, site)
    return obj
    
