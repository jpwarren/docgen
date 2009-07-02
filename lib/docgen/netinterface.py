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

    def __init__(self, type, mode, switchname=None, switchport=None, hostport=None, ipaddress=None, mtu=9000, vlans=[]):

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

def create_netinterface_from_node(node, defaults, parent):
    """
    Create a network interface from an XML node
    """
    try:
        switchname = node.find('switchname').text
        switchport = node.find('switchport').text
    except AttributeError, e:
        if not parent.is_virtual:
            log.debug("Switch parameters not present for NetInterface of %s: %s", parent, e)
        switchname = None
        switchport = None

    try:
        hostport = node.find('hostport').text
    except AttributeError, e:
        log.debug("No host port defined for host: %s", parent)
        hostport = None

    try:
        ipaddr = node.find('ipaddr').text
    except AttributeError:
        ipaddr = None
        pass
    
    # NetInterface must have a type
    try:    
        type = node.attrib['type']
    except KeyError:
        raise KeyError("NetInterface for %s has no type" % parent)

    try:
        mode = node.attrib['mode']
    except KeyError:
        mode = 'passive'
        pass
    
    # Figure out the VLANs this interface should be in.
    # If one isn't defined, put it in the first VLAN for
    # the site the parent is in with the same type
    vlan_nums = node.findall('vlan_number')
    vlans = []
    if len(vlan_nums) == 0:
        vlans = [ vlan for vlan in parent.get_site().get_vlans() if vlan.type == type ]

    else:
        for vlan_num in vlan_nums:
            vlans.extend([ vlan for vlan in parent.get_site().get_vlans()
                           if vlan.number == int(vlan_num.text) ])
            pass
        pass

    try:
        mtu = int(node.attrib['mtu'])
    except KeyError:
        # If the MTU isn't set on the interface, try to use
        # the mtu for the VLAN it's in, if one is defined
        try:
            vlan = vlans[0]
            mtu = vlan.mtu
        except IndexError:
            # Use the default mtu
            mtu = defaults.getint('vlan', 'default_mtu')

    # Add the required switch to the project switches list
    if switchname is not None:
        try:
            switch = self.known_switches[switchname]
        except KeyError:
            raise KeyError("Switch '%s' is not defined. Is it in switches.conf?" % switchname)

        log.debug("Adding switch '%s' to project switch list at site '%s'", switch, site)
        switch.site = site
        self.project_switches[switchname] = switch

        # If this is an edge, make sure its connected cores are added to the
        # list of project switches.
        if switch.type == 'edge':
            for coreswitch in switch.connected_switches:
                if coreswitch not in self.project_switches:
                    self.project_switches[coreswitch] = self.known_switches[coreswitch]
                    self.project_switches[coreswitch].site = site
                    pass
                pass
            pass


    iface = NetInterface(type, mode, switchname, switchport, hostport, ipaddr, mtu, vlans)
    return iface

