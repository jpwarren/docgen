#
# $Id$
# Dump activation commands out as as plain text
#

import zope.interface
import sys

import logging
from docgen import debug
log = logging.getLogger('docgen')

from docgen.docgen import IDocumentGenerator, FileOutputMixin

class CommandGenerator(FileOutputMixin):
    """
    An abstract base class that implements some commonly used functions.
    """
    zope.interface.implements(IDocumentGenerator)

    def __init__(self, conf):
        self.conf = conf

class IPSANCommandsGenerator(CommandGenerator):
    """
    A generator for creating the commandlines required to activate a project.
    """

    def emit(self, outfile=None, versioned=True, ns={}):

        ns['iscsi_prefix'] = self.conf.defaults.get('global', 'iscsi_prefix')

        cmdlist = []
        cmdlist.extend( self.build_activation_commands(ns) )
        book = '\n'.join(cmdlist)
        book += '\n'

        if outfile is None:
            outfile = sys.stdout
            sys.stdout.write(book)
        else:
            if versioned:
                outfile = self.version_filename(outfile, self.conf)
                pass
            outf = open(outfile, "w")
            outf.write(book)
            outf.close()
            
    def build_activation_commands(self, ns):
        """
        Build the activation commands for all the filers.
        """

        activation_commands = []

        # Build the commands for all primary filers
        for filer in [ x for x in self.conf.filers.values() if x.site.type == 'primary' and x.type == 'primary' ]:
            vfiler = filer.vfilers.values()[0]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site.type == 'primary' and x.type == 'secondary' ]:
            # My vfiler is the vfiler from the primary
            vfiler = filer.secondary_for.vfilers.values()[0]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site.type == 'primary' and x.type == 'nearstore' ]:
            vfiler = filer.vfilers.values()[0]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        # Build the commands for all secondary filers
        for filer in [ x for x in self.conf.filers.values() if x.site.type == 'secondary' and x.type == 'primary' ]:
            vfiler = filer.vfilers.values()[0]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site.type == 'secondary' and x.type == 'secondary' ]:
            # My vfiler is the vfiler from the primary
            vfiler = filer.secondary_for.vfilers.values()[0]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site.type == 'secondary' and x.type == 'nearstore' ]:
            vfiler = filer.vfilers.values()[0]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        return activation_commands

    def build_filer_activation_commands(self, filer, vfiler, ns):
        """
        Build the various command sections for a specific filer.
        """
        log.debug("Adding activation commands for %s", filer.name)
        commands = []

        commands.append( "\n#\n# Activation commands for %s\n#" % filer.name)

        # Volumes are not created on secondary filers
        if not filer.type == 'secondary':
            commands.append( "\n# Volume Creation\n" )
            commands.extend( self.conf.filer_vol_create_commands(filer) )

        #
        # Create qtrees
        #
        cmds = self.conf.filer_qtree_create_commands(filer)
        if len(cmds) > 0:
            commands.append( "\n# Qtree Creation\n" )
            commands.extend( cmds )

        # Create the vfiler VLAN
        commands.append("\n# VLAN Creation\n")
        commands.extend( self.conf.vlan_create_commands(filer, vfiler) )

        # Create the vfiler IPspace
        commands.append("\n# IP Space Creation\n")
        commands.extend( self.conf.ipspace_create_commands(filer, ns) )

        # Only create the vfiler on primary and nearstore filers
        if filer.type in [ 'primary', 'nearstore' ]:
            commands.append("\n# vFiler Creation\n")
            commands.extend( self.conf.vfiler_create_commands(filer, vfiler, ns) )

        # Don't add volumes on secondary filers
        if not filer.type == 'secondary':
            commands.append("\n# vFiler Volume Addition\n")
            commands.extend( self.conf.vfiler_add_volume_commands(filer, ns) )

        # Add interfaces
        commands.append("\n# Interface Configuration\n")
        commands.extend( self.conf.vfiler_add_storage_interface_commands(filer, vfiler) )

        # Configure secureadmin
        if not filer.type == 'secondary':
            commands.append("\n# SecureAdmin Configuration\n")
            commands.extend( self.conf.vfiler_setup_secureadmin_ssh_commands(vfiler) )

        # Inter-project routing
