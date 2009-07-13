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
from docgen.project import Project
from docgen.background import Background

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class BackgroundTest(unittest.TestCase):
    """
    Test the Background class 
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        xmldata = """<project name="testproj1" code="01" title="Test Project 1"/>
"""
        self.project = Project()

    def test_empty_background(self):
        xmldata = """
<background>
</background>
"""
        node = etree.fromstring(xmldata)
        bg = Background()
        bg.configure_from_node(node, self.defaults, self.project)
        astext = bg.get_docbook()
        self.failUnlessEqual(astext, "<background>\n</background>")

    def test_minimal_background(self):
        xmldata = """
<background>
  <para>This is a dummy description for testing.</para>
</background>
"""
        node = etree.fromstring(xmldata)
        bg = Background()
        bg.configure_from_node(node, self.defaults, self.project)
        astext = bg.get_docbook()
        self.failUnlessEqual(astext, "<background>\n  <para>This is a dummy description for testing.</para>\n</background>")
