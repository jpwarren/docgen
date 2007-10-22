#
# $Id$
# Dump activation commands out as as plain text
#

import zope.interface
import logging
import debug
import sys

log = logging.getLogger('docgen')

from docgen import IDocumentGenerator

class CommandGenerator:
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

    def emit(self, outfile=None, ns={}):

        if outfile is None:
            outfile = sys.stdout
        else:
            outfile = open(outfile, "w")

        cmdlist = []
        cmdlist.extend( self.build_activation_commands(ns) )

        outfile.write( '\n'.join(cmdlist) )
        outfile.write('\n')

    def build_activation_commands(self, ns):
        """
        Build the activation commands for all the filers.
        """

        activation_commands = []

        # Build the commands for all primary filers
        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'primary' ]:
            vfiler = filer.vfilers[self.conf.shortname]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'secondary' ]:
            # My vfiler is the vfiler from the primary
            vfiler = filer.secondary_for.vfilers[self.conf.shortname]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'nearstore' ]:
            vfiler = filer.vfilers[self.conf.shortname]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        # Build the commands for all secondary filers
        for filer in [ x for x in self.conf.filers.values() if x.site == 'secondary' and x.type == 'primary' ]:
            vfiler = filer.vfilers[self.conf.shortname]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site == 'secondary' and x.type == 'secondary' ]:
            # My vfiler is the vfiler from the primary
            vfiler = filer.secondary_for.vfilers[self.conf.shortname]
            activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        for filer in [ x for x in self.conf.filers.values() if x.site == 'secondary' and x.type == 'nearstore' ]:
            vfiler = filer.vfilers[self.conf.shortname]
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
        # Only create qtrees on primary filers at primary site
        #
        if filer.site == 'primary' and filer.type == 'primary':
            commands.append( "\n# Qtree Creation\n" )
            commands.extend( self.conf.filer_qtree_create_commands(filer) )

        # Create the vfiler VLAN
        commands.append("\n# VLAN Creation\n")
        commands.extend( self.conf.vlan_create_commands(filer) )

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

        if filer.type == 'primary':
            commands.append("\n# Allowed Protocols\n")
            commands.extend( self.conf.vfiler_set_allowed_protocols_commands(vfiler, ns) )

        if not filer.type == 'secondary':
            commands.append("\n# vFiler Options\n")
            commands.extend( self.conf.vfiler_set_options_commands(vfiler, ns) )

        # Careful! Quotas file is the verbatim file contents, not a list!
        # Quotas are only used on primary filers
        if filer.type == 'primary':
            commands.append("\n# Quota File Contents\n")
            commands.extend( self.conf.vfiler_quotas_add_commands(filer, vfiler, ns) )

        if filer.type == 'primary':
            commands.append("\n# Quota Enablement Commands\n")
            commands.extend(self.conf.vfiler_quota_enable_commands(filer, vfiler))

        # NFS exports are only configured on primary filers
        if filer.site == 'primary' and filer.type == 'primary':
            commands.append("\n# NFS Exports Configuration\n")
            commands.extend( self.conf.vfiler_nfs_exports_commands(filer, vfiler, ns) )

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
            if filer.site == 'secondary' and filer.type in ['primary', 'nearstore']:
                log.debug("Adding snapmirror config for '%s'", filer.name)
                commands.append("\n# SnapMirror Initialisation")
                commands.extend( self.conf.filer_snapmirror_init_commands(filer) )

        # /etc/snapmirror.conf additions
        if self.conf.has_dr:
            if filer.site == 'secondary' and filer.type in ['primary', 'nearstore']:
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
        
