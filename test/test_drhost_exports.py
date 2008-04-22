#
# $Id$
#
"""
Test that exports from primary hosts are also provided to DR hosts.
"""
from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from config import ProjectConfig
from ipsan_storage import IPSANStorageDesignGenerator
from commands import IPSANCommandsGenerator

class DRHostExportTest(unittest.TestCase):

    def setUp(self):
        """
        Load testing XML into a config instance.
        """
        projfile = sibpath(__file__, 'xml/drhostexport_test.xml')
        self.proj = ProjectConfig( projfile )

    def test_working(self):
        self.failUnlessEqual( 1, 1 )

    def test_drhost_parse(self):
        """
        Test that the drhost exports for a project are correctly done.
        """
        docgen = IPSANCommandsGenerator(self.proj)
        #docgen.emit()

        # The list of drhosts for the first volume should be 1 in length.
        self.failUnlessEqual( len(self.proj.hosts['testhost01'].drhosts), 1 )

        # Grab the test volume
        testvol = [x for x in self.proj.filers['primary-filer-01'].volumes if x.name == 'testvol01' ][0]

        # Check that the target volume qtree is being exported to the dr testhost
        targethost = testvol.snapmirrors[0].targetvol.qtrees.values()[0].rwhostlist[0]
        self.failUnlessEqual(targethost.name, 'dr_testhost01')
        
    def test_storage_design_secondary_qtrees(self):
        """
        Test that the qtrees detected at the secondary site are correct.
        """
        docgen = IPSANStorageDesignGenerator(self.proj)

        self.failUnlessEqual( len(docgen.get_nfs_qtree_rows({}, 'secondary')), 1)
