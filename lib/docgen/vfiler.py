# $Id$
#

"""
VFiler object definition

"""
from ConfigParser import NoSectionError, NoOptionError

from lxml import etree

from base import DynamicNamedXMLConfigurable
# FIXME: Doing it this way means we can't override this in
# a user defined plugin. Need the lookup table instead.
from volume import Volume
from aggregate import Aggregate
from export import Export

import debug
import logging
log = logging.getLogger('docgen')

class VFiler(DynamicNamedXMLConfigurable):
    """
    A NetApp vFiler object
    """
    xmltag = 'vfiler'
    
    child_tags = [
        'protocol',
        'ipaddress',
        'aggregate',
        #'volume',
        'nameserver',
        'winsserver',
        #'qtree',
        ]

    mandatory_attribs = [ 
        ]

    optional_attribs = [
        'name',
        'netmask',
        'dns_domain',
        'ad_account_location',
        'vlan_number',
        ]

    def __init__(self):

        self.name = None
        self.filer = None
        self.site = None
        # We will need at least one additional 'services' VLAN
        # This will have a separate interface, IP address and gateway route
        # The format of each entry in the list is a tuple:
        # (vlan, ipaddress)
        self.services_ips = []

        # Which vlan I belong to, if any
        self.vlan = None

    def _depr__init__(self):
        self.name = ''
        self.children = {}
        
        self.filer = None
        self.rootaggr = None

        self.ipaddress = ipaddress
        self.netmask = netmask
        self.gateway = gateway
        self.vlan = vlan
        self.alias_ips = []
        self.volumes = []

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
        self.filer = filer
        self.site = filer.site

        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, filer)
        # Attempt to create a root aggregate if one hasn't
        # been defined manually
        self.create_root_aggregate(defaults)
        
        # Create a root volume if one hasn't been manually defined
        self.create_root_volume(defaults)


    def configure_optional_attributes(self, node, defaults):
        DynamicNamedXMLConfigurable.configure_optional_attributes(self, node, defaults)
        
        # If a vlan number is defined, use that vlan, otherwise
        # use the first project vlan we find.
        # FIXME: Need to cope with non-VLAN projects
        # Ticket: #48
        if self.vlan_number is not None:
            self.vlan = [ vlan for vlan in self.site.get_vlans() if vlan.number == self.vlan_number ][0]
        else:
            try:
                self.vlan = [ vlan for vlan in self.site.get_vlans() if vlan.type == 'project'][0]
            except IndexError:
                log.warn("No VLANs defined.")
                self.vlan = None
            pass

        if self.dns_domain is None:
            try:
                self.dns_domain = defaults.get('vfiler', 'default_dns_domain')
            except (NoSectionError, NoOptionError):
                pass

    def name_dynamically(self, defaults):
        if getattr(self, 'name', None) is None:
            # Name via naming convention
            ns = self.populate_namespace()
            naming_convention = defaults.get('vfiler', 'vfiler_name')
            self.name = naming_convention % ns
        
    def populate_namespace(self, ns={}):
        ns = self.filer.populate_namespace(ns)
        ns['vfiler_name'] = self.name
        return ns

    def get_filer(self):
        return self.filer

    def get_next_volnum(self):
        return self.filer.get_next_volnum()

    def set_volnum(self, num):
        return self.filer.set_volnum(self, num)

    def get_vlan(self):
        return self.vlan

    def get_primary_ipaddr(self):
        return [x for x in self.get_ipaddresss() if x.type == 'primary'][0]

    def get_alias_ipaddrs(self):
        return [x for x in self.get_ipaddresss() if x.type == 'alias']
    
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

    def get_volumes(self):
        """
        Find all the volumes on this vFiler
        """
        volumes = []
        for aggr in self.get_aggregates():
            volumes.extend(aggr.get_volumes())
            pass
        return volumes

    def get_qtrees(self):
        """
        Find all the qtrees on this vFiler        
        """
        qtrees = []
        for vol in self.get_volumes():
            qtrees.extend( vol.get_qtrees() )
            pass
        return qtrees
    
    def get_root_aggregate(self):
        """
        Get the root aggregate for the vfiler
        """
        try:
            aggrs = [ x for x in self.get_aggregates() ]
            log.debug("aggr: %s", aggrs)
            #aggrs = [ x for x in self.get_aggregates() if x.type == 'root' ]
            return aggrs[0]
        except IndexError:
            raise ValueError("No root aggregates defined for vfiler: %s:%s" % (self.filer.name, self.name))

    def create_root_aggregate(self, defaults):
        """
        If a root aggregate doesn't already exist, create one
        """
        try:
            aggr = self.get_root_aggregate()
            return
        except ValueError, valerr:
            try:
                root_aggr_name = defaults.get('vfiler', 'default_root_aggregate')
                xmldata = """<aggregate type="root" name="%s"/>""" % root_aggr_name
                node = etree.fromstring(xmldata)
                aggr = Aggregate()
                aggr.configure_from_node(node, defaults, self)
                self.add_child(aggr)
                
            except (NoSectionError, NoOptionError), e:
                raise valerr
        
    def create_root_volume(self, defaults):
        """
        Create a root volume for the vFiler if one hasn't
        been manually defined
        """
        log.debug("No manually defined root volume. Creating one...")
        ns = self.populate_namespace()
        try:
            volname = defaults.get('vfiler', 'root_volume_name') % ns
        except (NoSectionError, NoOptionError):
            volname = '%s_root' % self.name
            pass

        # FIXME: This can probably be improved somehow
        usable = float(defaults.get('vfiler', 'root_volume_usable'))
        aggr = self.get_root_aggregate()
        log.debug("got root aggr")
        xmldata = """<volume type="root" name="%s" usable="%s" raw="%s" />
        """ % ( volname, usable, usable )
        node = etree.fromstring(xmldata)
        vol = Volume()
        vol.configure_from_node(node, defaults, aggr)

        vol.snapreserve = int(defaults.get('vfiler', 'root_volume_snapreserve'))
        vol.space_guarantee = 'volume'

        if defaults.getboolean('vfiler', 'backup_root_volume'):
            log.warn("Request to back up vfiler root volume")

        log.debug("Root volume: %s", vol)
        # Add the volume as a child of the root aggregate
        aggr.add_child(vol)
        pass

    def get_allowed_protocols(self):
        """
        Get all the protocols defined for me, and
        turn them into pretty printed strings.
        """
        protos = self.get_protocols()
        # If protocols aren't defined manually, then just
        # allow all the protocols defined for volumes/qtrees
        if len(protos) == 0:
            for vol in self.get_volumes():
                if vol.protocol not in protos:
                    protos.append( vol.protocol )
                    pass
                pass
            pass
            
        return protos

    def get_exports(self):
        """
        Find all the export objects for this vFiler's volumes/qtrees
        """
        all_exports = []
        for vol in self.get_volumes():
            log.debug("Finding qtrees: %s", vol.get_qtrees())
            for qtree in vol.get_qtrees():
                log.debug("Finding exports")
                exports = qtree.get_exports()
                all_exports.extend( exports )
                pass
            pass
        return all_exports

    def setup_exports(self):
        """
        Set up all the exports for my volumes and qtrees
        """
        for vol in self.get_volumes():
            # FIXME:
            # Do we add default exports for volumes if they don't have any?
            # Do we even allow volume based exports?
            
            for qtree in vol.get_qtrees():
                exports = qtree.get_exports()

                # If a qtree doesn't have any exports, add the
                # default set of qtree exports.
                if len(exports) == 0:
                    for export in self.get_default_qtree_exports():
                        qtree.add_child(export)
                        pass
                    log.debug("Added default set of qtree exports to %s", qtree)
                    pass
                pass
            pass
        pass

    def get_site(self):
        return self.parent.get_site()
                    
    def get_default_qtree_exports(self):
        exports = [ Export(type='rw', tohost=host, fromip=self.get_primary_ipaddr().ip) for host in self.get_site().get_hosts() ]
        return exports
        
def create_vfiler_from_node(node, defaults, site):
    vf = VFiler()
    vf.configure_from_node(node, defaults, site)
    return vf
