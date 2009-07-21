#
# $Id$
#
"""
Test Hosts
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.config import ProjectConfig

from docgen.site import Site
from docgen import host

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class HostTest(unittest.TestCase):
    """
    Test various host configurations
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.defaults.get('global', 'dns_domain_name')
        if len(configfiles) == 0:
            raise ValueError("Cannot load configuration file: %s" % optparser.options.configfile)

        self.proj = ProjectConfig(self.defaults)
        self.sitea = Site()
        self.sitea.name = 'sitea'
        self.sitea.type = 'primary'
        self.sitea.location = 'testlab'

    def test_empty_host(self):
        """
        Test an empty host node
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'host_empty.xml')
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        self.failUnlessRaises(KeyError, host.create_host_from_node, node, self.defaults, self.sitea)
        
    def test_named_host(self):
        """
        Test a host node with just a name
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'host_named.xml')
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        self.failUnlessRaises(KeyError, host.create_host_from_node, node, self.defaults, self.sitea)

    def test_named_host_os(self):
        """
        Test a host node with just a name
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'host_named_os.xml')
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        hostobj = host.create_host_from_node(node, self.defaults, self.sitea)
        self.failUnlessEqual(hostobj.name, 'fred')
        self.failUnlessEqual(hostobj.operatingsystem, 'Linux')

    def test_named_host_os_platform(self):
        """
        Test a host node with just a name
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'host_named_os_platform.xml')
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        hostobj = host.create_host_from_node(node, self.defaults, self.sitea)
        self.failUnlessEqual(hostobj.name, 'fred')
        self.failUnlessEqual(hostobj.operatingsystem, 'Linux')
        self.failUnlessEqual(hostobj.platform, 'intel')
