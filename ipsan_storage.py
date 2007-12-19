##
## $Id$
## IPSAN Storage Design generation components
## 

import sys
import textwrap

from datetime import datetime
from zope.interface import Interface
from string import Template
from lxml import etree

from docgen import DocBookGenerator
from config import ProjectConfig
from modipy import IPSANModiPYGenerator
from commands import IPSANCommandsGenerator, IPSANVolumeSizeCommandsGenerator
from activation_advice import IPSANActivationAdvice

import options
import logging
import debug

log = logging.getLogger('docgen')

__version__ = '$Revision: 36 $'

class IPSANStorageDesignGenerator(DocBookGenerator):
    """
    An IPSANDesignGenerator emits an XML DocBook schema for a design
    document for the IP-SAN.
    """

    introduction = Template('''
  <chapter>
    <title>Introduction</title>
    <para>This document provides an IP-SAN design for the project &project.name;.</para>
    <section>
      <title>Background</title>
      $background_text
    </section>

    <section>
      <title>Audience</title>
      <para>This document is intended to be read by:
        <itemizedlist>
          <listitem>
            <para>The stakeholders of the project.</para>
          </listitem>
          <listitem>
            <para>The host build teams for the project.</para>
          </listitem>
          <listitem>
            <para>The team responsible for the IP-SAN architecture.</para>
          </listitem>
          <listitem>
            <para>The team responsible for the activation of the storage.</para>
          </listitem>

        </itemizedlist>
      </para>

    </section>

    $assumptions
    $scope
    $how_to_use
    $typographical_conventions
 </chapter>
''')

    assumptions = Template('''<section>
    <title>Assumptions</title>
  <para>This storage design assumes the following:</para>
  <para>
    <itemizedlist>
      <listitem>
        <para>Snap Reserve space for each volume is set at a default
        of 20% of the size of the active volume. If the active filesystem
        in the volume changes to a great degree, there is a possibility
        that data within this reserve space may start consuming part of
        the active filesystem. Pro-active support is required to monitor
        reserve utilisation.
        </para>
      </listitem>

      $assumption_list

    </itemizedlist>
  </para>
</section>''')

    scope = Template('''<section>
    <title>Scope</title>
    <para>This document is limited to the NFS, CIFS and iSCSI based storage
    needs for the &project.name; project, and this document provides
    the information in the following areas:
    </para>
    <para>
      <itemizedlist>
        <listitem>
          <para>The storage topology for the project.
          </para>
        </listitem>

        <listitem>
          <para>The storage layout and mapping to individual hosts.
          </para>
        </listitem>

        <listitem>
          <para>The configuration of volumes, qtrees and vFiler resources.
          </para>
        </listitem>

        $scope_list

      </itemizedlist>
    </para>
  </section>
''')

    how_to_use = Template('''
    <section>
      <title>How To Use This Document</title>
      <para>This document assumes the existence of an associated Excelsior Customer Network Storage
Design document for &project.name;. The network storage design document contains the IP-
SAN configuration details for this project.</para>

<para>In addition to the storage design for &project.name;, this document contains the necessary
activation instructions to configure the storage on the Excelsior storage appliances and
present the storage to the project hosts.</para>

    <note>
      <para>For specific instructions on how to activate and configure the storage on the project
hosts, please refer to the specific IP-SAN Host Activation Guides. Project hosts must be
configured to access IP-SAN storage by following the instructions and content provided in
the host activation guides.
      </para>
    </note>
  </section>
  ''')

    typographical_conventions = Template('''
    <section>
      <title>Typographical Conventions</title>
      <para>The following typographical conventions are used within this document:
      </para>

      <itemizedlist>
        <listitem>
          <para>Ordinary text will appear like this.
          </para>
        </listitem>

        <listitem>
          <para>Filenames, computer program names, and similar text will <filename>appear like this</filename>.
          </para>
        </listitem>

        <listitem>
          <screen>Computer output, program listings, file contents, etc. will appear like this.
          </screen>
        </listitem>

        <listitem>
          <note>
            <para>Informational notes will appear like this.</para>
          </note>
        </listitem>

        <listitem>
          <warning>
            <para>Important warnings will appear like this.</para>
          </warning>
        </listitem>


      </itemizedlist>
    </section>
    ''')

    def build_chapters(self, ns={}):
        book_content = ''
        book_content += self.build_introduction(ns)
        book_content += self.build_design_chapter(ns)

        return book_content

    def build_appendices(self, ns={}):
        """
        Return some appendix information
        """
        content = self.build_activation_section(ns)
        #content += self.build_document_control(ns)
        return content

    def build_introduction(self, ns={}):

        assumptions = []
        #assumptions.append('''Storage will only be provisioned for Oracle 10g databases residing on database hosts.''')

        assumption_list = ''.join( [ '<listitem><para>%s</para></listitem>' % x for x in assumptions ] )

        ns['assumption_list'] = assumption_list
        ns['assumptions'] = self.assumptions.safe_substitute(ns)

        background_text = ''.join([etree.tostring(x) for x in self.conf.tree.xpath("background/*")])

        ns['background_text'] = background_text

        ns['scope'] = self.build_scope(ns)
        ns['how_to_use'] = self.how_to_use.safe_substitute(ns)
        ns['typographical_conventions'] = self.typographical_conventions.safe_substitute(ns)
        introduction = self.introduction.safe_substitute(ns)

        return introduction

    def build_scope(self, ns):
        ns['scope_list'] = self.build_scope_list(ns)
        return self.scope.safe_substitute(ns)

    def build_scope_list(self, ns):
        """
        Create additional scope list items based on the project configuration.
        """
        scope_list = []
        scope_list.append('''Configuration of NFS exports and mounts.''')

        retstr = ''.join([ '<listitem><para>%s</para></listitem>' % x for x in scope_list ])

        return retstr

    def build_design_chapter(self, ns):
        """
        The design chapter is where the bulk of the design goes.
        """
        chapter = Template('''
  <chapter>
    <title>Storage Design and Configuration</title>
    $topology_section
    $connectivity_section
    $vfiler_section
    $project_hosts_section
    $volume_section
    $nfs_config_section
    $iscsi_config_section
    $cifs_config_section
    $snapvault_config_section
    $snapmirror_config_section
  </chapter>
''')

        ns['project_hosts_section'] = self.build_project_hosts_section(ns)
        ns['topology_section'] = self.build_topology_section(ns)
        ns['connectivity_section'] = self.build_connectivity_section(ns)
        ns['vfiler_section'] = self.build_vfiler_section(ns)
        ns['volume_section'] = self.build_volume_section(ns)
        ns['nfs_config_section'] = self.build_nfs_config_section(ns)
        ns['iscsi_config_section'] = self.build_iscsi_config_section(ns)
        ns['cifs_config_section'] = self.build_cifs_config_section(ns)
        ns['snapvault_config_section'] = self.build_snapvault_config_section(ns)
        ns['snapmirror_config_section'] = self.build_snapmirror_config_section(ns)
        
        return chapter.safe_substitute(ns)

    def build_project_hosts_section(self, ns):
        """
        Build the project hosts listing section
        """
        section = Template('''
        <section>
          <title>Project Hosts For Storage Connectivity</title>
          <para>The following hosts will require access to the storage:</para>
          <para>
          $hosts_table
          </para>
        </section>
 ''')

        hosttable = Template('''
        <table tabstyle="techtable-01">
          <title>List of project hosts</title>
            <tgroup cols="4">
              <colspec colnum="1" align="center" colwidth="1*"/>
              <colspec colnum="2" align="center" colwidth="1.5*"/>
              <colspec colnum="3" align="center" colwidth="1.5*"/>
              <colspec colnum="4" align="center" colwidth="1.5*"/>

              <thead>
                <row valign="middle">
                  <entry>
                    <para>Hostname</para>
                  </entry>
                  <entry>
                    <para>Operating System</para>
                  </entry>
                  <entry>
                    <para>Location</para>
                  </entry>
                  <entry>
                    <para>Storage IP Address</para>
                  </entry>
                </row>
              </thead>
              <tbody>
                $hosttable_rows
              </tbody>
          </tgroup>
        </table>
''')

        rowlist = []
        hosts = self.conf.tree.xpath('host')
        for host in hosts:
            row = '''
            <row>
              <entry>%s</entry>
              <entry>%s %s</entry>
              <entry>%s</entry>
              <entry>%s</entry>
            </row>
            ''' % ( host.xpath('@name')[0],
                    host.xpath('platform')[0].text,
                    host.xpath('operatingsystem')[0].text,
                    host.xpath('location')[0].text,
                    host.xpath('storageip/ipaddr')[0].text,
                    )
            rowlist.append( row )
            pass

        # Now that we've built the rowlist, join them together as a string
        tablerows = '\n'.join(rowlist)
        table = hosttable.safe_substitute(hosttable_rows=tablerows)

        return section.safe_substitute(hosts_table=table)

    def build_topology_section(self, ns):
        """
        Build the section describing the project's Topology and Storage Model.
        """
        section = Template('''
        <section>
          <title>Topology and Storage Model</title>
          <para>The fundamental design of the storage solution is described by the following statements:</para>
          <para>
            <itemizedlist>
              <listitem>
                <para><emphasis role="bold">Project IP-SAN Storage VLANs</emphasis> - One storage
                VLAN will be provided to deliver the storage to the &project.name; environment.
                </para>
              </listitem>

              $services_vlan_item

              <listitem>
                <para><emphasis role="bold">NetApp vFilers</emphasis> - One NetApp
                 vFiler will be configured for the project.
                </para>
              </listitem>
              
              <listitem>
                <para><emphasis role="bold">Link Resilience</emphasis> - Each host will be
                dual connected to the IP-SAN.
                </para>
              </listitem>

              <listitem>
                <para><emphasis role="bold">Filer Resilience</emphasis> - Filer failover will be
                configured.
                </para>
              </listitem>

              <listitem>
                <para><emphasis role="bold">Switch Resilience</emphasis> - The edge and core
                switches are provided in pairs for resilience.
                </para>
              </listitem>

              <listitem>
                <para><emphasis role="bold">NearStore</emphasis> - A NearStore device will be
                configured to provide secondary copies of primary data.
                </para>
              </listitem>

              $oracle_database_item

            </itemizedlist>
          </para>

          <section>
            <title>Resource Sharing</title>
            <para>The following components of the design may be shared with other projects:
            </para>

            <itemizedlist>
              <listitem>
                <para>The physical NetApp Filer heads and their associated supporting infrastructure
                (FCAL loops, network interfaces, CPU, memory, etc.).
                </para>
              </listitem>

              <listitem>
                <para>The IP-SAN storage network infrastructure.
                </para>
              </listitem>

              <listitem>
                <para>Spare disks will be automatically shared between projects if failures occur.
                </para>
              </listitem>

              <listitem>
                <para>For Data ONTAP 7 implementations, aggregates will be shared with other projects
                according to capacity requirements.
                </para>
              </listitem>

            </itemizedlist>

            <para>The following components of the design are <emphasis role="bold">not</emphasis>
            shared with other projects:
            </para>

            <itemizedlist>
              <listitem>
                <para>The Cat6 edge links between the IP-SAN edge and the hosts.
                </para>
              </listitem>

              <listitem>
                <para>The filer volumes are dedicated to an individual project. This means snapshots will be
                contained within a project.
                </para>
              </listitem>

            </itemizedlist>

          </section>
          
        </section>
 ''')

        if len(self.conf.get_services_vlans()) > 0:
            log.info("Services VLANs are defined.")
            services_vlan = '''
              <listitem>
                <para><emphasis role="bold">Project IP-SAN Services VLANs</emphasis> - Services
                VLANs will be provided to deliver services to the project.
                </para>
              </listitem>
              '''
        else:
            services_vlan = ''

        retstr = section.safe_substitute(services_vlan_item=services_vlan, oracle_database_item='')
        return retstr

    def build_connectivity_section(self, ns):
        """
        This section describes how the connectivity to the IP-SAN works.
        """
        section = Template('''
        <section>
          <title>IP-SAN Connectivity</title>
          <para>The IP-SAN configuration designs for this project are provided in the project's IP-SAN
          design document. It contains the IP addressing for each host and the port connectivity
          requirements.
          </para>
          <para>The host-based configurations are outlined in the appropriate host activation guides. From
          these documents some important information is summarised:
          </para>


          <itemizedlist>
            <listitem>
              <para>The host must be within 75m of an IP-SAN edge switch.
              </para>
            </listitem>

            <listitem>
              <para>The host requires two independent Gigabit connections to the IP-SAN.
              </para>
            </listitem>

            <listitem>
              <para>Two cables are required for each host from the host to the nominated pair of IP-SAN
              edge switches. These cables must be Cat6 UTP.
              </para>
            </listitem>

            <listitem>
              <para>The host connections to the IP-SAN should support Jumbo Frames of 9000 bytes.
              </para>
            </listitem>

          </itemizedlist>

          <section>
            <title>Exceptions</title>
            <para>The following exceptions exist for the storage design and implementation for &project.name;:
            </para>

          <itemizedlist>
            <listitem>
              <para>Stress and volume testing (SVT) has not been provisioned and will not be allowed.
              </para>
            </listitem>

            <listitem>
              <para>All resolutions will be IP address based. No DNS or WINS are to be configured on the
              windows hosts. Filer hostname resolution must be added to each host's resolution
              file. For Solaris, Linux and ESX servers, this is <filename>/etc/hosts</filename>. For
              Windows, this is <filename>C:\windows\system32\drivers\etc\hosts</filename> and
              <filename>C:\windows\system32\drivers\etc\lmhosts</filename>
              </para>
            </listitem>
          </itemizedlist>

<screen>&primary.storage_ip;  &vfiler.name;
</screen>
            
          </section>

          
        </section>
          ''')


        return section.safe_substitute()

    def build_vfiler_section(self, ns):
        """
        The vFiler design section.
        """

        section = Template('''
          <section id="vfiler-design">
          <title>vFiler Design</title>
            <para>The following tables provide the device configuration information.</para>

            $primary_site_vfiler_section
            $dr_site_vfiler_section

            $primary_vfiler_interface_section
            $dr_vfiler_interface_section

            $vfiler_routes_section

          </section>
            ''')
        
        primary_section = Template('''
          <section>
          <title>Primary Site vFiler Configuration</title>
          <para>
            <table tabstyle="techtable-01">
              <title>Primary Site vFiler Configuration Information</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="2*"/>
                <thead>
                  <row>
                    <entry><para>Attribute</para></entry>
                    <entry><para>Value</para></entry>
                    <entry><para>Comment</para></entry>
                  </row>
                </thead>
                <tbody>
                  <row>
                    <entry><para>Physical Filer Primary</para></entry>
                    <entry><para>&primary.filer_name;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>
                  
                  <row>
                    <entry><para>Physical Filer Secondary</para></entry>
                    <entry><para>&secondary.filer_name;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>

                  <row>
                    <entry><para>Primary Storage IP Address</para></entry>
                    <entry><para>&primary.storage_ip;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>
                  
                  <row>
                    <entry><para>Physical &nearstore;</para></entry>
                    <entry><para>&nearstore.filer_name;</para></entry>
                    <entry><para>Used as the backup target for the primary data held on	&primary.filer_name;.</para></entry>
                  </row>

                  <row>
                    <entry><para>&nearstore; IP Address</para></entry>
                    <entry><para>&nearstore.storage_ip;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>


                  <row>
                    <entry><para>vFiler Name</para></entry>
                    <entry><para>&vfiler.name;</para></entry>
                    <entry/>
                  </row>

                  <row>
                    <entry><para>IP Space Name</para></entry>
                    <entry><para>&ipspace.name;</para></entry>
                    <entry/>
                  </row>

                  <row>
                    <entry><para>Project VLAN</para></entry>
                    <entry><para>&primary.project.vlan;</para></entry>
                    <entry/>
                  </row>

                  $primary_services_vlan_rows

                  <row>
                    <entry><para>MTU</para></entry>
                    <entry><para>9000</para></entry>
                    <entry/>
                  </row>

                  <row>
                    <entry><para>Storage Protocols</para></entry>
                    <entry>$storage_protocol_cell</entry>
                    <entry><para>Allowed storage protocols.</para></entry>
                  </row>
                </tbody>
              </tgroup>
            </table>
          </para>
          </section>
            ''')

        dr_section = Template('''
          <section>
          <title>DR Site vFiler Configuration</title>

          <para>
            <table tabstyle="techtable-01">
              <title>Disaster Recovery Site vFiler Configuration Information</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="2*"/>
                <thead>
                  <row>
                    <entry><para>Attribute</para></entry>
                    <entry><para>Value</para></entry>
                    <entry><para>Comment</para></entry>
                  </row>
                </thead>
                <tbody>
                  <row>
                    <entry><para>DR Physical Filer Primary</para></entry>
                    <entry><para>&dr.primary.filer_name;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>
                  
                  <row>
                    <entry><para>DR Physical Filer Secondary</para></entry>
                    <entry><para>&dr.secondary.filer_name;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>

                  <row>
                    <entry><para>DR Filer IP Address</para></entry>
                    <entry><para>&dr.primary.storage_ip;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>
                  
                  <row>
                    <entry><para>DR Physical &nearstore;</para></entry>
                    <entry><para>&dr.nearstore.filer_name;</para></entry>
                    <entry><para>Used as the backup target for the primary data held on	&dr.nearstore.filer_name;.</para></entry>
                  </row>

                  <row>
                    <entry><para>DR &nearstore; IP Address</para></entry>
                    <entry><para>&dr.nearstore.storage_ip;</para></entry>
                    <entry><para>Obtained from network design document.</para></entry>
                  </row>


                  <row>
                    <entry><para>vFiler Name</para></entry>
                    <entry><para>&vfiler.name;</para></entry>
                    <entry/>
                  </row>

                  <row>
                    <entry><para>IP Space Name</para></entry>
                    <entry><para>&ipspace.name;</para></entry>
                    <entry/>
                  </row>

                  <row>
                    <entry><para>Project VLAN</para></entry>
                    <entry><para>&secondary.project.vlan;</para></entry>
                    <entry/>
                  </row>

                  $dr_services_vlan_rows

                  <row>
                    <entry><para>MTU</para></entry>
                    <entry><para>9000</para></entry>
                    <entry/>
                  </row>

                  <row>
                    <entry><para>Storage Protocols</para></entry>
                    <entry>$storage_protocol_cell</entry>
                    <entry><para>Allowed storage protocols.</para></entry>
                  </row>
                </tbody>
              </tgroup>
            </table>
          </para>
          </section>
            ''')

        primary_interface_section = Template('''
        <section>
          <title>Primary vFiler Interfaces</title>
            <table tabstyle="techtable-01">
              <title>Primary vFiler Interface Configuration</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="2*"/>
                <thead>
                  <row>
                    <entry><para>Filer</para></entry>
                    <entry><para>Interface</para></entry>
                    <entry><para>Comment</para></entry>
                  </row>
                </thead>
                <tbody>
                  <row>
                    <entry><para>&primary.filer_name;</para></entry>
                    <entry><para>svif0-&primary.project.vlan;</para></entry>
                    <entry><para>Primary Filer project VLAN interface.</para></entry>
                  </row>

                  <row>
                    <entry><para>&secondary.filer_name;</para></entry>
                    <entry><para>svif0-&primary.project.vlan;</para></entry>
                    <entry><para>Secondary Filer project VLAN interface.</para></entry>
                  </row>

                  <row>
                    <entry><para>&nearstore.filer_name;</para></entry>
                    <entry><para>svif0-&primary.project.vlan;</para></entry>
                    <entry><para>&nearstore; project VLAN interface.</para></entry>
                  </row>

                </tbody>
              </tgroup>
            </table>
          </section>
        ''')

        dr_interface_section = Template("""
        <section>
          <title>DR vFiler Interfaces</title>
            <table tabstyle="techtable-01">
              <title>DR vFiler Interface Configuration</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="2*"/>
                <thead>
                  <row>
                    <entry><para>Filer</para></entry>
                    <entry><para>Interface</para></entry>
                    <entry><para>Comment</para></entry>
                  </row>
                </thead>
                <tbody>
                  <row>
                    <entry><para>&dr.primary.filer_name;</para></entry>
                    <entry><para>svif0-&secondary.project.vlan;</para></entry>
                    <entry><para>DR Primary Filer project VLAN interface.</para></entry>
                  </row>

                  <row>
                    <entry><para>&dr.secondary.filer_name;</para></entry>
                    <entry><para>svif0-&secondary.project.vlan;</para></entry>
                    <entry><para>DR Secondary Filer project VLAN interface.</para></entry>
                  </row>

                  <row>
                    <entry><para>&dr.nearstore.filer_name;</para></entry>
                    <entry><para>svif0-&secondary.project.vlan;</para></entry>
                    <entry><para>DR &nearstore; project VLAN interface.</para></entry>
                  </row>

                </tbody>
              </tgroup>
            </table>
          </section>
          """)

        vfiler_routes = Template("""
        <section>
          <title>vFiler Routes</title>
          <para>The following static routes must be configured in the &vfiler.name; vFiler
          on &primary.filer_name; and &nearstore.filer_name; by placing the following commands
          in the startup file <filename>/etc/rc</filename>:
          </para>

          $services_vlan_routes

        </section>

        <note>
          <para>
            These routes need to be added to all project vFilers at the project's DR site.
          </para>
        </note>
        """)

        ns['storage_protocol_cell'] = self.storage_protocol_cell(ns)
        ns['primary_services_vlan_rows'] = self.get_services_rows(ns, 'primary')
        ns['dr_services_vlan_rows'] = self.get_services_rows(ns, 'secondary')

        ns['project_gateway'] = self.conf.tree.xpath("nas/site[@type = 'primary']/vlan[@type = 'project']/@gateway")[0]

        ns['services_vlan_routes'] = self.build_services_vlan_routes(ns)

        ns['primary_site_vfiler_section'] = primary_section.safe_substitute(ns)
        ns['primary_vfiler_interface_section'] = primary_interface_section.safe_substitute(ns)

        
        if self.conf.has_dr:
            ns['dr_site_vfiler_section'] = dr_section.safe_substitute(ns)
            ns['dr_vfiler_interface_section'] = dr_interface_section.safe_substitute(ns)
        else:
            ns['dr_site_vfiler_section'] = ''
            ns['dr_vfiler_interface_section'] = ''
            pass

        # FIXME: Only include vfiler routes if inter-project routing is required.
