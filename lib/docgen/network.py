## $Id$

"""
Networking related design objects
"""
import socket
import struct

import logging
import debug
log = logging.getLogger('docgen')

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

def create_network_from_node(node, defaults, parent):
    """
    Parse a network definition node and create a Network object.
    """
    try:
        number = node.attrib['number']
    except KeyError:
        raise KeyError("<network/> element has no 'number' attribute.")

    # Detect slash notation for network number/mask
    if number.find('/') > 0:
        try:
            number, netmask, maskbits = str2net(number)
        except:
            log.error("Error with network number for VLAN %s", number)
            raise
    else:
        try:
            netmask = node.attrib['netmask']
            maskbits = mask2bits(netmask)
        except KeyError:
            raise KeyError("network %s has no netmask defined." % number)
        pass

    try:
        gateway = node.attrib['gateway']
    except KeyError:
        raise KeyError("<network/> element has no 'gateway' attribute.")

    return Network(number, netmask, maskbits, gateway)
    
def str2net(netstr):
    """
    Convert a network string such as 10.0.0.0/8 to a network
    integer and a netmask
    """

    fields = netstr.split('/')
    addrstr = fields[0]
    if len(fields) > 1:
        maskbits = int(fields[1])
    else:
        maskbits = 32
        pass

    hostbits = 32 - maskbits
    mask = 0xFFFFFFFFL - ((1L << hostbits) - 1)
    maskstr = socket.inet_ntoa(struct.pack('!L',mask))

    addr = socket.inet_aton(addrstr)
    addr = long(struct.unpack('!I', addr)[0])
    addr = addr & mask

    return addrstr, maskstr, maskbits

def mask2bits(netmask):
    """
    Take a netmask and work out what number it
    would need on the righthand side of slash notation.
    eg: A netmask of 255.255.255.0 == /24
    """
    mask = socket.inet_aton(netmask)
    mask = long(struct.unpack('!I', mask)[0])

    bits = 0
    for byte in range(4):
        testval = (mask >> (byte * 8)) & 0xff
        while (testval != 0):
            if ((testval & 1) == 1):
                bits += 1
            testval >>= 1
    return bits        

def inverse_mask_str(netmaskstr):
    """
    Take a netmask and return the inverse mask, used for Cisco ACLs
    """
    maskint = long(struct.unpack('!I', socket.inet_aton(netmaskstr))[0])
    newmask = 0xFFFFFFFFL - maskint
    newmaskstr = socket.inet_ntoa(struct.pack('!L', newmask))
    return newmaskstr
