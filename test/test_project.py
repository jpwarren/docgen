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
from docgen.config import ProjectConfig
from docgen.project import Project

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class ProjectTest(unittest.TestCase):
    """
    Test the Project class
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.proj = ProjectConfig(self.defaults)

    def test_create_project_bare(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_bare.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        
    def test_create_project_1_site(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_1_site.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        # see if the convenience functions are set correctly
        self.failUnlessEqual( len(project.get_sites()), 1)
        
    def test_create_project_multiple_sites(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_multiple_sites.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        self.failUnlessEqual( len(project.get_sites()), 3)
        
    def test_create_project_1_site_vlans(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_1_site_vlans.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        self.failUnlessEqual( len(project.get_sites()), 1)

        site = project.get_sites()[0]
        vlans = project.get_sites()[0].get_vlans()
        self.failUnlessEqual( len(vlans), 1)
        
    def test_create_project_1_site_multiple_vlans(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_1_site_multiple_vlans.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        self.failUnlessEqual( len(project.get_sites()), 1)

        site = project.get_sites()[0]
        vlans = project.get_sites()[0].get_vlans()
        self.failUnlessEqual( len(vlans), 3)
        
    def test_create_project_1_site_1_host(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_1_site_1_host.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        self.failUnlessEqual( len(project.get_sites()), 1)
        site = project.get_sites()[0]
        hosts = project.get_sites()[0].get_hosts()
        self.failUnlessEqual( len(hosts), 1)
        
    def test_create_project_1_site_3_hosts(self):
        xmlfile = os.path.join(XML_FILE_LOCATION, "project_1_site_3_hosts.xml")
        tree = etree.parse(xmlfile)
        project = Project()
        project.configure_from_node(tree.getroot(), self.defaults, self.proj)
        self.failUnlessEqual( len(project.get_sites()), 1)
        site = project.get_sites()[0]
        hosts = project.get_sites()[0].get_hosts()
        self.failUnlessEqual( len(hosts), 3)
