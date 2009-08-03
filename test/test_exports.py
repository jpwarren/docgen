#
# $Id$
#
"""
Test storage exports
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project
from docgen import aggregate
from docgen import volume

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class ExportTest(unittest.TestCase):
    """
    Test various export configurations
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])
        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        xmldata = """
<project name="testproj" code="01">
  <site name="sitea" type="primary" location="testlab">

  <host name="sitea_host01" operatingsystem="linux" />
  <host name="sitea_host02" operatingsystem="windows" />
  <host name="sitea_host03" operatingsystem="solaris" />

  <vlan type="project" number="3001">
    <network number="10.20.30.1/26" gateway="10.20.30.254"/>
  </vlan>
    <filer name="filer1" type="filer">
      <vfiler name="vftest01" rootaggr="aggr0">
        <ipaddress type="primary" ip="10.20.30.1"/>
        <aggregate name="aggr01"/>
      </vfiler>
    </filer>
  </site>
</project>
"""
        node = etree.fromstring(xmldata)
        self.project = Project()
        self.project.configure_from_node(node, self.defaults, None)

        self.sitea = self.project.get_sites()[0]
        self.filer1 = self.sitea.get_filers()[0]
        self.vfiler1 = self.filer1.get_vfilers()[0]
        self.aggr1 = self.vfiler1.get_aggregates()[0]

    def test_default_exports(self):
        """
        Test a single volume and the default exports.
        """
        xmldata = """
<volume>
</volume>
"""
        node = etree.fromstring(xmldata)
        vol = volume.create_volume_from_node(node, self.defaults, self.aggr1)
        self.aggr1.add_child(vol)
        self.failUnlessEqual(vol.name, "filer1_vftest01_fs_01")

        self.project.setup_exports(self.defaults)
        
        # check the exports are set up correctly
        for qtree in self.vfiler1.get_qtrees():
            exports = qtree.get_exports()
            log.debug("exports: %s", [ str(x) for x in exports ])
            self.failUnlessEqual( len(exports), 3 )
            self.failUnlessEqual( exports[0].fromip, '10.20.30.1' )

    def test_default_exports_2(self):
        """
        Test a two volumes and the default exports.
        """
        xmldata = """
<volume/>
"""
        node = etree.fromstring(xmldata)
        vol = volume.create_volume_from_node(node, self.defaults, self.aggr1)
        self.aggr1.add_child(vol)
        vol = volume.create_volume_from_node(node, self.defaults, self.aggr1)
        self.aggr1.add_child(vol)

        self.failUnlessEqual(vol.name, "filer1_vftest01_fs_02")

        self.project.setup_exports(self.defaults)

        # check the exports are set up correctly
        for qtree in self.vfiler1.get_qtrees():
            exports = qtree.get_exports()
            log.debug("exports: %s", [ str(x) for x in exports ])
            self.failUnlessEqual( len(exports), 3 )
            self.failUnlessEqual( exports[0].fromip, '10.20.30.1' )

    def test_qtree_default(self):
        """
        Test a single volume and the default exports.
        """
        xmldata = """
<volume>
  <qtree name="blahblah"/>
</volume>
"""
        node = etree.fromstring(xmldata)
        vol = volume.create_volume_from_node(node, self.defaults, self.aggr1)
        self.aggr1.add_child(vol)
        self.failUnlessEqual(vol.name, "filer1_vftest01_fs_01")

        self.project.setup_exports(self.defaults)

        # check the exports are set up correctly
        for qtree in self.vfiler1.get_qtrees():
            exports = qtree.get_exports()
            log.debug("exports: %s", [ str(x) for x in exports ])
            self.failUnlessEqual( len(exports), 3 )
            self.failUnlessEqual( exports[0].fromip, '10.20.30.1' )
        
