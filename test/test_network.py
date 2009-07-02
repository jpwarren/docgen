#
# $Id$
#
"""
Test Network elements
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
from docgen.filer import Filer
from docgen.vfiler import VFiler
from docgen.volume import Volume
from docgen import network
from docgen import vlan

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class NetworkTest(unittest.TestCase):
    """
    Test network elements
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        self.site = Site()
        self.site.name = 'sitea'
        self.site.type = 'primary'
        self.site.location = 'testlab'
        pass
    
    def test_create_network(self):
        """
        Test a basic network creation
        """
        xmldata = """
<network number="192.168.1.0/24" gateway="192.168.1.1"/>
"""
        
        node = etree.fromstring(xmldata)
        net = network.create_network_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(net.number, '192.168.1.0')
        self.failUnlessEqual(net.maskbits, 24)
        self.failUnlessEqual(net.netmask, '255.255.255.0')
        self.failUnlessEqual(net.gateway, '192.168.1.1')

    def test_create_network_2(self):
        """
        Second network test
        """
        xmldata = """
<network number="10.45.7.0/13" gateway="10.77.3.4"/>
"""
        
        node = etree.fromstring(xmldata)
        net = network.create_network_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(net.number, '10.45.7.0')
        self.failUnlessEqual(net.maskbits, 13)
        self.failUnlessEqual(net.netmask, '255.248.0.0')
        self.failUnlessEqual(net.gateway, '10.77.3.4')

    def test_create_network_netmask(self):
        """
        Test creating a network using netmask syntax
        """
        xmldata = """
<network number="10.45.7.0" netmask="255.255.248.0" gateway="10.77.7.99"/>
"""
        
        node = etree.fromstring(xmldata)
        net = network.create_network_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(net.number, '10.45.7.0')
        self.failUnlessEqual(net.maskbits, 21)
        self.failUnlessEqual(net.netmask, '255.255.248.0')
        self.failUnlessEqual(net.gateway, '10.77.7.99')
        
class VlanTest(unittest.TestCase):
    """
    Test VLANs
    """
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])
        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        self.site = Site()
        self.site.name = 'sitea'
        self.site.type = 'primary'
        self.site.location = 'testlab'
        pass
    
    def test_create_vlan_blank(self):
        """
        Test Vlan object creation
        """
        vlanobj = vlan.Vlan()

    def test_create_basic_vlan(self):
        xmldata = """
<site name='primary' type='primary'>
  <vlan type='project' number='2006'/>
</site>
"""
        tree = etree.fromstring(xmldata)
        node = tree.find('vlan')
        vlanobj = vlan.create_vlan_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(vlanobj.site, self.site)
        self.failUnlessEqual(vlanobj.type, 'project')
        self.failUnlessEqual(vlanobj.number, 2006)
        self.failUnlessEqual(len(vlanobj.get_networks()), 0)
        
    def test_create_vlan_with_1_network(self):
        """
        Test creation of a VLAN with 1 network
        """        
        xmldata = """
<site name='primary' type='primary'>
  <vlan type='project' number='2006'>
    <network number="10.23.34.0/27" gateway="10.23.34.1"/>
  </vlan>
</site>
"""
        tree = etree.fromstring(xmldata)
        node = tree.find('vlan')
        vlanobj = vlan.create_vlan_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(vlanobj.site, self.site)
        self.failUnlessEqual(vlanobj.type, 'project')
        self.failUnlessEqual(vlanobj.number, 2006)
        self.failUnlessEqual(len(vlanobj.get_networks()), 1)

    def test_create_vlan_with_3_networks(self):
        """
        Test creation of a VLAN with 1 network
        """        
        xmldata = """
<site name='primary' type='primary'>
  <vlan type='project' number='2006'>
    <network number="10.23.34.0/27" gateway="10.23.34.1"/>
    <network number="10.84.34.0/27" gateway="10.23.34.1"/>
    <network number="10.97.34.0/27" gateway="10.23.34.1"/>
  </vlan>
</site>
"""
        tree = etree.fromstring(xmldata)
        node = tree.find('vlan')
        vlanobj = vlan.create_vlan_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(vlanobj.site, self.site)
        self.failUnlessEqual(vlanobj.type, 'project')
        self.failUnlessEqual(vlanobj.number, 2006)
        self.failUnlessEqual(len(vlanobj.get_networks()), 3)

    def test_create_vlan_with_mtu(self):
        """
        Test creation of a VLAN with non-default MTU
        """        
        xmldata = """
<site name='primary' type='primary'>
  <vlan type='project' number='2006' mtu='4453'>
    <network number="10.23.34.0/27" gateway="10.23.34.1"/>
    <network number="10.84.34.0/27" gateway="10.23.34.1"/>
  </vlan>
</site>
"""
        tree = etree.fromstring(xmldata)
        node = tree.find('vlan')
        vlanobj = vlan.create_vlan_from_node(node, self.defaults, self.site)

        self.failUnlessEqual(vlanobj.site, self.site)
        self.failUnlessEqual(vlanobj.type, 'project')
        self.failUnlessEqual(vlanobj.number, 2006)
        self.failUnlessEqual(vlanobj.get_mtu(), 4453)
        self.failUnlessEqual(len(vlanobj.get_networks()), 2)