##         cmds = '\n'.join( self.conf.vfiler_add_inter_project_routing(vfiler) )
##         cmd_ns['commands'] += """<section>
##         <title>Inter-Project Routing</title>
##         <screen>%s</screen>
##         </section>""" % cmds

        if filer.type in [ 'primary', 'nearstore' ]:
            commands.append("\n# Allowed Protocols\n")
            commands.extend( self.conf.vfiler_set_allowed_protocols_commands(vfiler, ns) )

        # Careful! Quotas file is the verbatim file contents, not a list!
        if filer.type in ['primary', 'nearstore']:
            commands.append("\n# Quota File Contents\n")
            commands.extend( self.conf.vfiler_quotas_add_commands(filer, vfiler, ns) )

            commands.append("\n# Quota Enablement Commands\n")
            commands.extend(self.conf.vfiler_quota_enable_commands(filer, vfiler))


        if not filer.type == 'secondary':
            commands.append("\n# Snap Reserve Configuration\n")
            commands.extend( self.conf.filer_snapreserve_commands(filer, ns) )

        if not filer.type == 'secondary':
            commands.append("\n# Snapshot Configuration\n")
            commands.extend( self.conf.filer_snapshot_commands(filer, ns) )

        # initialise the snapvaults to the nearstore
        if filer.type == 'nearstore':
            commands.append("\n# SnapVault Initialisation\n")
            commands.extend( self.conf.filer_snapvault_init_commands(filer, ns) )

        if not filer.type == 'secondary':
            commands.append("\n# SnapVault Configuration\n")
            commands.extend( self.conf.filer_snapvault_commands(filer, ns) )

        # initialise the snapmirrors to the DR site
        if self.conf.has_dr:
            if filer.site.type == 'secondary' and filer.type in ['primary', 'nearstore']:
                log.debug("Adding snapmirror config for '%s'", filer.name)
                commands.append("\n# SnapMirror Initialisation")
                commands.extend( self.conf.filer_snapmirror_init_commands(filer) )

        # Add default route
        if filer.type in ['primary', 'nearstore']:
            title, cmds = self.conf.default_route_command(filer, vfiler)
            commands.append("\n# %s\n" % title)
            commands.extend(cmds)

        # Add services vlan routes if required
        if filer.type in ['primary', 'nearstore']:
            services_vlans = self.conf.get_services_vlans(filer.site.type)
            if len(services_vlans) > 0:
                cmds = self.conf.services_vlan_route_commands(vfiler)
                commands.append("\n# VLAN routes\n")
                commands.extend(cmds)

                pass
            pass

        # /etc/snapmirror.conf additions
        if self.conf.has_dr:
            if filer.site.type == 'secondary' and filer.type in ['primary', 'nearstore']:
                commands.append("\n# Filer /etc/snapmirror.conf\n")
                commands.extend( self.conf.filer_etc_snapmirror_conf_commands(filer) )

        # /etc/hosts additions
        if not filer.type == 'secondary':
            commands.append("\n# vFiler /etc/hosts\n")
            commands.extend( self.conf.vfiler_etc_hosts_commands(filer, vfiler) )

        #
        # The /etc/rc file needs certain pieces of configuration added to it
        # to make the configuration persistent.
        #
        cmds = self.conf.filer_etc_rc_commands(filer, vfiler)

        commands.append("\n# Filer /etc/rc Additions\n")
        commands.extend(cmds)

        # NFS exports are only configured on primary filers.
        # NearStores are only exported temporarily for restore purposes.
        if filer.type == 'primary':
            cmdlist = self.conf.vfiler_nfs_exports_commands(filer, vfiler, ns)

            # Only add the section if NFS commands exist
            if len(cmdlist) == 0:
                log.debug("No NFS exports defined.")
            else:
                commands.append("\n# NFS Exports Configuration\n")
                commands.extend( self.conf.vfiler_nfs_exports_commands(filer, vfiler, ns) )
                pass
            pass

        #
        # DNS commands
        #
        if 'cifs' in self.conf.allowed_protocols:
            # Set up DNS
            if filer.type in [ 'primary', 'nearstore', ]:
                log.debug("Added DNS commands for %s", filer.name)

                commands.append("\n# DNS Configuration\n")
                commands.extend( self.conf.vfiler_cifs_dns_commands(vfiler) )

        #
        # Filer options
        #
        if not filer.type == 'secondary':
            commands.append("\n# vFiler Options\n")
            commands.extend( self.conf.vfiler_set_options_commands(vfiler, ns) )

        #
        # CIFS configuration
        #
        if 'cifs' in self.conf.allowed_protocols:
            # Set up CIFS in the vFiler
            if filer.type in [ 'primary', 'nearstore']:
                commands.append("\n# Set up CIFS")
                commands.extend( ['vfiler run %s cifs setup' % vfiler.name] )

                # Remove extra shares created during 'cifs setup'
                commands.append("\n# Remove auto-created shares")
                commands.extend( ['vfiler run %s cifs shares -delete ETC$' % vfiler.name] )
                commands.extend( ['vfiler run %s cifs shares -delete HOME' % vfiler.name] )
                commands.extend( ['vfiler run %s cifs shares -delete C$' % vfiler.name] )

            # Set up CIFS shares
            if filer.type in [ 'primary', ]:
                commands.append("\n# CIFS Share Configuration")
                commands.extend( self.conf.vfiler_cifs_shares_commands(vfiler) )

        #
        # iSCSI commands
        #
        if 'iscsi' in self.conf.allowed_protocols:
            if filer.type in [ 'primary', ]:

                # iSCSI CHAP configuration
                title, cmds = self.conf.vfiler_iscsi_chap_enable_commands(filer, vfiler, prefix=ns['iscsi_prefix'])
                commands.append("\n# %s" % title)
                commands.extend(cmds)

                # iSCSI iGroup configuration
                title, cmds = self.conf.vfiler_igroup_enable_commands(filer, vfiler)
                if len(cmds) > 0:
                    commands.append("\n# %s" % title)
                    commands.extend(cmds)

                # iSCSI LUN configuration
                title, cmds = self.conf.vfiler_lun_enable_commands(filer, vfiler)
                if len(cmds) > 0:
                    commands.append("\n# %s" % title)
                    commands.extend(cmds)
                    pass
                pass
            pass
        return commands
    
class IPSANVolumeSizeCommandsGenerator(IPSANCommandsGenerator):
    """
    A generator to provide just the volume size commands for a project.
    Useful if the volume sizes have changed.
    """

    def build_filer_activation_commands(self, filer, vfiler, ns):
        """
        Build the various command sections for a specific filer.
        """
        log.debug("Adding volume size commands for %s", filer.name)
        commands = []

        commands.append( "\n#\n# Volume size commands for %s\n#" % filer.name)

        # Volumes are not created on secondary filers
        if not filer.type == 'secondary':
            commands.extend( self.conf.filer_vol_size_commands(filer) )
        return commands
        