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

__version__ = '$Revision: 36 $'

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

    $edge_switch_detail_section

    $host_config_section

    $cabling_section

  </chapter>
''')

        ns['core_detail_section'] = self.build_core_detail_section(ns)
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
                  
                </tbody>
              </tgroup>
            </table>
            ''')

        primary_project_vlan = self.conf.get_project_vlan('primary')
        ns['primary_project_vlan'] = primary_project_vlan.number
        
        ns['project_subnet'] = '%s/%s' % (primary_project_vlan.network, primary_project_vlan.maskbits)
        ns['primary_vlan_name'] = '%s_01' % self.conf.shortname

        # FIXME: If the primary storage site is Clayton, this will
        # need to be updated somehow.
        log.warn("Edge balance algorithm is CoLo only at this stage.")
        if int(self.conf.primary_project_vlan) < 3500:
            
            ns['core_switch_balance_side'] = 'left (Core 01)'
            pass
        
        else:
            ns['core_switch_balance_side'] = 'right (Core 02)'
            pass

        ns['core_networking_table'] = core_networking_table.safe_substitute(ns)

        return section.safe_substitute(ns)

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

              <para>IPSAN switch port are clearly labelled on the edge switch devices.
              </para>

            </warning>

            
            ''')

        rows = ''
        for host in self.conf.hosts.values():

            interfaces = [ x for x in host.interfaces if x.type == 'storage' ]

            log.debug("Adding interfaces: %s", interfaces)

            for iface, index in zip(interfaces, range(20) ):

                entries = ''
                log.debug("Processing interface: %s, %s", iface, index)
                if index == 0:
                    if len(interfaces) > 1:
                        entries += "<entry morerows='%d' valign='middle'>%s</entry>\n" % ( len(interfaces)-1, host.name)
                        entries += "<entry morerows='%d' valign='middle'>%s</entry>\n" % ( len(interfaces)-1, host.get_storage_ip() )
                    else:
                        entries += "<entry>%s</entry>\n" %  host.name
                        entries += "<entry>%s</entry>\n" %  host.get_storage_ip()
                
                entries += "<entry>%s</entry>\n" % iface.hostport
                entries += "<entry>%s</entry>\n" % iface.switchname
                entries += "<entry>%s</entry>\n" % iface.switchport
                entries += "<entry>%s</entry>\n" % iface.mode

                rows += "<row>%s</row>\n" % entries
                pass
            pass
                
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
        for switch in [ x for x in self.conf.project_switches.values() if x.type == 'core' ]:
            log.debug("Adding core switch activation commands for %s...", switch.name)
            activation_commands += self.build_switch_activation_commands(switch)
            
        for switch in [ x for x in self.conf.project_switches.values() if x.type == 'edge' ]:
            log.debug("Adding edge switch activation commands for %s...", switch.name)
            activation_commands += self.build_switch_activation_commands(switch)
            pass

        log.debug("activation commands: %s", activation_commands)
        return activation_commands

    def build_switch_activation_commands(self, switch):
        """
        Build the switch activation commands for a specific switch
        in the configuration.
        """
        ns = {}
        section = Template("""<appendix><title>Switch Activation Commmands for %s</title>
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
        # Only create qtrees on primary filers at primary site
        #
        if filer.site == 'primary' and filer.type == 'primary':
            cmds = '\n'.join( self.conf.filer_qtree_create_commands(filer) )
            cmd_ns['commands'] += """<section>
            <title>Qtree Creation</title>
            <screen>%s</screen>
            </section>""" % cmds

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
        if filer.type in ['primary', 'nearstore'] and filer.site == 'primary':
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

        # NFS exports are only configured on primary filers
        if filer.type == 'primary':
            cmdlist = self.conf.vfiler_nfs_exports_commands(filer, vfiler, ns)

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

        cmd_ns['commands'] += """<section>
        <title>Filer <filename>/etc/rc</filename> Additions</title>
        <para>Use these commands to make the new vFiler configuration persistent across reboots:</para>
        <screen>%s</screen>
        </section>""" % '\n'.join( cmds )

        # Add services vlan routes if required
        if filer.type in ['primary', 'nearstore']:
            services_vlans = self.conf.get_services_vlans(filer.site)
            if len(services_vlans) > 0:
                cmds = self.conf.services_vlan_route_commands(filer.site, vfiler)
                cmd_ns['commands'] += """<section>
                <title>Services VLAN routes</title>
                <para>Use these commands to add routes into Services VLANs (aka VRFs):</para>
                <screen>%s</screen>
                </section>""" % '\n'.join( cmds )
                pass
            pass
        
        return section.safe_substitute(cmd_ns)
        
