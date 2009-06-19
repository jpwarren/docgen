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
from docgen.config import ProjectConfig
from docgen.site import Site
from docgen.filer import Filer, VFiler
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
        self.proj = ProjectConfig(self.defaults)
        sitea = Site('sitea', 'primary')
        self.proj.sites[sitea.name] = sitea
        self.filer1 = Filer('testfiler1', 'filer', sitea)
        self.proj.filers[self.filer1.name] = self.filer1

        self.vfiler1 = VFiler(self.filer1, 'vfiler01', 'aggr0', '10.20.30.10', '10.20.30.1')

    def test_line_volume(self):
        """
        Test the simplest possible volume configuration
        """
        xmldata = """
<volume>
</volume>
"""
        node = etree.fromstring(xmldata)
        self.failUnlessRaises(IndexError, volume.create_volume_from_node, node, self.defaults, 0, self.filer1, self.vfiler1)

    def test_no_aggregate_volume(self):
        """
        Test the simplest possible volume configuration
        """
        xmldata = """
<filer name='testfiler1'>
  <volume>
  </volume>
</filer>
"""
        node = etree.fromstring(xmldata)
        volnode = node.find('volume')
        self.failUnlessRaises(IndexError, volume.create_volume_from_node, volnode, self.defaults, 0, self.filer1, self.vfiler1)
        
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
        volume.create_volume_from_node(volnode, self.defaults, 0, self.filer1, self.vfiler1)
