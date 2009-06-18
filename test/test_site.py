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

from ConfigParser import SafeConfigParser

from docgen.options import BaseOptions
from docgen.config import ProjectConfig

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

        self.defaults = SafeConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.proj = ProjectConfig(self.defaults)

    def test_empty_site(self):
        """
        Test the simplest possible site configuration
        """
        xmldata = """
<site/>
"""
        node = etree.fromstring(xmldata)

