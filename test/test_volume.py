#
# $Id$
#
"""
Test Volumes
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project
from docgen import volume

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class VolumeTest(unittest.TestCase):
    """
    Test various volume configurations
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])
        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        xmldata = """
<project name="testproj" code="01">
  <site name="sitea" type="primary" location="testlab">
    <filer name="filer1" type="filer">
      <vfiler name="vftest01" rootaggr="aggr0">
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

    def test_line_volume(self):
        """
        Test the simplest possible volume configuration
        """
        xmldata = """
<volume>
</volume>
"""
        node = etree.fromstring(xmldata)
        vol = volume.create_volume_from_node(node, self.defaults, self.aggr1)
        self.failUnlessEqual(vol.name, "filer1_vftest01_fs_01")
        
    def test_simple_volume(self):
        """
        Test the simplest possible volume configuration
        """
        xmldata = """
<filer name='testfiler1'>
  <aggregate name='testaggr01'>
    <volume>
    </volume>
  </aggregate>
</filer>
"""
        node = etree.fromstring(xmldata)
        volnode = node.xpath('*/volume')[0]
        volume.create_volume_from_node(volnode, self.defaults, self.aggr1)
