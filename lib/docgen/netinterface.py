# $Id$

"""
Network interface design objects

These are found on hosts at the moment, though they may
be found on other objects depending on how things go.
"""
from docgen.base import DynamicNamedXMLConfigurable

import logging
import debug
log = logging.getLogger('docgen')

class NetInterface(DynamicNamedXMLConfigurable):

    xmltag = 'netinterface'

    child_tags = [
        'ipaddress',
        ]

    mandatory_attribs = [
        'type',
        ]

    optional_attribs = [
        'mode',
        'hostport',
        'switchname',
        'switchport',
        'mtu',
        ]
    
    def ___init__(self, type, mode, switchname=None, switchport=None, hostport=None, ipaddress=None, mtu=9000, vlans=[]):

        self.type = type
        self.mode = mode
        self.switchname = switchname
        self.switchport = switchport
        self.hostport = hostport
        self.ipaddress = ipaddress
        self.mtu = mtu
        self.vlans = vlans

        log.debug("Created interface with vlans: %s", self.vlans)

    def __repr__(self):
        return '<Interface %s:%s %s:%s (%s)>' % (self.type, self.mode, self.switchname, self.switchport, self.ipaddress)

    def get_vlans(self):
        return self.vlans

    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)

        if self.mode is None:
            self.mode = 'passive'
            pass

        if self.mtu is not None:
            self.mtu = int(self.mtu)
    
    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        # Figure out the VLANs this interface should be in.
        # If one isn't defined, put it in the first VLAN for
        # the site the parent is in with the same type
        vlan_nums = node.findall('vlan_number')

        if len(vlan_nums) == 0:
            self.vlans = [ vlan for vlan in parent.get_site().get_vlans() if vlan.type == type ]

        else:
            self.vlans = []
            for vlan_num in vlan_nums:
                self.vlans.extend([ vlan for vlan in parent.get_site().get_vlans() if vlan.number == int(vlan_num.text) ])
                pass
            pass

        if self.mtu is None:
            # If the MTU isn't set on the interface, try to use
            # the mtu for the VLAN it's in, if one is defined
            try:
                vlan = self.vlans[0]
                mtu = int(vlan.mtu)
            except IndexError:
                # Use the default mtu
                mtu = defaults.getint('vlan', 'default_mtu')
                pass
            pass
        pass

def create_netinterface_from_node(node, defaults, parent):
    """
    Create a network interface from an XML node
    """

    # Add the required switch to the project switches list
#     if switchname is not None:
#         try:
#             switch = self.known_switches[switchname]
#         except KeyError:
#             raise KeyError("Switch '%s' is not defined. Is it in switches.conf?" % switchname)

#         log.debug("Adding switch '%s' to project switch list at site '%s'", switch, site)
#         switch.site = site
#         self.project_switches[switchname] = switch

#         # If this is an edge, make sure its connected cores are added to the
#         # list of project switches.
#         if switch.type == 'edge':
#             for coreswitch in switch.connected_switches:
#                 if coreswitch not in self.project_switches:
#                     self.project_switches[coreswitch] = self.known_switches[coreswitch]
#                     self.project_switches[coreswitch].site = site
#                     pass
#                 pass
#             pass

    iface = NetInterface()
    iface.configure_from_node(node, defaults, parent)
    return iface

