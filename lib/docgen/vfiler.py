# $Id$
#

"""
VFiler object definition

"""
from docgen.base import XMLConfigurable, DynamicNaming

import debug
import logging
log = logging.getLogger('docgen')

class VFiler(XMLConfigurable, DynamicNaming):
    """
    A NetApp vFiler object
    """
    xmltag = 'vfiler'
    
    child_tags = [
        'protocol',
        'ipaddress',
        'aggregate',
        'volume',
        'nameserver',
        'winsserver',
        #'qtree',
        ]

    mandatory_attribs = [ 'name',
                          'rootaggr',
                          ]

    optional_attribs = [ 'netmask',
                         'dns_domain',
                         'ad_account_location',
                          ]
   
    def _depr__init__(self):
        self.name = ''
        self.children = {}
        
        self.filer = None
        self.rootaggr = None

        self.ipaddress = ipaddress
        self.netmask = netmask
        self.gateway = gateway
        self.vlan = vlan
        self.alias_ips = alias_ips
        self.volumes = []

        # We will need at least one additional 'services' VLAN
        # This will have a separate interface, IP address and gateway route
        # The format of each entry in the list is a tuple:
        # (vlan, ipaddress)
        self.services_ips = []

        #
        # CIFS related configuration stuff
        #
        self.dns_domain_name = dns_domain_name
        self.ad_account_location = ad_account_location

        self.nameservers = nameservers
        self.winsservers = winsservers
        
##         if self.filer.name.startswith('exip'):
##             self.nameservers = [ '161.117.218.175',
##                                  '161.117.245.73',
##                                  ]
##             self.winsservers = [ '161.117.218.175',
##                                  '161.117.245.73',
##                                  ]

##         elif self.filer.name.startswith('clip'):
##             self.nameservers = [ '161.117.245.73',
##                                  '161.117.218.175',
##                                  ]

##             self.winsservers = [ '161.117.245.73',
##                                  '161.117.218.175',
##                                  ]
##             pass

        self.netbios_aliases = []

        vfiler_key = '%s:%s' % (filer.name, name)
        filer.vfilers[vfiler_key] = self

    def as_string(self):
        """
        Dump vFiler config as a string
        """
        retstr = '<vFiler: %s, %s %s>' % (self.name, self.ipaddress, self.netmask)
        volume_strings = [ '  %s' % x for x in self.volumes ]
        return retstr

    def configure_from_node(self, node, defaults, filer):
        """
        Customise the configuration from a node slightly.
        """
        XMLConfigurable.configure_from_node(self, node, defaults, filer)
        self.filer = filer
        self.site = filer.site
    
    def populate_namespace(self, ns={}):
        ns = self.filer.populate_namespace(ns)
        ns['vfiler_name'] = self.name
        return ns
    
    def netbios_name(self):
        """
        Return my NetBIOS name.
        This is limited to 15 characters, which is a pain, so we
        have to cobble together yet another naming convention.
        This once is: XYnn-<vfiler-name>
        Where:
          X is 'ex' if the filer is at exhibition st, or 'cl' for clayton.
          Y is 'a' for filer head a, and 'B' for filer head b
          nn is the number of the filer.
        So, a vfiler called 'blah' on exip-fashda-01 would have the following
        NetBIOS name: exa01-blah
        """
        # Due to the naming convention for NearStores, the 'head_prefix'
        # ends up as 't'. We swap it to 'n' so that it's more obviously a
        # NearStore.
        site_prefix = self.filer.name[:2]
        if self.filer.type in [ 'primary', 'secondary' ]:
            head_prefix = 'f'
        else:
            head_prefix = 'n'            

        head_num = self.filer.name[-2:]

        retstr = '%s%s%s-%s' % (site_prefix, head_prefix, head_num, self.name)
        if len(retstr) > 15:
            log.warn("NetBIOS name of '%s' is longer than 15 characters. Truncating it.", retstr)
            retstr = retstr[:15]
            log.info("NetBIOS name is now '%s'", retstr)            
            pass

        log.debug("NetBIOS name: %s", retstr)
        return retstr

    def fqdn(self):
        """
        Return my fully qualified domain name.
        """
        return '%s.%s' % ( self.netbios_name(), self.dns_domain_name )

    def add_service_ip(self, vlan, ipaddress):
        self.services_ips.append( (vlan, ipaddress) )
    pass