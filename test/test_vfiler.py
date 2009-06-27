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
from docgen.config import ProjectConfig
from docgen.site import Site
from docgen.filer import Filer
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
        self.proj = ProjectConfig(self.defaults)

        self.site = Site()
        self.filer = Filer()
        self.filer.site = self.site

    def test_create_vfiler_bare(self):
        xmldata = """
<vfiler />
"""
        node = etree.fromstring(xmldata)
        vfiler = VFiler()
        self.failUnlessRaises(KeyError, vfiler.configure_from_node, node, self.defaults, self.filer)

    def test_create_vfiler_named(self):
        xmldata = """
<vfiler name="vftest01" />
"""
        node = etree.fromstring(xmldata)
        vfiler = VFiler()
        self.failUnlessRaises(KeyError, vfiler.configure_from_node, node, self.defaults, self.filer)

    def test_create_vfiler_minimal(self):
        xmldata = """
<vfiler name="vftest01" rootaggr="aggr0" />
"""
        node = etree.fromstring(xmldata)
        vfiler = VFiler()
        vfiler.configure_from_node(node, self.defaults, self.filer)

        self.failUnlessEqual( vfiler.name, "vftest01" )
        self.failUnlessEqual( vfiler.rootaggr, "aggr0" )

