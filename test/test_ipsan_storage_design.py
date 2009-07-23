#
# $Id$
#
"""
Test emitting the NetApp commands required to activate
a variety of project definitions.
"""
import os.path
from StringIO import StringIO
from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser
from StringIO import StringIO

from docgen.options import BaseOptions
from docgen.project import Project
from docgen.docplugins.ipsan_storage import IPSANStorageDesignGenerator

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class NetAppTestBase(unittest.TestCase):
    """
    Common basecode setup for testing design output
    """
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.outfile = StringIO()

    def load_testfile(self, filename):
        """
        Load a test file for verifying functionality
        """
        filepath = os.path.join(XML_FILE_LOCATION, filename)
        tree = etree.parse(filepath)

        self.project = Project()
        self.project.configure_from_node(tree.getroot(), self.defaults, None)
        self.docgenerator = IPSANStorageDesignGenerator(self.project, self.defaults)

class NetAppStorageDesign(NetAppTestBase):
    """
    Test the ability to emit a NetApp storage design document
    """
    def test_minimal(self):
        """
        Test parsing of minimal XML file
        """
        self.load_testfile("minimal_parsable_config.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')

    def test_simple(self):
        """
        Test parsing of simple project config
        """
        self.load_testfile("simple_single_site.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')
        
    def test_parse_drhostexports(self):
        """
        Test parsing of dr host exports syntax
        """
        self.load_testfile("drhostexport_test.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')

    def test_parse_clustered_nearstore(self):
        """
        Test parsing of clustered nearstore syntax
        """
        self.load_testfile("clustered_nearstore.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')
        
