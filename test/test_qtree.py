#
# $Id$
#
"""
Test Qtrees
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
from docgen.filer import Filer, VFiler
from docgen.volume import Volume

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class QtreeTest(unittest.TestCase):
    """
    Test various qtree configurations
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
        self.sitea = Site('sitea', 'primary')
        self.proj.sites[self.sitea.name] = self.sitea
        self.filer1 = Filer('testfiler1', 'filer', self.sitea)
        self.proj.filers[self.filer1.name] = self.filer1

        self.vfiler1 = VFiler(self.filer1, 'vfiler01', 'aggr0', '10.10.10.1', '10.10.10.254')

        self.volume1 = Volume('testvol1', self.filer1, 'aggr01', 100)
        self.proj.volumes.append( self.volume1 )

    def test_empty_qtree(self):
        """
        Test an empty qtree node
        """
        node = etree.Element('qtree')
        self.proj.create_qtree_from_node(self.volume1, node)
        #self.failUnlessRaises(IndexError, self.proj.create_qtree, node)

    def test_autocreate_qtree_plain(self):
        """
        Test a qtree that is autocreated for a plain data volume
        """
        volnode = etree.Element('volume')
        volume = Volume('testvol2', self.filer1, 'aggr01', 100, volnode=volnode)
        self.proj.volumes.append( volume )

        self.proj.create_qtrees_for_volume(volume)

    def test_autocreate_qtree_oradata(self):
        """
        Test a qtree that is autocreated for an oradata volume
        """
        raise unittest.SkipTest("Oracle volume/qtree plugin not written yet.")
        volnode = etree.Element('volume')
        volnode.attrib['oracle'] = 'ORASID'
        volume = Volume('testvol2', self.filer1, 'aggr01', 100, type='oradata', volnode=volnode)
        self.proj.volumes.append( volume )

        self.proj.create_qtrees_for_volume(volume)
        
