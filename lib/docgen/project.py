# $Id$
#

"""
DocGen Project definitions.

The <project/> node is the root of all DocGen projects,
and is used to dynamically configure and build the project
definition.
"""
from ConfigParser import NoSectionError, NoOptionError
from base import DynamicNamedXMLConfigurable

from lxml import etree

# FIXME: Doing it this way means we can't override this in
# a user defined plugin. Need the lookup table instead.
from volume import Volume

import debug
import logging
log = logging.getLogger('docgen')

class Project(DynamicNamedXMLConfigurable):
    """
    The core of the DocGen system: the Project
    """
    xmltag = 'project'
    child_tags = [ 'title', 'background', 'revision',
        'site', 'snapvaultset', 'snapmirrorset' ]

    mandatory_attribs = [ 'name', 'code' ]

    def populate_namespace(self, ns={}):
        """
        Add my namespace pieces to the namespace
        """
        ns['project_name'] = self.name
        ns['project_code'] = self.code
        return ns

    def get_volumes(self):
        """
        Find all the project volumes
        """
        volumes = []
        for site in self.get_sites():
            volumes.extend(site.get_volumes())
            pass
        return volumes

    def get_filers(self):
        filers = []
        for site in self.get_sites():
            filers.extend(site.get_filers())
            pass
        return filers

    def get_latest_revision(self):
        revlist = [ ('%s.%s' % (x.majornumber, x.minornumber), x) for x in self.get_revisions() ]
        revlist.sort()
        #log.debug("Last revision is: %s", revlist[-1])
        try:
            return revlist[-1][1]
        except IndexError:
            raise KeyError("No project revisions have been defined!")

    def get_project_vlan(self, site):
        """
        Find the project vlan for the site
        """
        vlan = [ vlan for vlan in site.get_vlans() if vlan.type == 'project' ][0]
        return vlan

    def get_services_vlans(self, site):
        """
        Return a list of all vlans of type 'services'
        """
        return [ vlan for vlan in site.get_vlans() if vlan.type == 'service' ]

    def configure_from_node(self, node, defaults, parent):
        DynamicNamedXMLConfigurable.configure_from_node(self, node, defaults, parent)

        self.create_vfiler_root_volumes(defaults)

    def create_vfiler_root_volumes(self, defaults):
        """
        All vFilers must have a root volume of some kind
        """
        for site in self.get_sites():
            for filer in site.get_filers():
                for vfiler in filer.get_vfilers():
                    # Do some post configuration processing
                    # If a root volume isn't manually defined, create one ourselves
                    if [ x for x in vfiler.get_volumes() if x.type == 'root' ] == []:
                        log.debug("No manually defined root volume. Creating one...")
                        ns = vfiler.populate_namespace()
                        try:
                            volname = defaults.get('vfiler', 'root_volume_name') % ns
                        except (NoSectionError, NoOptionError):
                            volname = '%s_root' % vfiler.name
                            pass

                        # FIXME: This can probably be improved somehow
                        usable = float(defaults.get('vfiler', 'root_volume_usable'))
                        aggr = vfiler.get_root_aggregate()
                        xmldata = """<volume type="root" name="%s" usable="%s" raw="%s" />
""" % ( volname, usable, usable )
                        node = etree.fromstring(xmldata)
                        vol = Volume()
                        vol.configure_from_node(node, defaults, aggr)

                        vol.snapreserve = int(defaults.get('vfiler', 'root_volume_snapreserve'))
                        vol.space_guarantee('volume')

                        if defaults.getboolean('vfiler', 'backup_root_volume'):
                            log.warn("Request to back up vfiler root volume")

                        log.debug("Root volume: %s", vol)
                        # Add the volume as a child of the root aggregate

                        aggr.add_child(vol)
