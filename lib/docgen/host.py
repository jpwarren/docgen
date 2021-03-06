## $Id$

"""
Host related design objects.
Hosts are things like client servers that make use of storage.
"""
from docgen.base import DynamicNamedXMLConfigurable

import logging
import debug
log = logging.getLogger('docgen')

class Host(DynamicNamedXMLConfigurable):
    """
    A host definition
    """
    xmltag = 'host'

    child_tags = [
        'netinterface',
        #'drhost',
        ]

    mandatory_attribs = [
        'name',
        'operatingsystem',
        ]
    
    optional_attribs = [
        'platform',
        'description',
        'location',
        'is_virtual',
        'iscsi_initiator',
        ]

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        # Add drhost bits, if available.
        # This is done here, rather than as a separate object,
        # to avoid a separate class that may not really be necessary
        self.children['drhostname'] = [x.attrib['name'] for x in node.findall('drhost')]

    def get_drhostnames(self):
        return self.children['drhostname']

    def get_drhosts(self):
        return self.children['drhost']
    
    def _configure_mandatory_attributes(self, node, defaults):
#         if getattr(self, 'name', None) is None:
#             raise KeyError("Host does not have 'name' set")

#         if getattr(self, 'operatingsystem', None) is None:
#             raise KeyError("Host '%s' does not have 'operatingsystem' set" % self.name)
        DynamicNamedXMLConfigurable.configure_mandatory_attributes(self, node, defaults)

        
    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)

        # If the location for the host is set, use that, else
        # default to the same location as the containing site
        if self.location is None:
            location = self.parent.location

        # Is the host virtual or physical?
        if self.is_virtual is None:
            self.is_virtual = False
        elif self.is_virtual.lower() == 'yes':
            self.is_virtual = True
            log.debug("Host '%s' is virtual.", hostname)
        else:
            self.is_virtual = False
    
    def _depr__init__(self, name, platform, os, site, location=None, description='',
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
        return "<Host: %s>" % (self.name, )

    def get_interfaces(self):
        return host.children['netinterface']

    def get_site(self):
        return self.parent
    
    def get_storage_ips(self):
        """
        Find the IP address(es) of the active storage interface(s).
        """
        #log.debug("Interfaces on %s: %s", self.name, self.interfaces)
        # Find the first 'storage' type interface that is 'active'
        ifacelist = [ x for x in self.get_netinterfaces() if x.type == 'storage' and x.mode == 'active' ]

        iplist = []
        for iface in ifacelist:
            iplist.extend( iface.get_ipaddresss() )
            pass
        return iplist

##         try:
##             if ifacelist[0] is None:
##                 raise ValueError("Cannot find active Storage IP for host '%s'")
##             return ifacelist[0].ipaddress

##         except IndexError:
##             raise ValueError("Host '%s' has no storage IP addresses defined." % self.name)

    def populate_namespace(self, ns={}):
        ns = self.parent.populate_namespace(ns)
        ns['host_name'] = self.name
        ns['host_os'] = self.operatingsystem
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
    host = Host()
    # Load host interfaces, etc.
    host.configure_from_node(node, defaults, site)
    return host