##         if len(self.conf.get_services_vlans('primary')) > 0:
##             ns['vfiler_routes_section'] = vfiler_routes.safe_substitute(ns)
##         else:

        ns['vfiler_routes_section'] = ''
        
        return section.safe_substitute(ns)

    def get_services_rows(self, ns, type='primary'):
        # add services vlans
        services_rows = []
        log.debug("finding services vlans...")
        for vlan in self.conf.get_services_vlans(type):
            log.debug("Adding a services VLAN: %s", vlan)
            services_rows.append("""
                  <row>
                    <entry><para>Services VLAN</para></entry>
                    <entry><para>%s</para></entry>
                    <entry><para>%s</para></entry>
                  </row>
                  """ % (vlan.number, vlan.description ) )
            pass
        return ''.join(services_rows)

    def build_services_vlan_routes(self, ns):
        """
        Fetch the services vlan additions that we need.
        """
        retstr = "<screen># For Services VLAN access\n"
        retstr += '\n'.join(self.conf.services_vlan_route_commands(self.conf.vfilers[self.conf.shortname]) )
        retstr += '</screen>'

        return retstr
    
    def storage_protocol_cell(self, ns):
        """
        Build the <para/> entries for the storage protocols cell
        """
        paras = []
        for node in self.conf.tree.xpath("nas/site[@type = 'primary']/filer[@type = 'primary']/vfiler/protocol"):
            paras.append('<para>%s</para>' % node.text)

        return '\n'.join(paras)

    def build_volume_section(self, ns):
        """
        Build the volume design section
        """

        section = Template("""
        <section>
          <title>Filer Volume Design</title>
          <para>The NAS devices represent groups of storage as volumes. Usable
          space on a volume is the amount available after partitioning and
          space reservation for snapshots used to provide backups. From
          the total volume capacity, 20% will be allocated as the snapshot
          reserve.</para>

          $filer_volume_allocations

          $volume_config_subsection

          $qtree_config_subsection

        </section>
        """)

        volumes_table_template = Template("""
          <section>
            <title>$sitetype Site $filer_type Volume Allocation</title>

            <informaltable tabstyle="techtable-01">
              <tgroup cols="7" align="left">
                <colspec colnum="1" colname="c1" align="center" colwidth="0.5*"/>
                <colspec colnum="2" colname="c2" align="center" colwidth="0.5*"/>
                <colspec colnum="3" colname="c3" align="center" colwidth="0.75*"/>
                <colspec colnum="4" colname="c4" align="center" colwidth="0.5*"/>
                <colspec colnum="5" colname="c5" colwidth="0.3*"/>
                <colspec colnum="6" colname="c6" colwidth="0.3*"/>
                <colspec colnum="7" colname="c7" colwidth="0.3*"/>
                <thead>
                  <row valign="middle">
                    <entry><para>Device</para></entry>
                    <entry><para>Aggregate</para></entry>
                    <entry><para>Volume</para></entry>
                    <entry><para>Type</para></entry>
                    <entry><para>Snap Reserve (%)</para></entry>
                    <entry><para>Raw Storage (GiB)</para></entry>
                    <entry><para>Usable Storage (GiB)</para></entry>
                  </row>
                </thead>

                <tfoot>
                  $volume_totals
                </tfoot>

                <tbody>
                  $volume_rows
                </tbody>
              </tgroup>
            </informaltable>
          </section>
          """)

        # FIXME:
        # Create a separate table for each Filer, in case we have
        # projects that span multiple Filers/NearStores.

        vol_alloc_tables = []
        
        for site in ['primary', 'secondary']:
            for role in ['primary', 'nearstore']:
                tblns = {}
                tblns['sitetype'] = site.capitalize()
                if role == 'primary':
                    tblns['filer_type'] = 'Filer'
                elif role == 'nearstore':
                    tblns['filer_type'] = 'NearStore'
                    pass

                vol_list = self.conf.get_volumes(site, role)
                if len(vol_list) > 0:
                    # Take the list of volumes and build a list of body rows
                    tblns['volume_rows'] = self.build_vol_rows(vol_list)

                    # calculate primary volume totals
                    total_usable, total_raw = self.conf.get_volume_totals(vol_list)

                    tblns['volume_totals'] = """
                      <row>
                        <entry namest="c1" nameend="c5" align="right"><para>Total:</para></entry>
                        <entry><para>%s</para></entry>
                        <entry><para>%s</para></entry>
                      </row>""" % (total_raw, total_usable)

                    vol_alloc_tables.append( volumes_table_template.safe_substitute(tblns) )
                    pass
                pass
            pass
        ns['filer_volume_allocations'] = '\n'.join( vol_alloc_tables )
        
        # Then do the configuration subsections
        ns['volume_config_subsection'] = self.build_volume_config_section(ns)
        ns['qtree_config_subsection'] = self.build_qtree_config_section(ns)

        return section.safe_substitute(ns)

    def build_vol_rows(self, vol_list):
        """
        Take a list of Volumes and build a list of <row/>s to be inserted
        into a table body.
        """
        volume_rows = []
        for vol in vol_list:
            entries = ''
            entries += "<entry><para>%s</para></entry>" % vol.filer.name
            for attr in ['aggregate', 'name', 'type', 'snapreserve', 'raw', 'usable']:
                entries += "<entry><para>%s</para></entry>" % getattr(vol, attr)
                pass
            volume_rows.append("<row>%s</row>" % entries)
            pass
        return '\n'.join(volume_rows)

    def build_vol_totals(self, total_usable, total_raw):
        pass


    def build_volume_config_section(self, ns):
        """
        The volume configuration section defines the volume options for each volume.
        """
        section = Template("""
        $filer_volume_configuration
        $nearstore_volume_configuration

        $dr_filer_volume_configuration
        $dr_nearstore_volume_configuration
        
        """)
        
        filer_volume_config = Template("""
          <section>
            <title>Filer Volume Configuration</title>
            <para>The following table details the volume configuration options
            used for the volumes on &primary.filer_name;.</para>

            <table tabstyle="techtable-01">
              <title>Volume Configuration for &primary.filer_name;</title>
              <tgroup cols="4" align="left">
                <colspec colnum="1" colwidth="1.5*"/>
                <colspec colnum="2" colwidth="1.5*"/>
                <colspec colnum="3" colwidth="1.5*"/>
                <colspec colnum="4" colwidth="2*"/>
                
                  <thead>
                    <row valign="middle">
                      <entry><para>Filer</para></entry>
                      <entry><para>Volume</para></entry>
                      <entry><para>Options</para></entry>
                      <entry><para>Comments</para></entry>
                    </row>
                  </thead>

                  <tbody>
                    $primary_volume_config_rows
                  </tbody>
                </tgroup>
              </table>
            </section>
            """)

        nearstore_volume_config = Template("""
          <section>
            <title>Nearstore Volume Configuration</title>
            <para>The following table details the volume configuration options
            used for the volumes on &nearstore.filer_name;.</para>

            <table tabstyle="techtable-01">
              <title>Volume Configuration for &nearstore.filer_name;</title>
              <tgroup cols="4" align="left">
                <colspec colnum="1" colwidth="1.5*"/>
                <colspec colnum="2" colwidth="1.5*"/>
                <colspec colnum="3" colwidth="1.5*"/>
                <colspec colnum="4" colwidth="2*"/>
                
                  <thead>
                    <row valign="middle">
                      <entry><para>Filer</para></entry>
                      <entry><para>Volume</para></entry>
                      <entry><para>Options</para></entry>
                      <entry><para>Comments</para></entry>
                    </row>
                  </thead>

                  <tbody>
                    $nearstore_volume_config_rows
                  </tbody>
                </tgroup>
              </table>
            </section>
            """)

        dr_filer_volume_config = Template("""
          <section>
            <title>DR Filer Volume Configuration</title>
            <para>The following table details the volume configuration options
            used for the volumes on &dr.primary.filer_name;.</para>

            <table tabstyle="techtable-01">
              <title>Volume Configuration for &dr.primary.filer_name;</title>
              <tgroup cols="4" align="left">
                <colspec colnum="1" colwidth="1.5*"/>
                <colspec colnum="2" colwidth="1.5*"/>
                <colspec colnum="3" colwidth="1.5*"/>
                <colspec colnum="4" colwidth="2*"/>
                
                  <thead>
                    <row valign="middle">
                      <entry><para>Filer</para></entry>
                      <entry><para>Volume</para></entry>
                      <entry><para>Options</para></entry>
                      <entry><para>Comments</para></entry>
                    </row>
                  </thead>

                  <tbody>
                    $dr_primary_volume_config_rows
                  </tbody>
                </tgroup>

              </table>
            </section>
            """)

        dr_nearstore_volume_config = Template("""
          <section>
            <title>DR Nearstore Volume Configuration</title>
            <para>The following table details the volume configuration options
            used for the volumes on &dr.nearstore.filer_name;.</para>

            <table tabstyle="techtable-01">
              <title>Volume Configuration for &dr.nearstore.filer_name;</title>

              <tgroup cols="4" align="left">
                <colspec colnum="1" colwidth="1.5*"/>
                <colspec colnum="2" colwidth="1.5*"/>
                <colspec colnum="3" colwidth="1.5*"/>
                <colspec colnum="4" colwidth="2*"/>
                
                  <thead>
                    <row valign="middle">
                      <entry><para>Filer</para></entry>
                      <entry><para>Volume</para></entry>
                      <entry><para>Options</para></entry>
                      <entry><para>Comments</para></entry>
                    </row>
                  </thead>

                  <tbody>
                    $dr_nearstore_volume_config_rows
                  </tbody>
                </tgroup>

              </table>
            </section>
            """)

        # Primary volumes should always exist
        ns['primary_volume_config_rows'] = self.get_volume_options_rows(ns, 'primary', 'primary')
        ns['filer_volume_configuration'] = filer_volume_config.safe_substitute(ns)

        # If DR volumes aren't required, exclude this section
        dr_primary_volume_config_rows = self.get_volume_options_rows(ns, 'secondary', 'primary')
        if len(dr_primary_volume_config_rows) > 0:
            ns['dr_primary_volume_config_rows'] = dr_primary_volume_config_rows
            ns['dr_filer_volume_configuration'] = dr_filer_volume_config.safe_substitute(ns)
        else:
            ns['dr_filer_volume_configuration'] = ''
            pass

        # If nearstore volumes aren't required, exclude this section
        nearstore_volume_config_rows = self.get_volume_options_rows(ns, 'primary', 'nearstore')
        if len(nearstore_volume_config_rows) > 0:
            ns['nearstore_volume_config_rows'] = nearstore_volume_config_rows
            ns['nearstore_volume_configuration'] = nearstore_volume_config.safe_substitute(ns)
        else:
            ns['nearstore_volume_configuration'] = ''
            pass

        # If offsite backup copies of the primary backups aren't required, exclude this section
        dr_nearstore_volume_config_rows = self.get_volume_options_rows(ns, 'secondary', 'nearstore')
        if len(dr_nearstore_volume_config_rows) > 0:
            ns['dr_nearstore_volume_config_rows'] = dr_nearstore_volume_config_rows
            ns['dr_nearstore_volume_configuration'] = dr_nearstore_volume_config.safe_substitute(ns)
        else:
            ns['dr_nearstore_volume_configuration'] = ''
            
        return section.safe_substitute(ns)

    def get_volume_options_rows(self, ns, site, filertype):
        """
        Build the volume options rows for the previously defined volumes
        for a given site/filer, using the sitekey.
        The sitekey is one of 'primary', 'nearstore', 'dr_primary', or 'dr_nearstore'
        """
        rows = []
        for volume in self.conf.get_volumes(site, filertype):
            row_detail = "<entry><para>%s</para></entry>\n" % volume.filer.name
            row_detail += "<entry><para>%s</para></entry>\n" % volume.name
            option_str = ''.join([ "<para>%s</para>" % x for x in volume.voloptions ])
            row_detail += "<entry>%s</entry>\n" % option_str
            row_detail += "<entry/>\n"

            row = "<row valign='middle'>%s</row>" % row_detail

            rows.append(row)

        return '\n'.join(rows)

    def get_volume_options_entry(self, ns, volume_name):
        """
        Build the volume options entry based on the volume's options.
        """
        options = self.conf.get_volume_options(volume_name)

    def build_qtree_config_section(self, ns):
        """
        Qtree layout and definitions.
        """
        section = Template("""
        <section>
          <title>Volume Qtree Structure</title>

        <para>Qtrees on primary site NearStores will be created automatically
	as part of &snapvault; replication; this will produce the
	same qtree structure on NearStores as exists on the source volumes.
        </para>

        <para>Qtrees on secondary site Filers and NearStores will be created automatically
	as part of the SnapMirror replication; this will produce the
	same qtree structure as exists on the source volumes.
        </para>

          $filer_qtrees

        </section>
        """)

        qtrees_table_template = Template("""
        <table tabstyle="techtable-01">
          <title>Qtree Configuration For $filer_name</title>
          <tgroup cols="4" align="left">
            <colspec colname="c1" colwidth="2*"/>
            <colspec colname="c2" colwidth="1*"/>
            <colspec colname="c2" colwidth="0.5*"/>
            <colspec colname="c3" colwidth="1.5*"/>
            <thead>
              <row valign="middle">
                <entry align="center"><para>Qtree Name</para></entry>
                <entry><para>Quota Details</para></entry>
                <entry><para>Qtree Security Style</para></entry>
                <entry><para>Comments</para></entry>
              </row>
            </thead>

            <tbody>
              $qtree_rows
            </tbody>
          </tgroup>
        </table>

      """)


        qtree_tables = []
        for site in ['primary', 'secondary']:
            for filertype in ['primary', ]:
                # Find filers with this site and type
                filers = [ x for x in self.conf.filers.values() if x.site == site and x.type == filertype ]

                for filer in filers:
                    log.debug("finding qtrees for filer: %s", filer.name)
                    tblns = {}
                    tblns['filer_name'] = filer.name
                    filer_qtree_rows = self.get_filer_qtree_rows(filer)
                    tblns['qtree_rows'] = filer_qtree_rows
                    if len(filer_qtree_rows) > 0:
                        log.debug("Adding qtree table for filer %s", filer.name)
                        qtree_tables.append( qtrees_table_template.safe_substitute(tblns) )
                        pass
                    pass
                pass
            pass
        pass


        ns['filer_qtrees'] = '\n'.join(qtree_tables)
        return section.safe_substitute(ns)

    def get_filer_qtree_rows(self, filer):
        """
        Process the filer's qtrees in the format required for the qtree
        configuration table.
        """
        rows = []
        qtree_list = []
        for vol in [ vol for vol in filer.volumes if vol.type not in ['snapvaultdst', 'snapmirrordst'] ]:
            log.debug("finding qtrees on volume: %s: %s", vol, vol.qtrees)
            qtree_list.extend(vol.qtrees.values())

        for qtree in qtree_list:
            row = """
            <row valign='middle'>
            <entry><para>/vol/%s/%s</para></entry>
            <entry><para>Reporting Only</para></entry>
            <entry><para>%s</para></entry>
            <entry><para>%s</para></entry>
            </row>
            """ % ( qtree.volume.name, qtree.name, qtree.security, qtree.comment )
            rows.append(row)
            pass
        return '\n'.join(rows)

    def build_nfs_config_section(self, ns):

        section = Template("""
        <section>
          <title>NFS Storage Configuration</title>
          <para>This section provides the NFS configuration for &project.name;.</para>

          <section>
            <title>Default NFS Mount Options</title>

            <para>All Linux hosts must use the following mount options when mounting NFS storage:</para>
            <screen>rw,bg,hard,tcp,vers=3,rsize=65535,wsize=65535,timeo=600</screen>

            <para>All Solaris hosts must use the following mount options when mounting NFS storage:</para>
            <screen>rw,bg,hard,proto=tcp,vers=3,rsize=65535,wsize=65535</screen>

            <para>Mount options for ESX NFS datastores will be handled and managed by the ESX server storage configuration subsystem.</para>
          </section>

          <section>
            <title>Host NFS Configuration</title>
            <para>The following tables provide the qtree NFS exports and host mount configurations.</para>

            $nfs_exports_tables

            <note>
            <para>Refer to the specific operating system host activation guides for further information on host
            side NFS activation.</para>
            </note>

          </section>

        </section>

            """)
            
        nfs_table_template = Template("""<para>
            <table tabstyle="techtable-01">
              <title>NFS Exports for $sitetype Site</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="2*"/>
                <colspec colnum="2" align="center" colwidth="0.75*"/>
                <colspec colnum="3" align="left" colwidth="1*"/>

                <thead>
                  <row valign="middle">
                    <entry><para>Mount Path</para></entry>
                    <entry><para>Host</para></entry>
                    <entry><para>Additional Mount Options</para></entry>
                  </row>
                </thead>

                <tbody>
                  $nfs_qtree_rows
                </tbody>
              </tgroup>
            </table>
            </para>
        """)

        nfs_tables = []
        for sitetype in ['primary', 'secondary']:
            tblns = {}
            # Only include the NFS qtree section if there are NFS qtrees
            nfs_qtree_rows = self.get_nfs_qtree_rows(ns, sitetype)
            if len(nfs_qtree_rows) > 0:
                #log.debug("Found NFS qtrees: '%s'", nfs_qtree_rows)
                tblns['sitetype'] = sitetype.capitalize()
                tblns['nfs_qtree_rows'] = nfs_qtree_rows
                nfs_tables.append( nfs_table_template.safe_substitute(tblns))
                pass
            pass

        ns['nfs_exports_tables'] = '\n'.join(nfs_tables)
        
        return section.safe_substitute(ns)

    def get_nfs_qtree_rows(self, ns, site):
        """
        Get the qtree level NFS configuration information for a site.
        @returns rows: an XML string of the rows data.
        """
        rows = []

        # only create export definition for nfs volumes
        qtree_list = [ x for x in self.conf.get_site_qtrees(ns, site) if x.volume.proto == 'nfs' and x.volume.type not in [ 'snapvaultdst', 'snapmirrordst' ] ]
        for qtree in qtree_list:
            #log.debug("Adding NFS export definition for %s", qtree)
            # For each qtree, add a row for each host that needs to mount it

            # Read/Write mounts
            for host in qtree.rwhostlist:
                filerip = qtree.volume.volnode.xpath("ancestor::vfiler/primaryip/ipaddr")[0].text
                mountopts = self.conf.get_host_qtree_mountoptions(host, qtree)
                mountoptions = ''.join([ '<para>%s</para>' % x for x in mountopts ])
                entries = """
                    <entry><para>%s:/vol/%s/%s</para></entry>
                    <entry><para>%s</para></entry>
                    <entry>%s</entry>
                    """ % ( filerip, qtree.volume.name, qtree.name, host.name, mountoptions )
                row = "<row valign='middle'>%s</row>" % entries
                rows.append(row)
                pass

            # Read Only mounts
            for host in qtree.rohostlist:
                filerip = qtree.volume.volnode.xpath("ancestor::vfiler/primaryip/ipaddr")[0].text
                mountopts = self.conf.get_host_qtree_mountoptions(host, qtree)
                mountoptions = ''.join([ '<para>%s</para>' % x for x in mountopts ])

                entries = """
                    <entry><para>%s:/vol/%s/%s</para></entry>
                    <entry><para>%s</para></entry>
                    <entry>%s</entry>
                    """ % ( filerip, qtree.volume.name, qtree.name, host.name, mountoptions )
                row = "<row valign='middle'>%s</row>" % entries
                rows.append(row)
                log.debug("Added ro host/qtree: %s/%s", host.name, qtree.name)
                pass

            pass
        return '\n'.join(rows)

    def build_iscsi_config_section(self, ns):
        """
        iSCSI configuration section
        """
        section = Template("""
        <section>
          <title>iSCSI Storage Configuration</title>
          <para>This section provides the iSCSI configuration for &project.name;.</para>

          <section>
            <title>Initiator and CHAP Configuration</title>

            <table tabstyle="techtable-01">
              <title>Project Global iSCSI CHAP Configuration for &project.name;</title>
              <tgroup cols="2">
                <colspec colnum="1" align="center" colwidth="2*"/>
                <colspec colnum="2" align="center" colwidth="2*"/>

                <thead>
                  <row valign="middle">
                    <entry><para>CHAP Username</para></entry>
                    <entry><para>CHAP Password</para></entry>
                  </row>
                </thead>

                <tbody>
                  <row valign="middle">
                    <entry><para>&iscsi.chap.username;</para></entry>
                    <entry><para>&iscsi.chap.password;</para></entry>
                  </row>
                </tbody>
              </tgroup>
            </table>

            <note>
              <para>Ensure that the default iSCSI security mode on all project vFilers is set to CHAP, using the
              following command syntax:</para>
              <screen># vfiler run &vfiler.name; iscsi security default -s CHAP -n &iscsi.chap.username; -p &iscsi.chap.password;</screen>
            </note>

          </section>

          <section>
            <title>iSCSI iGroup Configuration</title>
            <para>iSCSI initiator names must be obtained from each client host, and should be supplied by the project team.</para>
            
            $igroup_tables

          </section>

          <section>
            <title>iSCSI LUN Configuration</title>
            <para>iSCSI initiator names must be obtained from each client host, and should be supplied by the project team.</para>

            $lun_tables

          </section>

          <para>Once the above iSCSI configuration has been applied on the project's vfiler, the hosts can
          then be configured to connect to the vFiler's iSCSI target subsystem and mount the
          configured iSCSI LUNs.
          </para>

          <note>
            <para>Refer to the specific operating system host activation guides for further information on host
            side iSCSI activation.
            </para>
          </note>

      </section>
      """)

        igroup_table_template = Template("""
            <table tabstyle="techtable-01">
              <title>iSCSI iGroup Configuration on $filer_name</title>
              <tgroup cols="4">
                <colspec colnum="1" align="left" colwidth="1.2*"/>
                <colspec colnum="2" align="left" colwidth="2.5*"/>
                <colspec colnum="3" align="left" colwidth="1*"/>
                <colspec colnum="4" align="left" colwidth="1*"/>
                <thead>
                  <row valign="middle">
                    <entry><para>iGroup</para></entry>
                    <entry><para>Initator Name</para></entry>
                    <entry><para>Type</para></entry>
                    <entry><para>OS Type</para></entry>
                  </row>
                </thead>

                <tbody>
                  $iscsi_igroup_rows
                </tbody>
              </tgroup>
            </table>
            """)
        
        lun_table_template = Template("""
            <table tabstyle="techtable-01">
              <title>iSCSI LUN Configuration on $filer_name</title>
              <tgroup cols="5">
                <colspec colnum="1" align="left" colwidth="3*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="1*"/>
                <colspec colnum="4" align="left" colwidth="1.5*"/>
                <colspec colnum="5" align="left" colwidth="1*"/>
                <thead>
                  <row valign="middle">
                    <entry><para>LUN Name</para></entry>
                    <entry><para>Size (GiB)</para></entry>
                    <entry><para>OS Type</para></entry>
                    <entry><para>igroup</para></entry>
                    <entry><para>LUN ID</para></entry>
                  </row>
                </thead>

                <tbody>
                  $iscsi_lun_rows
                </tbody>
              </tgroup>
            </table>
            """)

        if len(self.conf.luns) > 0:
            igroup_tables = []
            lun_tables = []

            for filer in [ x for x in self.conf.filers.values() if x.type in ['primary', ] ]:
                tblns = {}
                tblns['filer_name'] = filer.name
                igroup_rows = self.get_iscsi_igroup_rows(filer)
                if len(igroup_rows) > 0:
                    tblns['iscsi_igroup_rows'] = igroup_rows
                    igroup_tables.append(igroup_table_template.safe_substitute(tblns))
                    pass
                
                lun_rows = self.get_iscsi_lun_rows(filer)
                if len(lun_rows) > 0:
                    tblns['iscsi_lun_rows'] = lun_rows
                    lun_tables.append(lun_table_template.safe_substitute(tblns))
                    pass
                pass

            ns['igroup_tables'] = '\n'.join(igroup_tables)
            ns['lun_tables'] = '\n'.join(lun_tables)

            return section.safe_substitute(ns)
        else:
            return ''

    def get_iscsi_igroup_rows(self, filer):
        """
        Find a list of iSCSI iGroups for the project, and convert
        them into the appropriate rows for the iGroup configuration table.
        """
        rows = []

        igroup_list = self.conf.get_filer_iscsi_igroups(filer)
        for igroup in igroup_list:
            entries = "<entry><para>%s</para></entry>\n" % igroup.name
            entries += "<entry><para>%s</para></entry>\n" % ''.join( [ "<para>%s</para>" % host.iscsi_initiator for host in igroup.initlist ] )
            entries += "<entry><para>iSCSI</para></entry>\n"
            entries += "<entry><para>%s</para></entry>\n" % igroup.type            

            rows.append("<row valign='middle'>%s</row>\n" % entries)
        return '\n'.join(rows)

    def get_iscsi_lun_rows(self, filer):
        rows = []
        lunlist = self.conf.get_filer_luns(filer)
        for lun in lunlist:
            entries = "<entry><para>%s</para></entry>\n" % lun.name
            entries += "<entry><para>%s</para></entry>\n" % lun.size
            entries += "<entry><para>%s</para></entry>\n" % lun.ostype
            entries += "<entry><para>%s</para></entry>\n" % lun.igroup.name
            entries += "<entry><para>%02d</para></entry>\n" % lun.lunid
            
            rows.append("<row valign='middle'>%s</row>\n" % entries)
        return '\n'.join(rows)
        
    def build_cifs_config_section(self, ns):

        section = Template("""
        <section>
          <title>CIFS Storage Configuration</title>
          <para/>

          $cifs_ad_section

          $cifs_shares_section

          $cifs_hosts_config_section
          
        </section>
        """)
        if 'cifs' in self.conf.allowed_protocols:
            log.debug("Configuring CIFS...")
            ns['cifs_ad_section'] = self.build_cifs_active_directory_section(ns)
            
            ns['cifs_shares_section'] = self.build_cifs_shares_section(ns)

            ns['cifs_hosts_config_section'] = self.build_cifs_hosts_config_section(ns)
            
            return section.safe_substitute(ns)
        else:
            return ''

    def build_cifs_active_directory_section(self, ns):
        """
        Set up any CIFS active directory configuration information
        """
        # FIXME: This is purely static for now, if CIFS is enabled.
        log.debug("Setting up AD authentication for CIFS...")
        section = Template("""
        <section>
          <title>CIFS Active Directory Configuration</title>
          <para>The following table provides the CIFS active directory
          configuration for the &project.name; project.</para>

          $cifs_ad_filer_tables

        </section>
        """)

        table_template = Template("""
        <table tabstyle='techtable-03'>
          <title>Active Directory Configuration for $filer_name:$vfiler_name</title>
            <tgroup cols='2'>
              <colspec colnum="1" align="left" colwidth="1*"/>
              <colspec colnum="2" align="left" colwidth="2*"/>

            <tbody>
              <row valign="middle">
                <entry><para>Filer:</para></entry>
                <entry><para>$filer_name</para></entry>
              </row>

              <row valign="middle">
                <entry><para>vFiler:</para></entry>
                <entry><para>$vfiler_name</para></entry>
              </row>

              <row valign="middle">
                <entry><para>Authentication Type:</para></entry>
                <entry><para>Active Directory</para></entry>
              </row>

              <row valign="middle">
                <entry><para>WINS Servers:</para></entry>
                <entry>$wins_servers</entry>
              </row>

              <row valign="middle">
                <entry><para>DNS Servers:</para></entry>
                <entry>$dns_servers</entry>
              </row>

              <row valign="middle">
                <entry><para>DNS Domain Name:</para></entry>
                <entry><para>$dns_domain_name</para></entry>
              </row>

              <row valign="middle">
                <entry><para>vFiler NetBIOS Name:</para></entry>
                <entry><para>$vfiler_netbios_name</para></entry>
              </row>

              <row valign="middle">
                <entry><para>vFiler NetBIOS Aliases:</para></entry>
                <entry>$vfiler_netbios_aliases</entry>
              </row>

              <row valign="middle">
                <entry><para>Fully Qualified AD Domain Name:</para></entry>
                <entry><para>$ad_domain_name</para></entry>
              </row>

              <row valign="middle">
                <entry><para>vFiler Computer Account Location in AD:</para></entry>
                <entry>$vfiler_ad_account_location</entry>
              </row>

            </tbody>
          </tgroup>
        </table>
        """)

        tables = []

        for filer in [ x for x in self.conf.filers.values() if x.type in ['primary', 'nearstore',] ]:
            log.debug("Adding AD config for filer: %s", filer.name)
            for vfiler in filer.vfilers.values():
                tabns = {}
                tabns['filer_name'] = filer.name
                tabns['vfiler_name'] = vfiler.name

                tabns['wins_servers'] = '\n'.join( [ '<para>%s</para>' % x for x in vfiler.winsservers ] )

                tabns['dns_servers'] =  '\n'.join( [ '<para>%s</para>' % x for x in vfiler.nameservers ] )

                tabns['dns_domain_name'] = vfiler.dns_domain_name

                tabns['vfiler_netbios_name'] = vfiler.netbios_name()
                #tabns['vfiler_netbios_aliases'] = "<para>%s</para>" % vfiler.name
                # No NetBIOS aliases will be used by default.
                tabns['vfiler_netbios_aliases'] = "<para>None</para>"
                tabns['ad_domain_name'] = vfiler.fqdn()
                tabns['vfiler_ad_account_location'] = vfiler.ad_account_location
                
                tables.append( table_template.safe_substitute(tabns) )

        ns['cifs_ad_filer_tables'] = '\n'.join(tables)
                
        return section.safe_substitute(ns)

    def build_cifs_shares_section(self, ns):
        """
        Build the CIFS sharing section for the hosts.
        """

        section = Template("""
        <section>
          <title>CIFS Share Configuration</title>
          <para/>

          $cifs_shares_tables
          
        </section>
        """)
        
        cifs_shares_table_template = Template("""
        <table tabstyle='techtable-01'>
          <title>CIFS Share Configuration for $filer_name</title>
          <tgroup cols='3'>
            <colspec colnum="1" align="left" colwidth="1.5*"/>
            <colspec colnum="2" align="left" colwidth="1*"/>
            <colspec colnum="3" align="left" colwidth="1*"/>

            <thead>
              <row valign='middle'>
                <entry><para>Qtree</para></entry>
                <entry><para>Sharename</para></entry>
                <entry><para>Permissions</para></entry>
              </row>
            </thead>

            <tbody>
              $table_rows
            </tbody>
            
          </tgroup>
        </table>
        """)

        tables = []

        for filer in [ x for x in self.conf.filers.values() if x.type == 'primary' ]:
            log.debug("Findings cifs qtrees on filer %s", filer.name)
            cifs_qtrees = self.conf.get_cifs_qtrees(filer)
            if len(cifs_qtrees) > 0:
                log.debug("Found CIFS exports on filer %s", filer)

                tabns = {}
                tabns['filer_name'] = filer.name

                rows = []
                for qtree in cifs_qtrees:
                    row = []

                    perms = []
                    if len(qtree.rwhostlist) > 0:
                        perms.extend( [ "<para>CORP\%s &lt;full&gt;</para>" % x.name for x in qtree.rwhostlist ] )
                        pass
                    
                    if len(qtree.rohostlist) > 0:
                        perms.extend( [ "<para>CORP\%s &lt;read-only&gt;</para>" % x.name for x in qtree.rohostlist ] )
                        pass
                    
                    # only add rows if there are permissions set for them.
                    if len(perms) > 0:

                        row.append("<entry><para>%s</para></entry>" % qtree.full_path() )
                        row.append("<entry><para>%s</para></entry>" % qtree.cifs_share_name() )

                        row.append("<entry>%s</entry>" % ''.join( perms ) )

                        rows.append("<row>%s</row>" % '\n'.join(row) )

                    else:
                        log.warn("Qtree '%s' is defined, but no CIFS hosts have permission to see it.", qtree.full_path())
                    pass

                tabns['table_rows'] = '\n'.join(rows)
                tables.append( cifs_shares_table_template.safe_substitute(tabns) )
                pass
            pass
                
        ns['cifs_shares_tables'] = '\n'.join(tables)
        return section.safe_substitute(ns)

    def build_cifs_hosts_config_section(self, ns):
        """
        Information how to configure CIFS shares on hosts.
        """
        section = Template("""
        <section>
          <title>Host Configurations For CIFS Mounts</title>
          <para>Use the following steps to turn on the 'Client for Microsoft Networks'
          and 'File and Printer Sharing for Microsoft Networks' options for MS Windows
          Hosts.</para>

          <note>
            <para>These steps must be performed on all MS Windows hosts.</para>
          </note>

          <procedure>
            <step>
              <para>Navigate to Control Panel <symbol role="symbolfont">&rarr;</symbol> Network Connections</para>
            </step>

            <step>
              <para>Double click on the teamed storage interface</para>
            </step>

            <step>
              <para>Click the 'Properties' button</para>
            </step>

            <step>
              <para>Tick 'Click for Microsoft Networks' check box.</para>
            </step>

            <step>
              <para>Tick 'File and Printer Sharing for Microsoft Networks' check box.</para>
            </step>

          </procedure>
        </section>
        """)
        return section.safe_substitute(ns)
    
    def build_snapvault_config_section(self, ns):

        section = Template("""
        <section>
          <title>SnapVault Configuration</title>
          <para>The following SnapVault configuration will be configured for &project.name;:
          </para>

            <table tabstyle="techtable-01">
              <title>SnapVault Schedules</title>
              <tgroup cols="5">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="1*"/>
                <colspec colnum="4" align="left" colwidth="1*"/>
                <colspec colnum="5" align="left" colwidth="1*"/>
                <thead>
                  <row valign="middle">
                    <entry><para>Source</para></entry>
                    <entry><para>Destination</para></entry>
                    <entry><para>Snapshot Basename</para></entry>
                    <entry><para>Source Schedule
                      <footnote id="netapp.schedule.format">
                        <para>Format is: number@days_of_the_week@hours_of_day</para>
                      </footnote></para></entry>
                    <entry><para>Destination Schedule<footnoteref linkend="netapp.schedule.format"/></para></entry>
                  </row>
                </thead>

                <tbody>
                  $snapvault_rows
                </tbody>
              </tgroup>
            </table>

        </section>
        """)

        snapvault_rows = self.get_snapvault_rows(ns)
        if len(snapvault_rows) > 0:
            ns['snapvault_rows'] = snapvault_rows
            return section.safe_substitute(ns)
        else:
            return ''

    def get_snapvault_rows(self, ns):
        """
        Build a list of snapvault rows based on the snapvault relationships
        defined in the configuration.
        """
        snapvaults = self.conf.get_snapvaults(ns)
        rows = []
        for sv in snapvaults:
            entries = ''
            entries += "<entry><para>%s</para></entry>\n" % sv.sourcevol.namepath()
            entries += "<entry><para>%s</para></entry>\n" % sv.targetvol.namepath()
            entries += "<entry><para>%s</para></entry>\n" % sv.basename
            entries += "<entry><para>%s</para></entry>\n" % sv.src_schedule
            entries += "<entry><para>%s</para></entry>\n" % sv.dst_schedule
            row = "<row>%s</row>\n" % entries
            rows.append(row)
            pass

        return ''.join(rows)

    
    def build_snapmirror_config_section(self, ns):

        section = Template("""
        <section>
          <title>SnapMirror Configuration</title>
          <para>The following SnapMirror configuration will be configured for &project.name;:
          </para>

            <table tabstyle="techtable-01">
              <title>SnapMirror Schedules</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="1*"/>
                <thead>
                  <row valign="middle">
                    <entry><para>Source</para></entry>
                    <entry><para>Destination</para></entry>
                    <entry><para>Schedule<footnote id="netapp.snapmirror.schedule.format">
                        <para>Format is: minute hour dayofmonth dayofweek</para>
                      </footnote></para></entry>
                  </row>
                </thead>

                <tbody>
                  $snapmirror_rows
                </tbody>
              </tgroup>
            </table>

        </section>
        """)

        snapmirror_rows = self.get_snapmirror_rows(ns)
        if len(snapmirror_rows) > 0:
            ns['snapmirror_rows'] = snapmirror_rows
            return section.safe_substitute(ns)
        else:
            return ''

    def get_snapmirror_rows(self, ns):
        """
        Build a list of snapmirror rows based on the snapmirror relationships
        defined in the configuration.
        """
        snapmirrors = self.conf.get_snapmirrors(ns)
        rows = []
        for sm in snapmirrors:
            entries = ''
            entries += "<entry><para>%s</para></entry>" % sm.sourcevol.namepath()
            entries += "<entry><para>%s</para></entry>" % sm.targetvol.namepath()
            entries += "<entry><para>%s</para></entry>" % sm.etc_snapmirror_conf_schedule()
            row = "<row>%s</row>" % entries
            rows.append(row)
            pass

        return ''.join(rows)

    def build_activation_section(self, ns):
        log.debug("Adding activation instructions...")

        # Old version with subsections
