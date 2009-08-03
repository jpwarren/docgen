#
# $Id$
#
"""
Test that exports from primary hosts are also provided to DR hosts.
"""
import os.path
from ConfigParser import RawConfigParser, NoSectionError

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from docgen.options import BaseOptions
from docgen.project import Project

from docgen import debug
import logging
log = logging.getLogger('docgen')

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class DRHostExportTest(unittest.TestCase):

    def setUp(self):
        """
        Load testing XML into a config instance.
        """
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)

        xmlfile = os.path.join(XML_FILE_LOCATION, "drhostexport_test.xml")
        tree = etree.parse(xmlfile)
        self.project = Project()
        self.project.configure_from_node(tree.getroot(), self.defaults, None)

    def test_working(self):
        self.failUnlessEqual( 1, 1 )

    def test_drhost_parse(self):
        """
        Test that the drhost exports for a project are correctly done.
        """
        raise unittest.SkipTest("DRhosts refactoring not yet complete.")

        # The list of drhosts for the first host should be 1 in length.
        testhost01 = self.project.get_host_byname('testhost01')
        self.failUnlessEqual( len(testhost01.get_drhosts()), 1 )

        # Grab the test volume
        testvol = [x for x in self.project.get_volumes() if x.name == 'testvol01' ][0]

        # Check that the target volume qtree is being exported to the dr testhost
        targethost = testvol.snapmirrors[0].targetvol.get_qtrees()[0].get_rw_exports()[0]
        self.failUnlessEqual(targethost.name, 'dr_testhost01')
        
    def test_storage_design_secondary_qtrees(self):
        """
        Test that the qtrees detected at the secondary site are correct.
        """
        raise unittest.SkipTest("Test not yet defined.")

