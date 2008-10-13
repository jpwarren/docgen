import sys
import textwrap

from datetime import datetime
from zope.interface import Interface
from string import Template
from lxml import etree

from docgen import DocBookGenerator

import logging
import debug

log = logging.getLogger('docgen')

__version__ = '$Revision$'

class IPSANNetworkDesignGenerator(DocBookGenerator):
    """
    An IPSANNetworkDesignGenerator emits an XML DocBook schema for a
    network design document for the IP-SAN.
    """

    introduction = Template('''
  <chapter>
    <title>Introduction</title>
    <para>This document provides an IPSAN network design for the project &project.name;.</para>
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
            <para>The network build teams for the project.</para>
          </listitem>
          <listitem>
            <para>The team responsible for the IPSAN architecture.</para>
          </listitem>
          <listitem>
            <para>The team responsible for the activation of the storage.</para>
          </listitem>

        </itemizedlist>
      </para>

    </section>

    $scope
    $how_to_use
    $typographical_conventions
 </chapter>
''')

    # FIXME: assumptions are unused.
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
    <para>This document is limited to the IP network information
    required to connect the &project.name; project hosts to
    IPSAN storage.
    </para>

  </section>
''')

    how_to_use = Template('''
    <section>
      <title>How To Use This Document</title>
      <para>This document assumes the existence of an associated IPSAN Storage
Design document for &project.name;. The Storage Design document contains the
Storage configuration details for this project.</para>

<para>This document should be used to configure the IPSAN network infrastructure
to provide IP connectivity between the project hosts and the storage infrastructure.</para>

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
        #ns['scope_list'] = self.build_scope_list(ns)
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
    <title>Network Design and Configuration</title>
    $core_detail_section

    $services_detail_section

    $edge_switch_detail_section

    $host_config_section

    $cabling_section

  </chapter>