##         section = Template("""
##         <appendix>
##           <title>Activation Instructions</title>

##           $activation_commands
          
##         </appendix>
##         """)

        # new version where each filer is a separate appendix.
        section = Template("""
          $activation_commands
        """)

        ns['activation_commands'] = self.build_activation_commands(ns)
        return section.safe_substitute(ns)
    
    def build_activation_commands(self, ns):

        activation_commands = ''

        # Build the commands for all primary filers
        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'primary' ]:
            vfiler = filer.vfilers[ns['vfiler_name']]
            activation_commands += self.build_filer_activation_commands(filer, vfiler, ns)

        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'secondary' ]:
            # My vfiler is the vfiler from the primary
            vfiler = filer.secondary_for.vfilers[ns['vfiler_name']]
            activation_commands += self.build_filer_activation_commands(filer, vfiler, ns)

        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'nearstore' ]:
            vfiler = filer.vfilers[ns['vfiler_name']]
            activation_commands += self.build_filer_activation_commands(filer, vfiler, ns)

        # Build the commands for all secondary filers
        for filer in [ x for x in self.conf.filers.values() if x.site == 'secondary' and x.type == 'primary' ]:
            vfiler = filer.vfilers[ns['vfiler_name']]
            activation_commands += self.build_filer_activation_commands(filer, vfiler, ns)

        for filer in [ x for x in self.conf.filers.values() if x.site == 'secondary' and x.type == 'secondary' ]:
            # My vfiler is the vfiler from the primary
            vfiler = filer.secondary_for.vfilers[ns['vfiler_name']]
            activation_commands += self.build_filer_activation_commands(filer, vfiler, ns)

        for filer in [ x for x in self.conf.filers.values() if x.site == 'secondary' and x.type == 'nearstore' ]:
            vfiler = filer.vfilers[ns['vfiler_name']]
            activation_commands += self.build_filer_activation_commands(filer, vfiler, ns)

        return activation_commands

    def build_filer_activation_commands(self, filer, vfiler, ns):
        """
        Build the various command sections for a specific filer.
        """
        log.debug("Adding activation commands for %s", filer.name)
        cmd_ns = {}
        cmd_ns['commands'] = ''
        
        section = Template("""<appendix>
          <title>Activation commands for %s</title>
          $commands
        </appendix>
        """ % filer.name)

        # Volumes are not created on secondary filers
        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.filer_vol_create_commands(filer) )
            cmd_ns['commands'] += """<section>
            <title>Volume Creation</title>
            <screen>%s</screen>
            </section>""" % cmds

        #
        # Only create qtrees on primary filers
        #
        if filer.type == 'primary':
            cmds = self.conf.filer_qtree_create_commands(filer)
            if len(cmds) > 0:
                cmd_ns['commands'] += """<section>
                <title>Qtree Creation</title>
                <screen>%s</screen>
                </section>""" % '\n'.join(cmds)

        # Create the vfiler VLAN
        cmds = '\n'.join( self.conf.vlan_create_commands(filer) )
        cmd_ns['commands'] += """<section>
        <title>VLAN Creation</title>
        <screen>%s</screen>
        </section>""" % cmds

        # Create the vfiler IPspace
        cmds = '\n'.join( self.conf.ipspace_create_commands(filer, ns) )
        cmd_ns['commands'] += """<section>
        <title>IP Space Creation</title>
        <screen>%s</screen>
        </section>""" % cmds

        # Only create the vfiler on primary and nearstore filers
        if filer.type in [ 'primary', 'nearstore' ]:
            cmds = '\n'.join( self.conf.vfiler_create_commands(filer, vfiler, ns) )
            cmd_ns['commands'] += """<section>
            <title>vFiler Creation</title>
            <screen>%s</screen>
            </section>""" % cmds

        # Don't add volumes on secondary filers
        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.vfiler_add_volume_commands(filer, ns) )
            cmd_ns['commands'] += """<section>
            <title>vFiler Volume Addition</title>
            <screen>%s</screen>
            </section>""" % cmds

        # Add interfaces
        cmds = '\n'.join( self.conf.vfiler_add_storage_interface_commands(filer, vfiler) )
        cmd_ns['commands'] += """<section>
        <title>Interface Configuration</title>
        <screen>%s</screen>
        </section>""" % cmds

        # Configure secureadmin
        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.vfiler_setup_secureadmin_ssh_commands(vfiler) )
            cmd_ns['commands'] += """<section>
            <title>SecureAdmin Configuration</title>
            <para>Run the following commands to enable secureadmin within the vFiler:</para>
            <screen>%s</screen>
            </section>""" % cmds

        # Inter-project routing
