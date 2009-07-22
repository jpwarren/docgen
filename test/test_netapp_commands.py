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
                             [
                'vol create vftest_root -s volume aggr01 20m',
                'vol options convert_ucode on',
                'vol options nvfail on',
                'vol options create_ucode on',
                'vol create testfiler01_vftest_fs_01 -s volume aggr02 125g',
                'vol options convert_ucode on',
                'vol options nvfail on',
                'vol options create_ucode on',

                ]
                             )

    def test_filer_qtree_create_commands(self):
        """
        Test creation of qtrees
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_qtree_create_commands(self.filer)
        self.failUnlessEqual(commands,
                             [
                'qtree create /vol/testfiler01_vftest_fs_01/testfiler01_vftest_fs_01_qtree',
                'qtree security /vol/testfiler01_vftest_fs_01/testfiler01_vftest_fs_01_qtree unix',
                ]
                             )

    def test_vlan_create_commands(self):
        """
        Test creation of vlans
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vlan_create_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'vlan add svif0 3003'
                ]
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

    def test_ipspace_create_commands(self):
        """
        Test creation of ipspace
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.ipspace_create_commands(self.filer)
        self.failUnlessEqual(commands,
                             [
                'ipspace create ips-test',
                'ipspace assign ips-test svif0-3003',
                ]
                             )

    def test_vfiler_voladd_commands(self):
        """
        Test adding the volumes to the vfiler
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_add_volume_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'vfiler add vftest /vol/testfiler01_vftest_fs_01',
                ]
                             )

    def test_vfiler_add_storage_interface_commands(self):
        """
        Test adding the storage interface
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_add_storage_interface_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'ifconfig svif0-3003 10.240.4.21 netmask 255.255.255.224 mtusize 9000 up',
                ]
                             )

    def test_vfiler_setup_secureadmin_ssh_commands(self):
        """
        Test setting up secureadmin in the vfiler
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_setup_secureadmin_ssh_commands(self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'vfiler run vftest secureadmin setup -q ssh 768 512 768',
                ]
                             )

    def test_vfiler_set_allowed_protocols_commands(self):
        """
        Test setting allowed protocols
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_set_allowed_protocols_commands(self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'vfiler disallow vftest proto=rsh proto=http proto=ftp proto=iscsi proto=nfs proto=cifs',
                'vfiler allow vftest proto=nfs',
                ]
                             )

    def test_vfiler_quotas_add_commands(self):
        """
        Test setting up quotas
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_quotas_add_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'wrfile -a /vol/vftest_root/etc/quotas "##"',
                'wrfile -a /vol/vftest_root/etc/quotas "## Quotas for vftest"',
                'wrfile -a /vol/vftest_root/etc/quotas "##"',
                'wrfile -a /vol/vftest_root/etc/quotas "*    tree@/vol/testfiler01_vftest_fs_01    -    -    -    -    -"'
                ]
                             )

    def test_vfiler_quotas_enable_commands(self):
        """
        Test enabling quotas
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_quotas_enable_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             [
                'vfiler run vftest quota on testfiler01_vftest_fs_01',
                ]
                             )

    def test_filer_snapreserve_commands(self):
        """
        Test setting filer volume snap reserves
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_snapreserve_commands(self.filer)
        self.failUnlessEqual(commands,
                             [
                'snap reserve vftest_root 20',
                'snap reserve testfiler01_vftest_fs_01 20',
                ]
                             )

    def test_filer_snapshot_commands(self):
        """
        Test setting NearStore volume snapshot schedules
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_snapshot_commands(self.filer)
        self.failUnlessEqual(commands,
                             [
                'snap sched vftest_root 0 0 0',
                'snap sched testfiler01_vftest_fs_01 0 0 0',
                ]
                             )

    def test_filer_snapvault_commands(self):
        """
        Test setting primary filer volume snapvaults
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_snapvault_commands(self.filer)
        self.failUnlessEqual(commands,
                             [
                ]
                             )

    def test_filer_snapmirror_commands(self):
        """
        Test initalising snapmirror commands
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_snapmirror_init_commands(self.filer)
        self.failUnlessEqual(commands,
                             [
                ]
                             )

    def test_vfiler_default_route_command(self):
        """
        Test setting vfiler default route
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.default_route_command(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                             ('Default Route',
                              [
                    'vfiler run vftest route add default 10.240.4.254 1',
                ])
                             )

    def test_vfiler_services_vlan_commands(self):
        """
        Test vfiler services vlans commands
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.services_vlan_route_commands(self.vfiler)
        self.failUnlessEqual(commands,
                              [
                ])

    def test_etc_snapmirror_conf_commands(self):
        """
        Test the /etc/snapmirror.conf commands
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_etc_snapmirror_conf_commands(self.filer)
        self.failUnlessEqual(commands,
                              [
                ])

    def test_vfiler_etc_hosts_commands(self):
        """
        Test the /etc/hosts commands
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_etc_hosts_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                              [
                'wrfile -a /vol/vftest_root/etc/hosts "##"',
                'wrfile -a /vol/vftest_root/etc/hosts "## vftest"',
                'wrfile -a /vol/vftest_root/etc/hosts "##"',
                'wrfile -a /vol/vftest_root/etc/hosts "10.240.4.21 testfiler01-svif0-3003"',
                ])

    def test_filer_etc_rc_commands(self):
        """
        Test the /etc/rc commands
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.filer_etc_rc_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                              [
                'wrfile -a /vol/vol0/etc/rc "##"',
                'wrfile -a /vol/vol0/etc/rc "## vftest"',
                'wrfile -a /vol/vol0/etc/rc "##"',
                'wrfile -a /vol/vol0/etc/rc "vlan add svif0 3003"',
                'wrfile -a /vol/vol0/etc/rc "ifconfig svif0-3003 10.240.4.21 netmask 255.255.255.224 mtusize 9000 up"',
                'wrfile -a /vol/vol0/etc/rc "vfiler run vftest route add default 10.240.4.254 1"'
                ])

    def test_vfiler_nfs_exports_commands(self):
        """
        Test the NFS exports commands
        """
        self.load_testfile('simple_single_site.xml')
        self.filer = self.project.get_filers()[0]
        self.vfiler = self.filer.get_vfilers()[0]

        commands = self.docgenerator.vfiler_nfs_exports_commands(self.filer, self.vfiler)
        self.failUnlessEqual(commands,
                              [
'vfiler run vftest exportfs -p root= /vol/testfiler01_vftest_fs_01/testfiler01_vftest_fs_01_qtree',
                ])
