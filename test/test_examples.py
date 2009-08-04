#
# $Id$
#
"""
Test the example definitions provided with the code
"""
import os.path
from ConfigParser import RawConfigParser, NoSectionError

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from docgen.options import BaseOptions
from docgen.project import Project

from docgen import debug
import logging
log = logging.getLogger('docgen')

XML_FILE_LOCATION = sibpath(__file__, os.path.join("..", "doc", "examples"))
TESTCONF = sibpath(__file__, "docgen_test.conf")

class ExampleTest(unittest.TestCase):

    def setUp(self):
        """
        Prepare for a configuration parse test
        """
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        self.project = Project()

    def test_working(self):
        self.failUnlessEqual( 1, 1 )

    def test_basic_example(self):
        """
        Test the general example file
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, "EXAMPLE.project-definition.xml")
        tree = etree.parse(xmlfile)
        self.project.configure_from_node(tree.getroot(), self.defaults, None)        
    def test_multi_network_example(self):
        """
        Test the general example file
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, "EXAMPLE.multi-network-vlan.project-definition.xml")
        tree = etree.parse(xmlfile)
        self.project.configure_from_node(tree.getroot(), self.defaults, None)        
