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
from docgen.site import Site
from docgen.host import Host
from docgen.vlan import Vlan
from docgen import netinterface

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class NetInterfaceTest(unittest.TestCase):
    """
    Test the Project class
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        self.site = Site('primary', 'prod', 'testlab')
        self.host = Host('fred', 'intel', 'linux', self.site)
        self.vlan1 = Vlan(1453, self.site, 'storage')
        self.vlan2 = Vlan(100, self.site, 'storage')
        self.vlan3 = Vlan(300, self.site, 'storage')
        self.site.children['vlan'] = [ self.vlan1,
                                       self.vlan2,
                                       self.vlan3,
                                       ]

    def test_create_netinterface_bare(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "netinterface_bare.xml")
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        #netinterface.create_netinterface_from_node(node, self.defaults, self.host)
        self.failUnlessRaises(KeyError, netinterface.create_netinterface_from_node, node, self.defaults, self.host)
        
    def test_create_netinterface_minimal(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "netinterface_minimal.xml")
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        iface = netinterface.create_netinterface_from_node(node, self.defaults, self.host)

    def test_create_netinterface_with_mtu(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "netinterface_with_mtu.xml")
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        iface = netinterface.create_netinterface_from_node(node, self.defaults, self.host)
        self.failUnlessEqual(iface.mtu, 3445)
    
    def test_create_netinterface_with_single_vlan(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "netinterface_with_single_vlan.xml")
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        iface = netinterface.create_netinterface_from_node(node, self.defaults, self.host)
        self.failUnlessEqual(len(iface.get_vlans()), 1)
        self.failUnlessEqual(iface.get_vlans()[0].number, 1453)
        
    def test_create_netinterface_with_multiple_vlan(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "netinterface_with_multiple_vlans.xml")
        tree = etree.parse(xmlfile)
        node = tree.getroot()
        iface = netinterface.create_netinterface_from_node(node, self.defaults, self.host)
        self.failUnlessEqual(len(iface.get_vlans()), 3)
