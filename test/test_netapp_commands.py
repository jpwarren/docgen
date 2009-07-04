#
# $Id$
#
"""
Test emitting the NetApp commands required to activate
a variety of project definitions.
"""
import os.path
from StringIO import StringIO
from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser
from StringIO import StringIO

from docgen.options import BaseOptions
from docgen.project import Project
from docgen.docplugins.netapp_commands import NetAppCommandsGenerator

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class NetAppTestBase(unittest.TestCase):
    """
    Common basecode setup for testing NetApp commands output
    """
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        self.outfile = StringIO()

    def load_testfile(self, filename):
        """
        Load a test file for verifying functionality
        """
        filepath = os.path.join(XML_FILE_LOCATION, filename)
        tree = etree.parse(filepath)

        self.project = Project()
        self.project.configure_from_node(tree.getroot(), self.defaults, None)
        self.docgenerator = NetAppCommandsGenerator(self.project, self.defaults)
        #self.docgenerator.emit(self.outfile)

class NetAppCommandTest(NetAppTestBase):
    """
    Test the ability to emit various NetApp configuration commands
    """
    def test_minimal(self):
        """
        Test parsing of minimal XML file
        """
        self.load_testfile("minimal_parsable_config.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')

    def test_simple(self):
        """
        Test parsing of simple project config
        """
        self.load_testfile("simple_single_site.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')
        
    def test_parse_drhostexports(self):
        """
        Test parsing of dr host exports syntax
        """
        self.load_testfile("drhostexport_test.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')

    def test_parse_clustered_nearstore(self):
        """
        Test parsing of clustered nearstore syntax
        """
        self.load_testfile("clustered_nearstore.xml")
        self.docgenerator.emit(self.outfile)
        data = self.outfile.read()
        self.failUnlessEqual(data, '')
        
class NetAppComponentTest(NetAppTestBase):
    """
    Test individual components of various project configurations
    to make sure the parsing and command generation bits
    function correctly.
    """
    def test_volume_create_commands(self):
        """
        Test creation of the volumes
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_vol_create_commands(self.filer)
        self.failUnlessEqual(commands,
                             ['vol create vftest_root -s volume aggr01 25m',
                              'vol options convert_ucode on',
                              'vol options nvfail on',
                              'vol options create_ucode on']
                             )

    def test_vfiler_create_commands(self):
        """
        Test creation of vfiler is done correctly
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_create_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             ['vfiler create vftest -n -s ips-vftest -i 10.240.4.21 /vol/vftest_root', ]
                             )

