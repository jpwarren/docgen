#
# $Id$
#
"""
Test the configuration loader
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

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class FilerTest(unittest.TestCase):
    """
    Test the Filer class
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.proj = ProjectConfig(self.defaults)

        self.site = Site()
        self.site.name = "testsite"
        self.site.type = "primary"
        self.site.locaion = "testlab"

    def test_create_filer_bare(self):
        xmldata = """
<filer />
"""
        node = etree.fromstring(xmldata)
        filer = Filer()
        self.failUnlessRaises(KeyError, filer.configure_from_node, node, self.defaults, self.site)

    def test_create_filer_named(self):
        xmldata = """
<filer name="testfiler1" />
"""
        node = etree.fromstring(xmldata)
        filer = Filer()
        filer.configure_from_node(node, self.defaults, self.site)
        
        self.failUnlessEqual( filer.name, "testfiler1" )
        self.failUnlessEqual( filer.type, "filer" )

        #self.failUnlessRaises(KeyError, filer.configure_from_node, node, self.defaults, self.site)

    def test_create_filer_minimal(self):
        xmldata = """
<filer name="testfiler1" type="filer" />
"""
        node = etree.fromstring(xmldata)
        filer = Filer()
        filer.configure_from_node(node, self.defaults, self.site)

        self.failUnlessEqual( filer.name, "testfiler1" )
        self.failUnlessEqual( filer.type, "filer" )

    def test_create_filer_nearstore(self):
        xmldata = """
<filer name="testfiler1" type="nearstore" />
"""
        node = etree.fromstring(xmldata)
        filer = Filer()
        filer.configure_from_node(node, self.defaults, self.site)

        self.failUnlessEqual( filer.name, "testfiler1" )
        self.failUnlessEqual( filer.type, "nearstore" )

    def test_create_filer_bad_type(self):
        xmldata = """
<filer name="testfiler1" type="secondary" />
"""
        node = etree.fromstring(xmldata)
        filer = Filer()
        self.failUnlessRaises(ValueError, filer.configure_from_node, node, self.defaults, self.site)

    def test_filer_site_correct(self):
        """
        Test the filer's site is set correctly
        """
        xmldata = """
<filer name="testfiler1" type="filer" />
"""
        node = etree.fromstring(xmldata)
        filer = Filer()
        filer.configure_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(filer.site.name, 'testsite')
