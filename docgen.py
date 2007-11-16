#
# $Id$
#

from zope.interface import Interface
from string import Template

import os.path

import logging
import debug
log = logging.getLogger('docgen')

__version__ = '$Revision$'

class IDocumentGenerator(Interface):
    """
    The IDocumentGenerator is an interface that should be implemented by
    DocumentGenerators.
    """

    def __init__(self, conf):
        """
        A DocumentGenerator requires a parsed configuration as input.
        """

    def emit(self, outfile=None, ns={}):
        """
        emit() sends the output of the generator to an outfile.
        If no output file is specified, it outputs to STDOUT.
        An optional namespace can be provided with values for
        the document generator to use.
        """

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

    bookstr = Template('''<?xml version="1.0" ?>
<!DOCTYPE book PUBLIC "-//OASIS//DTD DocBook XML V4.3//EN"
"http://docbook.org/xml/4.3/docbookx.dtd"
[
<!-- include standard entities -->

<!ENTITY % entities SYSTEM "http://docbook.sensis.com.au/sensis-docgen/entities.ent">
%entities;

<!ENTITY docgen.revision "$docgen_revision">

<!-- The name of the project that will appear on the front page -->
<!ENTITY project.name "$project_name">
<!ENTITY pmo.number "$pmo_number">

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

<!ENTITY iscsi.chap.username "$vfiler_name">
<!ENTITY iscsi.chap.password "sensis${vfiler_name}123">

]>

<book>
$book_content
</book>
''')

    bookinfo = Template('''
  <bookinfo>
    <title>${title}</title>
    <subtitle>&pmo.number; &project.name;</subtitle>
    <biblioid>&pmo.number;</biblioid>
    <author>
      <firstname>Storage</firstname>
      <surname>Design</surname>
      <email>storagemanagement@sensis.com.au</email>
    </author>
    <authorinitials>JPW</authorinitials>
    <corpauthor>Sensis</corpauthor>
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
      information of Sensis Pty Ltd (ABN 30 007 423 912). This document must not be used
      or reproduced with the prior consent of Sensis Pty Ltd.</para>

      <para>ALL INFORMATION CONTAINED IN THIS DOCUMENT MUST BE KEPT IN CONFIDENCE.</para>

      <para>None of this information may be divulged to any person other than Sensis Pty Ltd
      employees, or individuals or organisations authorised by Sensis Pty Ltd to
      receive such information.</para>
    </legalnotice>
''')
                        
    copyright = Template('''
    <copyright>
      <year>2007</year>
      <holder>Sensis Pty Ltd</holder>
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
                <para>Justin Warren</para>
                <para>justin.warren@sensis.com.au</para>
              </entry>
           </row>
           <row>
              <entry>
                <para>Originator</para>
              </entry>
              <entry>
                <para>Storage Design Team</para>
                <para>storagemanagement@sensis.com.au</para>
              </entry>
            </row>

           <row>
              <entry>
                <para>Department</para>
              </entry>
              <entry>
                <para>Enterprise Infrastructure Storage</para>
              </entry>
            </row>

           <row>
              <entry>
                <para>Project</para>
              </entry>
              <entry>
                <para>&project.name;</para>
              </entry>
            </row>

           <row>
              <entry>
                <para>PMO No.</para>
              </entry>
              <entry>
                <para>&pmo.number;</para>
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
                Business Requirements and approval of release as a Sensis Pty Ltd
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
        <tgroup cols="3" align="left">
          <colspec colname="c1" align="center" colwidth="0.5*"/>
          <colspec colname="c2" align="left" colwidth="2*"/>
          <colspec colname="c3" align="center" colwidth="0.5*"/>
          <colspec colname="c4" align="center" colwidth="0.75*"/>
          <thead>
            <row valign="middle">
              <entry namest="c1" nameend="c4" align="center">
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
            </row>
          </thead>
          <tbody>
            $revision_rows
         </tbody>
       </tgroup>
     </informaltable>
       
  </preface>
''')
    
    def __init__(self, conf):
        self.conf = conf

    def emit(self, outfile=None, versioned=True, ns={}):
        """
        Write out the book XML to a File, defaulting to STDOUT.
        """
        book = self.build_book(ns)
        if outfile is None:
            sys.stdout.write(book)
            pass
        else:
            if versioned:
                outfile = self.version_filename(outfile, self.conf)
                pass
            outf = open(outfile, "w")
            outf.write(book)
            outf.close()
            pass

    def build_book(self, ns={}):
        """
        Build up a book from its component elements.
        """
        if not ns.has_key('title'):
            ns['title'] = 'DocGen Automated Document'
            
        ns['docgen_revision'] = __version__
        ns['project_name'] = self.conf.longname
        ns['pmo_number'] = self.conf.code
        ns['vfiler_name'] = self.conf.shortname
        ns['primary_project_vlan'] = self.conf.primary_project_vlan

        ns['primary_filer_name'] = self.conf.get_filers('primary', 'primary')[0].name
        ns['secondary_filer_name'] = self.conf.get_filers('primary', 'secondary')[0].name
        ns['nearstore_filer_name'] = self.conf.get_filers('primary', 'nearstore')[0].name
        ns['primary_storage_ip'] = self.conf.get_filers('primary', 'primary')[0].vfilers.values()[0].ipaddress
        ns['nearstore_storage_ip'] = self.conf.get_filers('primary', 'nearstore')[0].vfilers.values()[0].ipaddress

        if self.conf.has_dr:
            try:
                ns['secondary_project_vlan'] = self.conf.secondary_project_vlan

                ns['dr_primary_filer_name'] = self.conf.get_filers('secondary', 'primary')[0].name
                ns['dr_secondary_filer_name'] = self.conf.get_filers('secondary', 'secondary')[0].name
                ns['dr_nearstore_filer_name'] = self.conf.get_filers('secondary', 'nearstore')[0].name

                ns['dr_primary_storage_ip'] = self.conf.get_filers('secondary', 'primary')[0].vfilers.values()[0].ipaddress
                ns['dr_nearstore_storage_ip'] = self.conf.get_filers('secondary', 'nearstore')[0].vfilers.values()[0].ipaddress

            except IndexError, e:
                log.error("DR filer details not supplied.")
                raise

        
        ns['book_content'] = self.build_book_content(ns)
        return self.bookstr.safe_substitute( ns )

    def build_bookinfo(self, ns={}):
        """
        Build the bookinfo section at the beginning of the book.
        """
        ns['legalnotice'] = self.build_legalnotice(ns)
        ns['copyright'] = self.build_copyright(ns)
        ns['releaseinfo'] = self.build_releaseinfo(ns)
        ns['revhistory'] = self.build_revhistory(ns)
        ns['abstract'] = self.build_abstract(ns)

        bookinfo = self.bookinfo.safe_substitute(ns)
        return bookinfo

    def build_legalnotice(self, ns={}):
        return self.legalnotice.safe_substitute(ns)

    def build_copyright(self, ns={}):
        return self.copyright.safe_substitute(ns)

    def build_revhistory(self, ns={}):
        section = Template("""
        <revhistory>
          $revisions
        </revhistory>
        """)

        revisionlist = []
        revstring = ''
        for rev in self.conf.revlist:
            revstring = "<revnumber>%s.%s</revnumber>\n" % (rev.majornum, rev.minornum)
            revstring += "<date>%s</date>\n" % rev.date
            revstring += "<authorinitials>%s</authorinitials>\n" % rev.authorinitials
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
        for rev in self.conf.revlist:
            revision_content = ''
            revision_content += '<entry><para>v%s.%s</para></entry>\n' % (rev.majornum, rev.minornum)
            revision_content += '<entry><para>%s</para></entry>\n' % rev.revremark
            revision_content += '<entry><para>%s</para></entry>\n' % rev.authorinitials
            revision_content += '<entry><para>%s</para></entry>\n' % rev.date
            revision_row = "<row>%s</row>\n" % revision_content
            revision_list.append(revision_row)

        ns['revision_rows'] = ''.join(revision_list)

        return self.doc_control.safe_substitute(ns)
    
