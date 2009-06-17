## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Host related design objects.
Hosts are things like client servers that make use of storage.
"""

class Host:
    """
    A host definition
    """
    def __init__(self, name, platform, os, site, location, description='',
                 drhosts=[], interfaces=[], iscsi_initiator=None, is_virtual=False):

        self.name = name
        self.platform = platform
        self.os = os
        self.location = location
        self.description = description

        # drhosts is a reference to other hosts that will take on
        # this host's role in the event of a DR, and so they should
        # inherit the exports configuration for this host, but for the
        # DR targetvol of the snapmirrors for this host's volumes.
        self.drhosts = drhosts

        self.interfaces = interfaces
        #self.filesystems = filesystems

        self.iscsi_initiator = iscsi_initiator

        self.is_virtual = is_virtual
        
        log.debug("Created host: %s", self)

    def __str__(self):
        return "%s (%s, %s)" % (self.name, self.os, self.location)

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

class Filesystem:

    def __init__(self, type, name):

        self.type = type
        self.name = name

