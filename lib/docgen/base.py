#$Id$
#

"""
Base definitions
"""
import sys
import os.path
from string import Template
from datetime import datetime
from ConfigParser import NoSectionError, NoOptionError
from zope.interface import implements

from docgen.interfaces import IXMLConfigurable, IDocumentGenerator
from docgen.util import import_module

import logging
import debug
log = logging.getLogger('docgen')

__version__ = '$Revision$'

class XMLConfigurable:
    implements(IXMLConfigurable)

    # A list of child tags that I have. Can be overridden by
    # a configuration file.
    child_tags = []

    # FIXME: Maybe make these overridable by config file also
    mandatory_attribs = []
    optional_attribs = []

    # Limit myself to only be allowed to be contained by
    # certain parent objects, or raise an error
    parent_type_names = []

    def configure_from_node(self, node, defaults, parent):
        """
        Configure an object from its XML node
        """
        self.parent = parent
        
        if len(self.parent_type_names) > 0:
            if parent.__class__.__name__ not in parent_type_names:
                raise ValueError("Parent of '%s' cannot be a '%s'" % ( self.__class__.__name__, parent.__class__.__name__))
        self.configure_mandatory_attributes(node, defaults)
        self.configure_optional_attributes(node, defaults)
        self.configure_children(node, defaults, parent)
        
    def configure_children(self, node, defaults, parent):
        
        self.children = {}
        # See if my child tags are set in the config file. If so,
        # they override my default set of tags.
        #log.debug("Configuring %s", self.__class__.__name__)
        try:
            child_tags = defaults.get('tags', '%s_known_children' % self.xmltag).split()
        except NoOptionError:
            # The option isn't set in the config file, so we use
            # my default set.
            child_tags = self.child_tags

        # For each child tag that I know of, find the module that
        # defines it and load it in. Create the object, and then
        # configure it from the XML
        for tag in child_tags:
            # Set up a list of these child objects
            #log.debug("adding '%s:%s' children...", self.__class__.__name__, tag)
            self.children[tag] = []

            # Add convenience accessors for the children, if there isn't one
            # already defined for the class
            funcname = "get_%ss" % tag
            if not hasattr(self, funcname):
                #log.debug("Adding convenience accessor: %s", funcname)
                # FIXME: This first version doesn't work, but the second
                # version does. Not sure why. It seems the second one
                # isn't actually evaluated at runtime for some reason.
                # I don't actually want you to be able to pass in a value, though.
                #setattr(self, funcname, lambda: self.children[tag])
                setattr(self, funcname, lambda tag=tag: self.children[tag])
            
            # See if we have any of these child nodes defined
            child_nodes = node.findall(tag)
            if len(child_nodes) > 0:
                #log.debug("Adding children: %s", tag)
                module_name = 'docgen.plugins.%s' % tag
                # Try loading it from plugin modules first
                try:
                    module = import_module(module_name)
                except (AttributeError, ImportError), e:
                    #log.debug("Plugin module load failed: %s, trying core modules...", e)
                    # If it didn't work, try the core area
                    module_name = 'docgen.%s' % tag
                    try:
                        module = import_module(module_name)
                    except (AttributeError, ImportError):
                        raise ImportError("Can't find module %s for %s child tag '%s'" % ( module_name, self.__class__.__name__, tag) )
                    pass

                create_func = getattr(module, 'create_%s_from_node' % tag)
                for childnode in child_nodes:
                    child = create_func(childnode, defaults, self)
                    self.children[tag].append(child)
                    pass

                pass
            pass
        pass

    def configure_mandatory_attributes(self, node, defaults):
        """
        If an object has mandatory attributes that must be found,
        configure them, and provide convenience functions for
        accessing them.
        """
        for attrib in self.mandatory_attribs:
            # Add convenience accessors
            funcname = "get_%s" % attrib
            #log.debug("Adding convenience accessor: %s", funcname)
            setattr(self, funcname, lambda: getattr(self, attrib) )

            try:
                setattr(self, attrib, node.attrib[attrib])
            except KeyError, e:
                raise KeyError("'%s' node mandatory attribute '%s' not set" % (self.xmltag, attrib))

    def configure_optional_attributes(self, node, defaults):
        """
        If an object has mandatory attributes that must be found,
        configure them, and provide convenience functions for
        accessing them.
        """
        for attrib in self.optional_attribs:
            # Add convenience accessors
            funcname = "get_%s" % attrib
            #log.debug("Adding convenience accessor: %s", funcname)
            setattr(self, funcname, lambda: getattr(self, attrib) )

            try:
                setattr(self, attrib, node.attrib[attrib])
            except KeyError:
                setattr(self, attrib, None)
                pass

    def add_child(self, obj):
        """
        Add a child object to myself.
        @param obj: a L{XMLConfigurable} object
        """
        if obj.xmltag not in self.child_tags:
            raise ValueError("%s is not a valid child of %s" % (obj, self) )

        self.children[obj.xmltag].append(obj)
    
