## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Host related design objects.
Hosts are things like client servers that make use of storage.
"""
from zope.interface import implements

from docgen.interfaces import IDynamicNaming, IXMLConfigurable
from docgen.base import XMLConfigurable, DynamicNaming

import logging
import debug
log = logging.getLogger('docgen')

class Host(XMLConfigurable):
    """
    A host definition
    """
    implements(IDynamicNaming)

    xmltag = 'host'
    
    def __init__(self, name, platform, os, site, location=None, description='',
                 drhostnames=[],
                 iscsi_initiator=None,
                 is_virtual=False,
                 hostnode=None):

        self.name = name
        self.platform = platform
        self.os = os
        self.site = site
        self.location = location
        self.description = description

        # drhosts is a reference to other hosts that will take on
        # this host's role in the event of a DR, and so they should
        # inherit the exports configuration for this host, but for the
        # DR targetvol of the snapmirrors for this host's volumes.
        self.drhostnames = drhostnames
        self.drhosts = []

        self.interfaces = []
        #self.filesystems = filesystems

        self.iscsi_initiator = iscsi_initiator

        self.is_virtual = is_virtual

        self.hostnode = hostnode
        
        log.debug("Created host: %s", self)

    def __str__(self):
        return "<Host: %s (%s, %s)>" % (self.name, self.os, self.location)

    def get_interfaces(self):
        return host.children['netinterface']

    def get_site(self):
        return self.site
    
    def get_storage_ips(self):
        """
        Find the IP address of the active storage interface(s).
        """
        #log.debug("Interfaces on %s: %s", self.name, self.interfaces)
        # Find the first 'storage' type interface that is 'active'
        ifacelist = [ x for x in self.interfaces if x.type == 'storage' and x.mode == 'active' ]

        iplist = [ int.ipaddress for int in ifacelist ]
        return iplist

##         try:
##             if ifacelist[0] is None:
##                 raise ValueError("Cannot find active Storage IP for host '%s'")
##             return ifacelist[0].ipaddress

##         except IndexError:
##             raise ValueError("Host '%s' has no storage IP addresses defined." % self.name)

    def populate_namespace(self, ns={}):
        ns = self.site.populate_namespace(ns)
        ns['host_name'] = self.name
        ns['host_os'] = self.os
        ns['host_platform'] = self.platform
        return ns

class Filesystem:

    def __init__(self, type, name):

        self.type = type
        self.name = name

def create_host_from_node(node, defaults, site):
    """
    Create a Host object from a node definition
    """
    # find some mandatory attributes
    try:
        hostname = node.attrib['name']
    except KeyError:
        raise KeyError("Host node has no 'name' attribute")

    host_attribs = {}
    for attribname in ['platform', 'operatingsystem']:
        try:
            host_attribs[attribname] = node.attrib[attribname]
        except KeyError, e:
            raise KeyError("Cannot find attribute '%s' for host '%s'" % (attribname, hostname))
        pass

    # If the location for the host is set, use that, else
    # default to the same location as the containing site
    try:
        location = node.attrib['location']
    except KeyError, e:
        location = site.location
        
    try:
        is_virtual = node.attrib['virtual']
        if is_virtual.lower() == 'yes':
            is_virtual=True
            log.debug("Host '%s' is virtual.", hostname)
        else:
            is_virtual=False
    except KeyError:
        is_virtual=False

    try:
        description = node.find('description').text
    except AttributeError:
        description = ''

    try:
        iscsi_initiator = node.find('iscsi_initiator').text
    except AttributeError:
        iscsi_initiator = None

    drhostnodes = node.findall('drhost')
    drhosts = [ host.attrib['name'] for host in drhostnodes ]

    host = Host(hostname, host_attribs['platform'],
                host_attribs['operatingsystem'],
                site, location, description, hostnode=node)
    
    # Load host interfaces, etc.
    host.configure_from_node(node, defaults, site)

    return host
