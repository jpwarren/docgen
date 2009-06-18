## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Networking related design objects
"""

import logging
import debug
log = logging.getLogger('docgen')

class Interface:

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

class Vlan:
    """
    A vlan defines the layer 2 network a vfiler belongs to, or a services vlan.
    """

    def __init__(self, number, site='primary', type='project', networks=[], description='', mtu=9000, node=None):

        self.description = description
        self.site = site
        self.sitetype = site
        self.type = type
        self.number = number

        self.networks = networks
        
##         self.network = network
##         self.netmask = netmask
##         self.gateway = gateway
##         self.maskbits = maskbits

        self.mtu = mtu
        self.node = node

        log.debug("Created vlan: %s", self)

    def __repr__(self):
        return '<Vlan: %s, %s/%s: %s>' % (self.number, self.site, self.type, self.networks)

class Network:
    """
    A Network object encapsulates an IP network.
    """

    def __init__(self, number, netmask, maskbits, gateway):
        """
        Create a Network object
        """
        self.number = number
        self.netmask = netmask
        self.maskbits = maskbits
        self.gateway = gateway

    def __repr__(self):

        return "<Network: %s/%s (%s) -> %s>" % (self.number, self.maskbits, self.netmask, self.gateway)


