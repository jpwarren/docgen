#
# $Id$
#
"""
Test VFilers
"""
import os.path
from ConfigParser import RawConfigParser, NoSectionError
from StringIO import StringIO

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from lxml import etree

from docgen.options import BaseOptions
from docgen.project import Project
from docgen.vfiler import VFiler

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class VFilerTest(unittest.TestCase):
    """
    Test the VFiler class
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        xmldata = """
<project name="demo" code="3">
  <site name="one" type="primary" location="somewhere">
    <vlan number="3001" type="project"/>
    <filer name="testfiler1" type="filer">
    </filer>
  </site>
</project>
"""
        node = etree.fromstring(xmldata)
        self.project = Project()
        self.project.configure_from_node(node, self.defaults, None)
        self.site = self.project.get_sites()[0]
        self.filer = self.site.get_filers()[0]

    def test_create_vfiler_bare(self):
        """
        A bare vfiler with full default options
        """
        xmldata = """
<vfiler />
"""
        node = etree.fromstring(xmldata)
        vfiler = VFiler()
        vfiler.configure_from_node(node, self.defaults, self.filer)
        self.failUnlessEqual( vfiler.name, "vfdemo" )
        rootaggr = vfiler.get_root_aggregate()
        self.failUnlessEqual( rootaggr.name, "rootaggr" )
        
    def test_create_vfiler_minimal(self):
        xmldata = """
<vfiler name="vftest01" />
"""
        node = etree.fromstring(xmldata)
        vfiler = VFiler()
        vfiler.configure_from_node(node, self.defaults, self.filer)

        self.failUnlessEqual( vfiler.name, "vftest01" )
        rootaggr = vfiler.get_root_aggregate()
        self.failUnlessEqual( rootaggr.name, "rootaggr" )
