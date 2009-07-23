#
# $Id$
#
"""
Test SetRefs
"""
import os.path

from lxml import etree

from twisted.trial import unittest, runner, reporter
from twisted.internet import reactor
from twisted.python.util import sibpath

from ConfigParser import RawConfigParser

from docgen.options import BaseOptions
from docgen.project import Project
from docgen.setref import SetRef

from docgen import debug
import logging
log = logging.getLogger('docgen')
log.setLevel(logging.DEBUG)

XML_FILE_LOCATION = sibpath(__file__, "xml")
TESTCONF = sibpath(__file__, "docgen_test.conf")

class SetRefTest(unittest.TestCase):
    """
    Test SetRef objects
    """
    
    def setUp(self):
        optparser = BaseOptions()
        optparser.parseOptions(['dummyfile.xml', '--debug=%s' % logging._levelNames[log.level].lower()])

        self.defaults = RawConfigParser()
        configfiles = self.defaults.read(TESTCONF)
        xmldata = """
<project name="testproj" code="01">
  <site name="sitea" type="primary" location="testlab">
    <filer name="filer1" type="filer">
      <vfiler name="vftest01">
        <aggregate type="root" name="aggr0"/>
        <aggregate name="aggr01">
          <volume name="blah">
          </volume>
        </aggregate>
      </vfiler>
    </filer>
  </site>
</project>
"""
        node = etree.fromstring(xmldata)
        self.project = Project()
        self.project.configure_from_node(node, self.defaults, None)

    def test_bare_setref(self):
        """
        Test a bare setref node
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        self.failUnlessRaises( KeyError, sr.configure_from_node, node, self.defaults, vol)

    def test_named_setref(self):
        """
        Test a setref node with just a name
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        self.failUnlessRaises( KeyError, sr.configure_from_node, node, self.defaults, vol)
        
    def test_setref_bad_type(self):
        """
        Test a setref node with an invalid type
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref type="blah" name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        self.failUnlessRaises( ValueError, sr.configure_from_node, node, self.defaults, vol)

    def test_setref_snapshot_type(self):
        """
        Test a setref node of type 'snapshot'
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref type="snapshot" name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        sr.configure_from_node(node, self.defaults, vol)

        self.failUnlessEqual( sr.name, 'alan' )
        self.failUnlessEqual( sr.type, 'snapshot' )

    def test_setref_snapvault_type(self):
        """
        Test a setref node of type 'snapshot'
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref type="snapvault" name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        sr.configure_from_node(node, self.defaults, vol)

        self.failUnlessEqual( sr.name, 'alan' )
        self.failUnlessEqual( sr.type, 'snapvault' )

    def test_setref_snapmirror_type(self):
        """
        Test a setref node of type 'snapmirror'
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref type="snapmirror" name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        sr.configure_from_node(node, self.defaults, vol)

        self.failUnlessEqual( sr.name, 'alan' )
        self.failUnlessEqual( sr.type, 'snapmirror' )

    def test_setref_snapmirrorvault_type(self):
        """
        Test a setref node of type 'snapmirrorvault'
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref type="snapmirrorvault" name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        sr.configure_from_node(node, self.defaults, vol)

        self.failUnlessEqual( sr.name, 'alan' )
        self.failUnlessEqual( sr.type, 'snapmirrorvault' )

    def test_setref_snapmirrorvault_type(self):
        """
        Test a setref node of type 'snapmirrorvault'
        """
        vol = [x for x in self.project.get_volumes() if x.name == 'blah'][0]
        
        xmldata = """
<setref type="snapvaultmirror" name="alan" />
"""
        node = etree.fromstring(xmldata)
        sr = SetRef()
        sr.configure_from_node(node, self.defaults, vol)

        self.failUnlessEqual( sr.name, 'alan' )
        self.failUnlessEqual( sr.type, 'snapvaultmirror' )
