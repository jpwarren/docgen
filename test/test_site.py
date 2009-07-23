#
# $Id$
#
"""
Test Sites
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class Site(unittest.TestCase):
    """
    Test various site configurations
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
        <aggregate name="aggr01"/>
      </vfiler>
    </filer>
  </site>
</project>
"""
        node = etree.fromstring(xmldata)
        self.project = Project()
        self.project.configure_from_node(node, self.defaults, None)

    def test_empty_site(self):
        """
        Test the simplest possible site configuration
        """
        xmldata = """
<site/>
"""
        node = etree.fromstring(xmldata)

