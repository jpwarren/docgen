 #
# $Id$
#
"""
Test snapvault configuration
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project
from docgen.snapvaultset import SnapVaultSet
from docgen.docplugins.netapp_commands import NetAppCommandsGenerator

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class SnapVaultTest(unittest.TestCase):
    """
    Test SnapVault configurations
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        xmldata = """
<project name="testproj" code="01">
  <site name="testprimary" type="primary">
    <vlan type="project" number="3003">
      <network number="10.240.4.0/26" gateway="10.240.4.254"/>
    </vlan>

    <filer type="filer" name="filer01">
      <vfiler>
        <ipaddress type="primary" ip="10.240.4.1"/>
        <aggregate name="aggr01" type="root"/>

	<aggregate name="aggr02">
          <volume>
            <setref type="snapvault" name="default_primary"/>
          </volume>
        </aggregate>

      </vfiler>
    </filer>

    <filer type="nearstore" name="nearstore01">

    </filer>

  </site>

  <snapvaultset name="default_primary" targetfiler="nearstore01" targetaggregate="aggr02">
    <snapvaultdef basename="sv_daily">
      <snapschedule>1@1</snapschedule>
      <snapvaultschedule>8@2</snapvaultschedule>
    </snapvaultdef>
    <snapvaultdef basename="sv_weekly">
      <snapvaultschedule>13@sun@3</snapvaultschedule>
    </snapvaultdef>
  </snapvaultset>

</project>
"""
        node = etree.fromstring(xmldata)
        self.project = Project()
        self.project.configure_from_node(node, self.defaults, None)

        self.docgen = NetAppCommandsGenerator(self.project, self.defaults)

    def test_aggregates_exist(self):
        """
        Check that all the right aggregates exist
        """
        aggregates = []
        for filer in self.project.get_filers():
            log.debug("adding aggregates on filer: %s: %s", filer, filer.get_aggregates())
            aggregates.extend( filer.get_aggregates() )
            pass

        self.failUnlessEqual( len(aggregates), 3)
        
    def test_volumes_exist(self):
        """
        Test the snapvault volumes exist
        """
        vols = self.project.get_volumes()
        log.debug("vols: %s", [x for x in vols])

        for vol in vols:
            log.debug("snapvaults: %s", vol.snapvaults)
            for snap in vol.snapvaults:
                log.debug("snap: %s", snap)
                pass
            pass

        filer = [ x for x in self.project.get_filers() if x.name == 'nearstore01'][0]
        cmds = self.docgen.filer_snapvault_init_commands(filer)
        log.debug("cmds: %s", cmds)
        self.failUnlessEqual( len(cmds), 1 )