##         cmds = '\n'.join( self.conf.vfiler_add_inter_project_routing(vfiler) )
##         cmd_ns['commands'] += """<section>
##         <title>Inter-Project Routing</title>
##         <screen>%s</screen>
##         </section>""" % cmds

        if filer.type in [ 'primary', 'nearstore' ]:
            cmds = '\n'.join( self.conf.vfiler_set_allowed_protocols_commands(vfiler, ns) )
            cmd_ns['commands'] += """<section>
            <title>Allowed Protocols</title>
            <screen>%s</screen>
            </section>""" % cmds

        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.vfiler_set_options_commands(vfiler, ns) )
            cmd_ns['commands'] += """<section>
            <title>vFiler Options</title>
            <screen>%s</screen>
            </section>""" % cmds

        # Careful! Quotas file is the verbatim file contents, not a list!
        if filer.type in ['primary', 'nearstore']:
            cmds = '\n'.join( self.conf.vfiler_quotas_add_commands(filer, vfiler, ns) )
            cmd_ns['commands'] += """<section>
            <title>Quota File Contents</title>
            <para>Run the following commands to create the quotas file <filename>/vol/%s_root/etc/quotas</filename>:
            </para>
            <screen>%s</screen>
            </section>""" % ( ns['vfiler_name'], cmds )

            # Quota enablement
            cmds = '\n'.join(self.conf.vfiler_quota_enable_commands(filer, vfiler))
            cmd_ns['commands'] += """<section>
            <title>Quota Enablement Commands</title>
            <para>Execute the following commands on the filer to enable quotas:
            </para>
            <screen>%s</screen>
            </section>""" % cmds

        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.filer_snapreserve_commands(filer, ns) )
            cmd_ns['commands'] += """<section>
            <title>Snap Reserve Configuration</title>
            <screen>%s</screen>
            </section>""" % cmds

        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.filer_snapshot_commands(filer, ns) )
            cmd_ns['commands'] += """<section>
            <title>Snapshot Configuration</title>
            <screen>%s</screen>
            </section>""" % cmds

        # initialise the snapvaults to the nearstore
        if filer.type == 'nearstore':
            cmds = '\n'.join( self.conf.filer_snapvault_init_commands(filer, ns) )
            cmd_ns['commands'] += """<section>
            <title>SnapVault Initialisation</title>
            <screen><?db-font-size 60%% ?>%s</screen>
            </section>""" % cmds

        if not filer.type == 'secondary':
            cmds = '\n'.join( self.conf.filer_snapvault_commands(filer, ns) )
            cmd_ns['commands'] += """<section>
            <title>SnapVault Configuration</title>
            <screen>%s</screen>
            </section>""" % cmds

        # initialise the snapmirrors to the DR site
        if self.conf.has_dr:
            if filer.site == 'secondary' and filer.type in ['primary', 'nearstore']:
                log.debug("initialising snapmirror on %s", filer.name)

                cmds = '\n'.join( self.conf.filer_snapmirror_init_commands(filer) )
                cmd_ns['commands'] += """<section>
                <title>SnapMirror Initialisation</title>
                <screen><?db-font-size 60%% ?>%s</screen>
                </section>""" % cmds

        # /etc/snapmirror additions
        if self.conf.has_dr:
            if filer.site == 'secondary' and filer.type in ['primary', 'nearstore']:

                cmds = self.conf.filer_etc_snapmirror_conf_commands(filer)
                cmd_ns['commands'] += """<section>
                <title>Filer <filename>/etc/snapmirror.conf</filename></title>
                <para>Use these commands to append to the Filer's /etc/snapmirror.conf file:</para>
                <screen><?db-font-size 60%% ?>%s</screen>
                </section>""" % '\n'.join(cmds)

        # Add default route
        if filer.type in ['primary', 'nearstore']:
            title, cmds = self.conf.default_route_command(filer, vfiler)
            cmd_ns['commands'] += """<section>
            <title>%s</title>
            <screen>%s</screen>
            </section>""" % (title, '\n'.join( cmds ) )

        # Add services vlan routes if required
        if filer.type in ['primary', 'nearstore']:
            services_vlans = self.conf.get_services_vlans(filer.site)
            if len(services_vlans) > 0:
                cmds = self.conf.services_vlan_route_commands(vfiler)
                cmd_ns['commands'] += """<section>
                <title>Services VLAN routes</title>
                <para>Use these commands to add routes into Services VLANs:</para>
                <screen>%s</screen>
                </section>""" % '\n'.join( cmds )
                pass
            pass

        # /etc/hosts additions
        if not filer.type == 'secondary':
            cmds = self.conf.vfiler_etc_hosts_commands(filer, vfiler)
            cmd_ns['commands'] += """<section>
            <title>vFiler <filename>/etc/hosts</filename></title>
            <para>Use these commands to create the vFiler's /etc/hosts file:</para>
            <screen>%s</screen>
            </section>""" % '\n'.join(cmds)

        #
        # The /etc/rc file needs certain pieces of configuration added to it
        # to make the configuration persistent.
        #
        cmds = self.conf.vlan_create_commands(filer)
        cmds += self.conf.vfiler_add_storage_interface_commands(filer, vfiler)
        title, cmdlist = self.conf.default_route_command(filer, vfiler)
        cmds += cmdlist
        cmds += self.conf.services_vlan_route_commands(vfiler)

        cmd_ns['commands'] += """<section>
        <title>Filer <filename>/etc/rc</filename> Additions</title>
        <para>Use these commands to make the new vFiler configuration persistent across reboots:</para>
        <screen>%s</screen>
        </section>""" % '\n'.join( cmds )

        # NFS exports are only configured on primary filers
        if filer.type == 'primary':
            cmdlist = self.conf.vfiler_nfs_exports_commands(filer, vfiler, ns)

            # Only add the section if NFS commands exist
            if len(cmdlist) == 0:
                log.debug("No NFS exports defined.")
            else:
                wrapped_lines = []
                for line in cmdlist:
                    if len(line) > 90:
                        wraplines = textwrap.wrap(line, 90)
                        wrapped_lines.append('\\\n'.join(wraplines))
                        pass
                    else:
                        wrapped_lines.append(line)

                cmds = '\n'.join( wrapped_lines )
                cmd_ns['commands'] += """<section>
                <title>NFS Exports Configuration</title>
                <screen><?db-font-size 60%% ?>%s</screen>
                </section>""" % cmds

        # CIFS exports are only configured on primary filers
        if 'cifs' in self.conf.allowed_protocols:
            if filer.type in ['primary', 'nearstore']:
                cmds = self.conf.vfiler_cifs_dns_commands(vfiler)
                cmd_ns['commands'] += """<section>
                <title>CIFS DNS Configuration</title>
                <para>Use these commands to configure the vFiler for DNS:</para>
                <screen>%s</screen>
                </section>""" % '\n'.join(cmds)
                pass
            
            # Set up CIFS in the vFiler
            if filer.type in [ 'primary', 'nearstore']:
                cmds = ['vfiler run %s cifs setup' % vfiler.name]
                cmd_ns['commands'] += """<section>
                <title>Set Up CIFS</title>
                <para>Set up CIFS for the vFiler. This is an interactive process.</para>
                <screen>%s</screen>
                </section>""" % '\n'.join(cmds)

            # Set up CIFS shares
            if filer.type in [ 'primary', ]:
                cmds = self.conf.vfiler_cifs_shares_commands(vfiler)
                cmd_ns['commands'] += """<section>
                <title>CIFS Share Configuration</title>
                <para>Set up CIFS for the vFiler. This is an interactive process.</para>
                <screen>%s</screen>
                </section>""" % '\n'.join(cmds)

        # iSCSI exports are only configured on primary filers
        if 'iscsi' in self.conf.allowed_protocols:
            if filer.type in [ 'primary', ]:

                # iSCSI CHAP configuration
                title, cmds = self.conf.vfiler_iscsi_chap_enable_commands(filer, vfiler)
                cmd_ns['commands'] += """<section>
                <title>%s</title>
                <screen>%s</screen>
                </section>""" % (title, '\n'.join(cmds) )

                # iSCSI iGroup configuration
                title, cmds = self.conf.vfiler_igroup_enable_commands(filer, vfiler)
                if len(cmds) > 0:
                    cmd_ns['commands'] += """<section>
                    <title>%s</title>
                    <screen><?db-font-size 60%% ?>%s</screen>
                    </section>""" % (title, '\n'.join(cmds) )

                # iSCSI LUN configuration
                title, cmds = self.conf.vfiler_lun_enable_commands(filer, vfiler)
                if len(cmds) > 0:
                    cmd_ns['commands'] += """<section>
                    <title>%s</title>
                    <screen><?db-font-size 60%% ?>%s</screen>
                    </section>""" % (title, '\n'.join(cmds) )
                
        return section.safe_substitute(cmd_ns)
