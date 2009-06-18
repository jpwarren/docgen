#
# $Id$
#
"""
Test parsing of XML files
"""
import os.path

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import SafeConfigParser
from StringIO import StringIO

from docgen.options import BaseOptions
from docgen.config import ProjectConfig

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class ParserTest(unittest.TestCase):
    """
    Test the ability to parse various XML files
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = SafeConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.defaults.get('global', 'dns_domain_name')
        log.debug("Loaded: %s", configfiles)
        if len(configfiles) == 0:
            raise ValueError("Cannot load configuration file: %s" % optparser.options.configfile)

    def test_parse_minimal(self):
        """
        Test parsing of minimal XML file
        """
        xmlfile = "minimal_parsable_config.xml"
        filepath = os.path.join(XML_FILE_LOCATION, xmlfile)
        proj = ProjectConfig(filepath, self.defaults)

    def test_parse_drhostexports(self):
        """
        Test parsing of dr host exports syntax
        """
        xmlfile = "drhostexport_test.xml"
        filepath = os.path.join(XML_FILE_LOCATION, xmlfile)
        proj = ProjectConfig(filepath, self.defaults)
        
    def test_parse_clustered_nearstore(self):
        """
        Test parsing of clustered nearstore syntax
        """
        xmlfile = "clustered_nearstore.xml"
        filepath = os.path.join(XML_FILE_LOCATION, xmlfile)
        proj = ProjectConfig(filepath, self.defaults)