class DynamicNaming:
    """
    A Mixin class used for doing dynamic naming
    using naming conventions loaded in from a
    defaults configuration file.
    """
    def populate_namespace(self, ns={}):
        """
        Take a namespace passed in (or a blank one)
        and add any extra bits to be found at this
        level to the namespace.
        """
        if self.parent is not None:
            log.debug("my parent is: %s", self.parent)
            ns = self.parent.populate_namespace(ns)
            pass
        return ns

    def name_dynamically(self, defaults):
        """
        Do any dynamic naming that may need to be done.
        """
        if getattr(self, 'name', None) is None:
            # Set up a namespace for use in naming
            ns = self.populate_namespace()
            try:
                name_convention = defaults.get(self.xmltag, '%s_name' % self.xmltag)
            except (NoSectionError, NoOptionError):
                raise KeyError("No naming convention set for %s objects in config file" % self.xmltag)
                
            try:
                self.name = name_convention % ns
            except KeyError, e:
                raise KeyError("Unknown variable %s for %s naming convention" % (e, self.xmltag))

        pass
    
class DynamicNamedXMLConfigurable(XMLConfigurable, DynamicNaming):
    """
    A combined class that is XMLConfigurable, and can do DynamicNaming
    """
    def configure_from_node(self, node, defaults, parent):
        """
        Configure an object from its XML node
        """
        self.parent = parent
        
        if len(self.parent_type_names) > 0:
            if parent.__class__.__name__ not in self.parent_type_names:
                raise ValueError("Parent of '%s' cannot be a '%s'" % ( self.__class__.__name__, parent.__class__.__name__))

        self.configure_mandatory_attributes(node, defaults)
        self.configure_optional_attributes(node, defaults)

        self.name_dynamically(defaults)
        
        self.configure_children(node, defaults, parent)


class FileOutputMixin:
    """
    A mixin to provide some utility functions for outputing to files.
    """

    def version_filename(self, filename, conf):
        """
        Return a filename that has had the version information from a configuration
        appended to it.
        """
        # Get the revision information from the config
        rev = conf.get_latest_revision()
        
        # Take the filename, and insert the revision information before the suffix
        base, ext = os.path.splitext(filename)
        vers_filename = '%s-v%s.%s%s' % (base, rev.majornum, rev.minornum, ext)
        #log.debug("Versioned filename: %s", vers_filename)
        return vers_filename

