 #
# $Id$
#
"""
Test SnapVaultSet
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project
from docgen.snapvaultset import SnapVaultSet

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class SnapVaultSetTest(unittest.TestCase):
    """
    Test SnapVaultSet objects
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        xmldata = """
<project name="testproj" code="01">
</project>
"""
        node = etree.fromstring(xmldata)
        self.project = Project()
        self.project.configure_from_node(node, self.defaults, None)

    def test_bare_snapvaultset(self):
        """
        Test a bare snapvaultset node
        """
        xmldata = """
<snapvaultset />
"""
        node = etree.fromstring(xmldata)
        sr = SnapVaultSet()
        self.failUnlessRaises( KeyError, sr.configure_from_node, node, self.defaults, self.project)

    def test_snapvaultset_id(self):
        """
        Test a snapvaultset with an id
        """
        xmldata = """
<snapvaultset name="default" />
"""
        node = etree.fromstring(xmldata)
        sr = SnapVaultSet()
        self.failUnlessRaises( KeyError, sr.configure_from_node, node, self.defaults, self.project)

    def test_snapvaultset_targetfiler(self):
        """
        Test a snapvaultset with targetfiler, but no targetaggregate
        """
        xmldata = """
<snapvaultset name="default" targetfiler="filer01" />
"""
        node = etree.fromstring(xmldata)
        sr = SnapVaultSet()
        self.failUnlessRaises( KeyError, sr.configure_from_node, node, self.defaults, self.project)

    def test_snapvaultset_targetaggr(self):
        """
        Test a snapvaultset with targetfiler and targetaggregate
        """
        xmldata = """
<snapvaultset name="default" targetfiler="filer01" targetaggregate="aggr02"/>
"""
        node = etree.fromstring(xmldata)
        sr = SnapVaultSet()
        sr.configure_from_node(node, self.defaults, self.project)

        self.failUnlessEqual( sr.name, 'default')
        self.failUnlessEqual( sr.targetfiler, 'filer01')
        self.failUnlessEqual( sr.targetaggregate, 'aggr02')
        self.failUnlessEqual( sr.targetvolume, None)
        
    def test_snapvaultset_targetvolume(self):
        """
        Test a snapvaultset with targetfiler and targetvolume
        """
        xmldata = """
<snapvaultset name="default" targetfiler="filer01" targetvolume="testvol03"/>
"""
        node = etree.fromstring(xmldata)
        sr = SnapVaultSet()
        sr.configure_from_node(node, self.defaults, self.project)

        self.failUnlessEqual( sr.name, 'default')
        self.failUnlessEqual( sr.targetfiler, 'filer01')
        self.failUnlessEqual( sr.targetaggregate, None)
        self.failUnlessEqual( sr.targetvolume, 'testvol03')
        
    def test_snapvaultset_multiplier(self):
        """
        Test setting a custom multipler for the snapvaultset
        """
        xmldata = """
<snapvaultset name="default"
              targetfiler="filer01"
              targetaggregate="aggr02"
              multiplier="3.4"/>
"""
        node = etree.fromstring(xmldata)
        sr = SnapVaultSet()
        sr.configure_from_node(node, self.defaults, self.project)

        self.failUnlessEqual( sr.name, 'default')
        self.failUnlessEqual( sr.multiplier, 3.4)
