#
# $Id$
#
"""
Test LUNs
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project
from docgen import lun

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class LUNTest(unittest.TestCase):
    """
    Test various LUN configurations
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])
        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        self.project = Project()
        
    def test_bare_lun(self):
        """
        Test the simplest possible lun configuration
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'bare_lun.xml')
        tree = etree.parse(xmlfile)
        self.project.configure_from_node(tree.getroot(), self.defaults, None)

        # Find the lun
        vol = self.project.get_volumes()[1]
        lunobj = vol.get_luns()[0]
        self.assertEquals( lunobj.name, 'vftest01.lun00')
        self.assertEquals( lunobj.size, 100)
        self.assertEquals( lunobj.igroup.name, 'testproj00')
        
    def test_three_bare_luns(self):
        """
        Test three bare luns in the same volume/qtree
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'bare_lun_three.xml')
        tree = etree.parse(xmlfile)
        self.project.configure_from_node(tree.getroot(), self.defaults, None)

        # Find the lun
        vol = self.project.get_volumes()[1]

        lunobj = vol.get_luns()[0]
        self.assertEquals( lunobj.name, 'vftest01.lun00')
        self.assertEquals( int(lunobj.size), 33)
        self.assertEquals( lunobj.igroup.name, 'testproj00')
        
        lunobj = vol.get_luns()[2]
        self.assertEquals( lunobj.name, 'vftest01.lun02')
        self.assertEquals( int(lunobj.size), 33)
        self.assertEquals( lunobj.igroup.name, 'testproj00')
        
    def test_2vols_1lun_each(self):
        """
        2 volumes, each with 1 lun
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'lun_2vols_1lun_each.xml')
        tree = etree.parse(xmlfile)
        self.project.configure_from_node(tree.getroot(), self.defaults, None)

        # Find the lun
        vols = self.project.get_volumes()
        log.debug("vols: %s", vols)
        lunobj = vols[2].get_luns()[0]

        self.assertEquals( lunobj.name, 'vftest01.lun01')
        self.assertEquals( int(lunobj.size), 100)
        self.assertEquals( lunobj.igroup.name, 'testproj00')

    def test_lun_3vols_multiple_luns(self):
        """
        A more complex example with multiple aggregates, volumes, luns, qtrees
        """
        xmlfile = os.path.join(XML_FILE_LOCATION, 'lun_3vols_multiple_luns.xml')
        tree = etree.parse(xmlfile)
        self.project.configure_from_node(tree.getroot(), self.defaults, None)
