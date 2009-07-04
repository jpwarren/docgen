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
from docgen.project import Project
from docgen import qtree

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

        xmldata = """
<project name="test" code="qtree">
  <site name="sitea" type="primary" location="testlab">
    <filer name="testfiler1" type="filer">
      <vfiler name="vfiler01" rootaggr="aggr0">
         <aggregate name="aggr01">
           <volume name="testvol1"/>
         </aggregate>
      </vfiler>
    </filer>
  </site>
</project>
"""

        node = etree.fromstring(xmldata)
        self.proj = Project()        
        self.proj.configure_from_node(node, self.defaults, None)

        self.volume = self.proj.get_volumes()[0]

    def test_empty_qtree(self):
        """
        Test an empty qtree node
        """
        xmldata = """
<qtree />
"""
        node = etree.fromstring(xmldata)
        qtreeobj = qtree.create_qtree_from_node(node, self.defaults, self.volume)
        log.debug("qtree: %s", qtreeobj)

    def test_autocreate_qtree_plain(self):
        """
        Test a qtree that is autocreated for a plain data volume
        """
        raise unittest.SkipTest("Move this test to the volume tests")

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
        
