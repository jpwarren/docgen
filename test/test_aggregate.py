#
# $Id$
#
"""
Test Aggregates
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

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class AggregateTest(unittest.TestCase):
    """
    Test various aggregate configurations
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
      <vfiler name="vftest01">
        <aggregate type="root" name="aggr0"/>
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

    def test_bare_aggregate(self):
        """
        Test the simplest single aggregate node
        """
        xmldata = """
<aggregate>
</aggregate>
"""
        node = etree.fromstring(xmldata)
        self.failUnlessRaises(KeyError, aggregate.create_aggregate_from_node, node, self.defaults, self.vfiler1)