''')

        ns['core_detail_section'] = self.build_core_detail_section(ns)
        ns['services_detail_section'] = self.build_services_detail_section(ns)
        ns['edge_switch_detail_section'] = self.build_edge_switch_detail_section(ns)
        ns['host_config_section'] = '' #self.build_core_detail_section(ns)
        ns['cabling_section'] = '' #self.build_core_detail_section(ns)
        return chapter.safe_substitute(ns)

    def build_core_detail_section(self, ns):
        """
        The core networking details section.
        This is just a table with a bunch of info in it.
        """

        section = Template('''
          <section id="core-detail-section">
          <title>Project Core Networking Details</title>
            <para>The following table provides the fundamental project network information.</para>

            $core_networking_table

          </section>
            ''')
        
        core_networking_table = Template('''
            <table tabstyle="techtable-01">
              <title>Project Core Networking Details</title>
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
                    <entry><para>Project VLAN</para></entry>
                    <entry><para>&primary.project.vlan;</para></entry>
                    <entry><para></para></entry>
                  </row>

                  <row>
                    <entry><para>VLAN Name</para></entry>
                    <entry><para>$primary_vlan_name</para></entry>
                    <entry><para></para></entry>
                  </row>

                  <row>
                    <entry><para>Core Switch Balance Side</para></entry>
                    <entry><para>$core_switch_balance_side</para></entry>
                    <entry><para>Chosen based on VLAN id</para></entry>
                  </row>

                  <row>
                    <entry><para>Project Subnet</para></entry>
                    <entry><para>$project_subnet</para></entry>
                    <entry><para></para></entry>
                  </row>

                  <row>
                    <entry><para>Physical Filer Primary</para></entry>
                    <entry><para>&primary.filer_name;</para></entry>
                    <entry><para></para></entry>
                  </row>
                  
                  <row>
                    <entry><para>Physical Filer Secondary</para></entry>
                    <entry><para>&secondary.filer_name;</para></entry>
                    <entry><para></para></entry>
                  </row>

                  <row>
                    <entry><para>Primary Storage IP Address</para></entry>
                    <entry><para>&primary.storage_ip;</para></entry>
                    <entry><para></para></entry>
                  </row>
                  
                  <row>
                    <entry><para>Physical &nearstore;</para></entry>
                    <entry><para>&nearstore.filer_name;</para></entry>
                    <entry><para>Used as the backup target for the primary data held on	&primary.filer_name;.</para></entry>
                  </row>

                  <row>
                    <entry><para>&nearstore; IP Address</para></entry>
                    <entry><para>&nearstore.storage_ip;</para></entry>
                    <entry><para></para></entry>
                  </row>
                  
                </tbody>
              </tgroup>
            </table>
            ''')

        primary_project_vlan = self.conf.get_project_vlan('primary')
        ns['primary_project_vlan'] = primary_project_vlan.number
        
        ns['project_subnet'] = '%s/%s' % (primary_project_vlan.networks[0].number, primary_project_vlan.networks[0].maskbits)
        ns['primary_vlan_name'] = '%s_01' % self.conf.shortname

        if int(self.conf.primary_project_vlan) < 3500:
            
            ns['core_switch_balance_side'] = 'left (Core 01)'
            pass
        
        else:
            ns['core_switch_balance_side'] = 'right (Core 02)'
            pass

        ns['core_networking_table'] = core_networking_table.safe_substitute(ns)

        return section.safe_substitute(ns)

    def build_services_detail_section(self, ns):
        """
        The Services VLAN information.
        This is just a table with a bunch of info in it.
        """

        section = Template('''
          <section id="services-detail-section">
          <title>Services Networking Details</title>
            <para>The following table(s) provide Services VLAN configuration information.</para>

            $networking_tables

          </section>
            ''')
        
        services_networking_table = Template('''
            <table tabstyle="techtable-01">
              <title>Services VLAN $vlan_number Details</title>
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
                    <entry><para>VLAN Number</para></entry>
                    <entry><para>$vlan_number</para></entry>
                    <entry><para></para></entry>
                  </row>

                  <row>
                    <entry><para>VLAN Name</para></entry>
                    <entry><para>$vlan_name</para></entry>
                    <entry><para></para></entry>
                  </row>

                  <row>
                    <entry><para>VLAN Subnet</para></entry>
                    <entry><para>$vlan_subnet</para></entry>
                    <entry><para></para></entry>
                  </row>
                </tbody>
              </tgroup>
            </table>
            ''')

        services_ipaddress_table = Template("""
            <table tabstyle="techtable-01">
              <title>Services VLAN $vlan_number IP Address Details</title>
              <tgroup cols="3">
                <colspec colnum="1" align="left" colwidth="1*"/>
                <colspec colnum="2" align="left" colwidth="1*"/>
                <colspec colnum="3" align="left" colwidth="2*"/>
                <thead>
                  <row>
                    <entry><para>Device</para></entry>
                    <entry><para>IP Address</para></entry>
                    <entry><para>Comment</para></entry>
                  </row>
                </thead>

                <tbody>

                  $ipaddress_rows

                </tbody>
              </tgroup>
            </table>
        """)

        tblns = {}
        tables = []
        for i, vlan in enumerate(self.conf.get_services_vlans()):
            log.debug("Adding a services VLAN to doco: %s...", vlan)
            tblns['vlan_name'] = '%s_%02d' % (self.conf.shortname, i+1)
            tblns['vlan_number'] = vlan.number
            tblns['vlan_subnet'] = '%s/%s' % (vlan.networks[0].number, vlan.networks[0].maskbits)

            tables.append( services_networking_table.safe_substitute(tblns) )

            rows = []
            for device in [ filer for filer in self.conf.filers.values() if filer.type in ['primary', 'nearstore'] ]:
                vfiler = device.vfilers.values()[0]

                # For all the devices that will have IP addresses in the VLAN, fetch the
                # IP of the device from its list of services IPs.

                for vlan, ipaddr in [ (vf_vlan,ipaddr) for (vf_vlan,ipaddr) in vfiler.services_ips if vf_vlan == vlan ]:
                    log.debug("Services IP: %s for filer %s", ipaddr, device.name)
                    rows.append("""
                  <row>
                    <entry><para>%s</para></entry>
                    <entry><para>%s</para></entry>
                    <entry><para></para></entry>
                  </row>""" % (device.name, ipaddr) )
                    pass
                pass
            
            if len(rows) > 0:
                tblns['ipaddress_rows'] = rows
                tables.append( services_ipaddress_table.safe_substitute( tblns ) )
                pass
            pass
        if len(tables) > 0:
            ns['networking_tables'] = '\n'.join(tables)
            return section.safe_substitute(ns)
        else:
            return ''
            
    def build_edge_switch_detail_section(self, ns):
        """
        The edge switch detail section.
        This is just a table with a bunch of info in it.
        """

        section = Template('''
          <section id="edge-detail-section">
          <title>Project Edge Networking Details</title>
            <para>The following table provides the connectivity information for
            connecting the hosts to the IPSAN edge switches.</para>

            <para>All host to edge cabling is required to be CAT-6 UTP.
            </para>

            $edge_networking_table

          </section>
            ''')
        
        edge_networking_table = Template('''
            <table tabstyle="techtable-03">
              <title>Project Edge Networking Details</title>
              <tgroup cols="6">
                <colspec colnum="1" align="center" colwidth="1*"/>
                <colspec colnum="2" align="center" colwidth="1*"/>
                <colspec colnum="3" align="center" colwidth="0.5*"/>
                <colspec colnum="4" align="center" colwidth="1*"/>
                <colspec colnum="5" align="center" colwidth="1*"/>
                <colspec colnum="6" align="center" colwidth="0.5*"/>
                
                <thead>
                  <row>
                    <entry><para>Host</para></entry>
                    <entry><para>Storage IP</para></entry>
                    <entry><para>Host Port</para></entry>

                    <entry><para>Edge Switch Name</para></entry>
                    <entry><para>Switch Port</para></entry>
                    <entry><para>Mode</para></entry>
                    
                  </row>
                </thead>

                <tbody>
                
                  $edge_table_body_rows
                  
                </tbody>
              </tgroup>
            </table>

            <note>
              <para>Hosts with dual connections to edge pairs must have their active connections
              alternated between the edge switch pairs; this spreads the load across the
              switch uplinks to the core switches, which increases throughput.
              </para>
            </note>

            <warning>
              <para>Care should be taken to correctly identify the host end ports. Sun host ports
              are notoriously difficult to identify as the port names are determined by a
              software process. Assistance may be required by build teams to correctly identify
              the required host ports.
              </para>

              <para>IPSAN switch ports are clearly labelled on the edge switch devices.
              </para>

            </warning>

            
            ''')

        rows = ''

        # Sort hosts by name
        hostlist = [ (host.name, host) for host in self.conf.hosts.values() ]
        hostlist.sort()
        for (hostname, host) in hostlist:

            interfaces = [ x for x in host.interfaces if x.type == 'storage' ]

            log.debug("Adding interfaces: %s", interfaces)

            for iface, index in zip(interfaces, range(20) ):

                entries = ''
                log.debug("Processing interface: %s, %s", iface, index)
                if index == 0:
                    if len(interfaces) > 1:
                        entries += "<entry morerows='%d' valign='middle'>%s</entry>\n" % ( len(interfaces)-1, host.name)
                        entries += "<entry morerows='%d' valign='middle'>%s</entry>\n" % ( len(interfaces)-1, ' '.join(host.get_storage_ips()) )
                    else:
                        entries += "<entry>%s</entry>\n" % host.name
                        entries += "<entry>%s</entry>\n" % ' '.join( host.get_storage_ips() )
                
                entries += "<entry>%s</entry>\n" % iface.hostport
                entries += "<entry>%s</entry>\n" % iface.switchname
                entries += "<entry>%s</entry>\n" % iface.switchport
                entries += "<entry>%s</entry>\n" % iface.mode

                rows += "<row>%s</row>\n" % entries
                pass
            pass

        if len(rows) < 1:
            log.error("No hosts have storage interfaces.")
            ns['edge_networking_table'] = ''
        else:
            ns['edge_table_body_rows'] = rows
            ns['edge_networking_table'] = edge_networking_table.safe_substitute(ns)

        return section.safe_substitute(ns)

    def build_activation_section(self, ns):
        log.debug("Adding activation instructions...")

        section = Template("""
          $activation_commands
        """)

        ns['activation_commands'] = self.build_activation_commands(ns)
        return section.safe_substitute(ns)
    
    def build_activation_commands(self, ns):

        activation_commands = ''

        # build core switch configs
        # sort the cores by site
        switchlist = [ (x.site,x) for x in self.conf.project_switches.values() if x.type == 'core' ]
        switchlist.sort()
        for site,switch in switchlist:
            log.debug("Adding core switch activation commands for %s...", switch.name)
            activation_commands += self.build_switch_activation_commands(switch)
            pass
        
        switchlist = [ (x.site,x) for x in self.conf.project_switches.values() if x.type == 'edge' ]
        switchlist.sort()
        for site,switch in switchlist:            
            log.debug("Adding edge switch activation commands for %s...", switch.name)
            activation_commands += self.build_switch_activation_commands(switch)
            pass

        if len(self.conf.get_services_vlans()) > 0:
            log.info("Services VLANs are defined.")

            activation_commands += self.build_firewall_activation_commands()

        return activation_commands

    def build_switch_activation_commands(self, switch):
        """
        Build the switch activation commands for a specific switch
        in the configuration.
        """
        ns = {}
        section = Template("""<appendix><title>Switch Activation Commands for %s</title>
        $sections
        </appendix>
        """ % switch.name)

        ns['sections'] = ''
        if switch.type == 'core':
            ns['sections'] += self.build_core_switch_activation_commands(switch)

        elif switch.type == 'edge':
            ns['sections'] += self.build_edge_switch_activation_commands(switch)
            pass

        return section.safe_substitute(ns)

    def build_core_switch_activation_commands(self, switch):
        """
        Build the core switch activation commands
        """
        ns = {}

        section = Template("""<section><title>VLAN Activation</title>
        <screen>$cmds</screen>
        </section>
        """)
        ns['cmds'] = '\n'.join( self.conf.core_switch_activation_commands(switch) )

        return section.safe_substitute(ns)

    def build_edge_switch_activation_commands(self, switch):
        """
        Build the edge switch activation commands
        """
        sections = ''

        sections += self.build_switch_vlan_activation_section(switch)
        sections += self.build_edgeswitch_port_acls(switch)
        sections += self.build_edgeswitch_interfaces(switch)
        
        return sections

    def build_switch_vlan_activation_section(self, switch):
        ns = {}

        section = Template("""<section><title>VLAN Activation</title>
        <screen>$cmds</screen>
        </section>
        """)
        ns['cmds'] = '\n'.join( self.conf.switch_vlan_activation_commands(switch) )

        return section.safe_substitute(ns)

    def build_edgeswitch_port_acls(self, switch):
        """
        Build ACLs for an edge switch
        """
        ns = {}

        section = Template("""<section><title>Edge Port ACLs</title>
        <screen>$cmds</screen>
        </section>
        """)
        ns['cmds'] = '\n'.join( self.conf.edge_switch_port_acl_commands(switch) )

        return section.safe_substitute(ns)

    def build_edgeswitch_interfaces(self, switch):
        """
        Build interfaces for an edge switch
        """
        ns = {}

        section = Template("""<section><title>Edge Interfaces</title>
        <screen>$cmds</screen>
        </section>
        """)
        ns['cmds'] = '\n'.join( self.conf.edge_switch_interfaces_commands(switch) )

        return section.safe_substitute(ns)

    def build_firewall_activation_commands(self):
        """
        When services VLANs are defined, the firewalls will need to have
        the services VLANs added to them.
        """
        ns = {}
        section = Template("""<appendix><title>Firewall Activation Commands</title>
        $sections
        </appendix>
        """)
        ns['sections'] = ''

        subinterface_section = Template("""<section>
        <title>Configure Firewall Sub-Interface</title>
        $subinterface_commands
        </section>
        """)

        ns['subinterface_commands'] = "<screen>%s</screen>" % '\n'.join( self.build_firewall_subinterface_commands() )

        ns['sections'] += subinterface_section.safe_substitute(ns)
        
        return section.safe_substitute(ns)

    def build_firewall_subinterface_commands(self):
        cmds = []
        for i, vlan in enumerate(self.conf.get_services_vlans()):
            # The subinterface number is the last 2 digits in the VLAN number
            # We convert it to single digit precision number (no leading zero)
            subinterface_num = '%d' % int( ('%s' % vlan.number)[-2])
            cmds.append('set interface ethernet0/3.%s tag %s zone services' % ( subinterface_num, vlan.number))
            cmds.append('set interface ethernet0/3.%s ip %s/%s' % (subinterface_num, vlan.networks[0].gateway, vlan.networks[0].maskbits) )
            cmds.append('set interface ethernet0/3.%s route' % (subinterface_num) )
            cmds.append('set interface ethernet0/3.%s ip manageable' % (subinterface_num))            
            cmds.append('set interface ethernet0/3.%s manage ping' % (subinterface_num))
            cmds.append('set address services %s_SVC_%02d %s %s' % (self.conf.shortname, i, vlan.networks[0].number, vlan.networks[0].netmask) )
            cmds.append('set address Untrust %s_SVC_%02d %s.ipaddr 255.255.255.255' % (self.conf.shortname, i, vlan.networks[0].number) )
            cmds.append('set interface ethernet0/0 ext ip 161.117.180.0 255.255.255.0 dip 5 161.117.180.2 161.117.180.2')
            cmds.append('set policy from services to Untrust %s 161.117.0.0/16 StorageAD nat src dip-id 5 permit log' % (self.conf.shortname, ))
        return cmds