class DocBookGenerator(FileOutputMixin):
    """
    A Document Generator builds a standard DocBook XML format document.

    It takes as input a minidom Document that is the project configuration,
    loaded from an XML definition file.
    """
    implements(IDocumentGenerator)
    
    bookstr = Template('''<?xml version="1.0" ?>
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.3//EN"
"http://docbook.org/xml/4.3/docbookx.dtd"
[
<!-- include standard entities -->

<!ENTITY % entities SYSTEM "http://docgen.eigenmagic.com/docbook/entities.ent">
%entities;

<!ENTITY docgen.revision "$docgen_revision">

<!-- The name of the project that will appear on the front page -->
<!ENTITY project.title "$project_title">
<!ENTITY project.code "$project_code">

<!-- The vfiler name for the project -->
<!ENTITY vfiler.name "$vfiler_name">

<!-- The IPspace name -->
<!ENTITY ipspace.name "ips-$vfiler_name">

<!-- The VLANs name -->
<!ENTITY primary.project.vlan "$primary_project_vlan">
<!ENTITY secondary.project.vlan "$secondary_project_vlan">

<!-- The storage IP for the project -->
<!ENTITY primary.storage_ip "$primary_storage_ip">

<!-- The storage IP for the nearstore -->
<!ENTITY nearstore.storage_ip "$nearstore_storage_ip">

<!ENTITY dr.primary.storage_ip "$dr_primary_storage_ip">
<!ENTITY dr.nearstore.storage_ip "$dr_nearstore_storage_ip">

<!ENTITY primary.filer_name "$primary_filer_name">
<!ENTITY secondary.filer_name "$secondary_filer_name">
<!ENTITY nearstore.filer_name "$nearstore_filer_name">

<!ENTITY dr.primary.filer_name "$dr_primary_filer_name">
<!ENTITY dr.secondary.filer_name "$dr_secondary_filer_name">
<!ENTITY dr.nearstore.filer_name "$dr_nearstore_filer_name">

]>

<book>
$book_content
</book>
''')

    bookinfo = Template('''
  <bookinfo>
    <title>${title}</title>
    <subtitle>&project.code; &project.title;</subtitle>
    <biblioid>&project.code;</biblioid>
    <author>
      <firstname>$doc_owner_firstname</firstname>
      <surname>$doc_owner_surname</surname>
      <email>$doc_owner_email</email>
    </author>
    <authorinitials>JPW</authorinitials>
    <corpauthor>eigenmagic.com</corpauthor>
${legalnotice}
${copyright}
${releaseinfo}
${revhistory}
${abstract}
  </bookinfo>
''')
    
    legalnotice = Template('''
    <legalnotice>
      <para><emphasis role="bold">CONFIDENTIALITY STATEMENT</emphasis></para>
      <para>This document contains copyright material and/or confidential and proprietary
      information of $copyright_holder. This document must not be used
      or reproduced with the prior consent of $copyright_holder.</para>

      <para>ALL INFORMATION CONTAINED IN THIS DOCUMENT MUST BE KEPT IN CONFIDENCE.</para>

      <para>None of this information may be divulged to any person other than $copyright_holder
      employees, or individuals or organisations authorised by $copyright_holder to
      receive such information.</para>

      <para><trademark class="registered">NetApp</trademark> is a registered trademark of NetApp Inc.</para>
    </legalnotice>
''')
                        
    copyright = Template('''
    <copyright>
      <year>$copyright_year</year>
      <holder>$copyright_holder</holder>
    </copyright>
''')

    doc_control = Template('''
  <preface>
    <title>Document Control</title>
    <para>This is a controlled document.</para>
    <para>Comments or requests for changes to content should be
    addressed to the Owner.</para>

    <informaltable tabstyle="techtable-03">
        <tgroup cols="2" align="left">
          <colspec colname="c1" align="left" colwidth="1*"/>
          <colspec colname="c2" align="left" colwidth="2*"/>

          <thead>
            <row valign="middle">
              <entry namest="c1" nameend="c2" align="center">
                <para>Document Summary</para>
              </entry>
            </row>
          </thead>
          <tbody>
            <row>
              <entry>
                <para>Owner</para>
              </entry>
              <entry>
                <para>$doc_owner_firstname $doc_owner_surname</para>
                <para>$doc_owner_email</para>
              </entry>
           </row>

           <row>
              <entry>
                <para>Department</para>
              </entry>
              <entry>
                <para>$doc_department</para>
              </entry>
            </row>

           <row>
              <entry>
                <para>Project Title</para>
              </entry>
              <entry>
                <para>&project.title;</para>
              </entry>
            </row>

           <row>
              <entry>
                <para>Project Code</para>
              </entry>
              <entry>
                <para>&project.code;</para>
              </entry>
            </row>

           <row>
              <entry>
                <para>DocGen Revision</para>
              </entry>
              <entry>
                <para>&docgen.revision;</para>
              </entry>
            </row>

         </tbody>
      </tgroup>
    </informaltable>

    <!-- Acceptance Table -->
    <!--
    <informaltable tabstyle="techtable-03">
        <tgroup cols="3" align="left">
          <colspec colname="c1" align="left" colwidth="1*"/>
          <colspec colname="c2" align="left" colwidth="2*"/>
          <colspec colname="c3" align="left" colwidth="1*"/>
          <thead>
            <row valign="middle">
              <entry namest="c1" nameend="c3" align="center">
                <para>Acceptance (Business Requirements)</para>
              </entry>
            </row>
            <row valign="middle">
              <entry namest="c1" nameend="c3" align="center">
                <para>Signature denotes official acceptance of document in terms of
                Business Requirements and approval of release as a $copyright_holder
                published document.</para>
              </entry>
            </row>

            <row valign="middle">
              <entry align="center">
                <para>Position</para>
              </entry>

              <entry align="center">
                <para>Name and Signature</para>
              </entry>

              <entry align="center">
                <para>Date</para>
              </entry>

            </row>

          </thead>

          <tbody>
            <row>
              <entry>
                <para>Owner</para>
              </entry>
           </row>
           <row>
              <entry>
                <para>Originator</para>
              </entry>
              <entry>
              </entry>
            </row>

           <row>
              <entry>
                <para>Other</para>
              </entry>
              <entry>
              </entry>
           </row>

           <row>
              <entry>
                <para>Other</para>
              </entry>
              <entry>
              </entry>
           </row>

           <row>
              <entry>
                <para>Other</para>
              </entry>
              <entry>
              </entry>
           </row>


         </tbody>
      </tgroup>
    </informaltable>
    -->

    <!-- Document History -->
    <informaltable tabstyle="techtable-03">
        <tgroup cols="6" align="left">
          <colspec colname="c1" align="center" colwidth="0.5*"/>
          <colspec colname="c2" align="left" colwidth="1.6*"/>
          <colspec colname="c3" align="center" colwidth="0.5*"/>
          <colspec colname="c4" align="center" colwidth="0.6*"/>
          <colspec colname="c5" align="center" colwidth="0.5*"/>
          <colspec colname="c6" align="center" colwidth="0.6*"/>

          <thead>
            <row valign="middle">
              <entry namest="c1" nameend="c6" align="center">
                <para>Document History</para>
              </entry>
            </row>
            <row valign="middle">
              <entry align="center">
                <para>Revision</para>
              </entry>
              <entry align="center">
                <para>Summary of Changes</para>
              </entry>
              <entry align="center">
                <para>Author</para>
              </entry>
              <entry align="center">
                <para>Date</para>
              </entry>

              <entry align="center">
                <para>Reviewer</para>
              </entry>
              <entry align="center">
                <para>Date</para>
              </entry>

            </row>
          </thead>
          <tbody>
            $revision_rows
         </tbody>
       </tgroup>
     </informaltable>
       
  </preface>
''')
    
    def __init__(self, project, defaults):
        self.project = project
        self.defaults = defaults

    def emit(self, outfile=None, ns={}):
        """
        Write out the book XML to a File object, defaulting to STDOUT.
        """
        ns['copyright_holder'] = self.defaults.get('global', 'copyright_holder')
        ns['iscsi_prefix'] = self.defaults.get('global', 'iscsi_prefix')

        book = self.build_book(ns)
        if outfile is None:
            sys.stdout.write(book)
            pass
        else:
            outfile.write(book)

    def build_book(self, ns={}):
        """
        Build up a book from its component elements.
        """
        if not ns.has_key('title'):
            ns['title'] = 'DocGen Automated Document'
            
        ns['docgen_revision'] = __version__
        ns['project_title'] = getattr(self.project, 'title', '')
        ns['project_code'] = getattr(self.project, 'code', '')
        ns['vfiler_name'] = getattr(self.project, 'name', '')

        ns['book_content'] = self.build_book_content(ns)
        return self.bookstr.safe_substitute( ns )

    def build_bookinfo(self, ns={}):
        """
        Build the bookinfo section at the beginning of the book.
        """
        ns['copyright'] = self.build_copyright(ns)
        ns['legalnotice'] = self.build_legalnotice(ns)
        ns['releaseinfo'] = self.build_releaseinfo(ns)
        ns['revhistory'] = self.build_revhistory(ns)
        ns['abstract'] = self.build_abstract(ns)

        ns['doc_owner_firstname'] = self.defaults.get('document_control', 'owner_firstname')
        ns['doc_owner_surname'] = self.defaults.get('document_control', 'owner_surname')
        ns['doc_owner_email'] = self.defaults.get('document_control', 'owner_email')
        ns['doc_department'] = self.defaults.get('document_control', 'department')
        
        bookinfo = self.bookinfo.safe_substitute(ns)
        return bookinfo

    def build_legalnotice(self, ns={}):
        return self.legalnotice.safe_substitute(ns)

    def build_copyright(self, ns={}):
        ns['copyright_year'] = datetime.now().strftime('%Y')
        return self.copyright.safe_substitute(ns)

    def build_revhistory(self, ns={}):
        section = Template("""
        <revhistory>
          $revisions
        </revhistory>
        """)

        revisionlist = []
        revstring = ''
        for rev in self.project.get_revisions():
            revstring = "<revnumber>%s.%s</revnumber>\n" % (rev.majornumber, rev.minornumber)
            revstring += "<date>%s</date>\n" % rev.date
            revstring += "<authorinitials>%s</authorinitials>\n" % rev.author
            revstring += "<revremark>%s</revremark>\n" % rev.revremark
            revisionlist.append("<revision>%s</revision>" % revstring)
            pass
        ns['revisions'] = ''.join(revisionlist)

        return section.safe_substitute(ns)

    def build_releaseinfo(self, ns={}):
        return "<releaseinfo/>"

    def build_abstract(self, ns={}):
        return "<abstract><para>This is a computer generated document.</para></abstract>"

    def build_book_content(self, ns={}):
        book_content = ''
        book_content += self.build_bookinfo(ns)
        book_content += self.build_preface(ns)
        book_content += self.build_chapters(ns)
        book_content += self.build_appendices(ns)

        return book_content

    def build_preface(self, ns={}):
        content = self.build_document_control(ns)
        return content

    def build_appendices(self, ns={}):
        """
        Return some appendix information
        """
        content = ''
        return content

    def build_document_control(self, ns={}):
        """
        Build the document control pages.
        """
        revision_list = []
        for rev in self.project.get_revisions():
            revision_content = ''
            revision_content += '<entry><para>v%s.%s</para></entry>\n' % (rev.majornumber, rev.minornumber)
            revision_content += '<entry><para>%s</para></entry>\n' % rev.revremark
            revision_content += '<entry><para>%s</para></entry>\n' % rev.author
            revision_content += '<entry><para>%s</para></entry>\n' % rev.date
            revision_content += '<entry><para>%s</para></entry>\n' % rev.reviewer
            revision_content += '<entry><para>%s</para></entry>\n' % rev.reviewdate
            revision_row = "<row>%s</row>\n" % revision_content
            revision_list.append(revision_row)

        ns['revision_rows'] = ''.join(revision_list)

        return self.doc_control.safe_substitute(ns)
    
class LunNumbering:
    """
    A Mixin class that is used to implement an upwards cascade of
    LUN numbering grouping, so that LUNs can be numbered sequentially
    within a whole project, or by site, filer, aggregate, or volume.
    """
    def get_next_lunid(self, defaults):
        """
        Get the next available lunid for the volume
        """
        try:
            numberby = defaults.get('lun', 'lun_numbering')
            log.debug("numbering LUNs by: %s", numberby)
            if numberby == self.xmltag:
                value = self.current_lunid
                self.current_lunid += 1
                return value
            else:
                return self.parent.get_next_lunid(defaults)
            
        except (NoSectionError, NoOptionError):
            return self.parent.get_next_lunid(defaults)
                
    def set_current_lunid(self, value, defaults):
        try:
            numberby = defaults.get('lun', 'lun_numbering')
            if numberby == self.xmltag:
                self.current_lunid = value
            else:
                self.parent.set_current_lunid(value, defaults)
                pass
        except (NoSectionError, NoOptionError):
            return self.parent.get_next_lunid(defaults)

