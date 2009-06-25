#
# $Id$
#
"""
Test the configuration loader
"""
import os.path
from ConfigParser import SafeConfigParser, NoSectionError
from StringIO import StringIO

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from lxml import etree

from docgen.options import BaseOptions
from docgen.config import ProjectConfig

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class ProjectConfigTest(unittest.TestCase):
    """
    Test the ProjectConfig class
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = SafeConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.proj = ProjectConfig(self.defaults)

class SiteTest(ProjectConfigTest):
    """
    Test loading of sites
    """
        
    def test_single_site(self):
        """
        Test loading of single site
        """
        xmldata = """
<project>
  <site name="sitea" type="primary"/>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        sites = self.proj.load_sites()
        self.failUnlessEqual( len(sites), 1 )
        
    def test_non_default_site(self):
        """
        Test load of site without defaults
        """
        xmldata = """
<project>
  <site name="fred" type="primary"/>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        self.failUnlessRaises(NoSectionError, self.proj.load_sites)

    def test_non_default_manual_site(self):
        """
        Test load of site completely manually defined
        """
        xmldata = """
<project>
  <site name="fred" type="primary" location="labtest" />
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        sites = self.proj.load_sites()
        
        self.failUnlessEqual( len(sites), 1 )
        mysite = sites['fred']
        
    def test_multiple_sites(self):
        """
        Test loading of multiple sites
        """
        xmldata = """
<project>
  <site name="sitea" type="primary"/>
  <site name="siteb" type="dr"/>
  <site name="sitec" type="demo" location="labtest"/>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        sites = self.proj.load_sites()
        self.failUnlessEqual( len(sites), 3 )

class VlanTest(ProjectConfigTest):
    """
    Test loading of vlans
    """
        
    def test_incorrect_vlan_place(self):
        """
        Test loading of project with vlan in the wrong place
        """
        xmldata = """
<project>
  <vlan number='14' />
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        vlans = self.proj.load_vlans()
        self.failUnlessEqual( len(vlans), 0 )

    def test_load_single_vlan(self):
        """
        Test loading of single vlan
        """
        xmldata = """
<project>
  <site name='test1' type='testing' location='testlab'>
    <vlan number='14' type='project' />
  </site>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        vlans = self.proj.load_vlans()
        self.failUnlessEqual( len(vlans), 1 )

    def test_load_multiple_vlans(self):
        """
        Test loading of single vlan
        """
        xmldata = """
<project>
  <site name='test1' type='testing' location='testlab'>
    <vlan number='14' type='project' />
    <vlan number='865' type='project' />
    <vlan number='1004' type='service' />
  </site>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        vlans = self.proj.load_vlans()
        self.failUnlessEqual( len(vlans), 3 )

class HostTest(ProjectConfigTest):
    """
    Test loading of Hosts
    """
    def test_host_wrong_place(self):
        """
        Test host node in the wrong place
        """
        xmldata = """
<project>
  <host />
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        self.failUnlessRaises(ValueError, self.proj.load_hosts)
    
    def test_single_host_no_name(self):
        """
        Test loading of single host with no name
        """
        xmldata = """
<project>
  <site name="fred" type="testing" location="testlab">
    <host />
  </site>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        self.failUnlessRaises(KeyError, self.proj.load_hosts)

    def test_single_host(self):
        """
        Test loading of single host
        """
        raise unittest.SkipTest("config.py testing may be decommissioned.")
        xmldata = """
<project>
  <site name="fred" type="testing" location="testlab">
    <host name="dummy1" platform="intel" operatingsystem="linux"/>
  </site>
</project>
"""
        tree = etree.fromstring(xmldata)
        self.proj.tree = tree
        hosts = self.proj.load_hosts()
        self.failUnlessEqual( len(hosts), 3 )
