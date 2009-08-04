#
# $Id$
# Dump activation commands out as as plain text
#

import sys
from zope.interface import implements
from ConfigParser import NoSectionError, NoOptionError

import logging
from docgen import debug
log = logging.getLogger('docgen')

from docgen.interfaces import IDocumentGenerator
from docgen.base import FileOutputMixin

class CommandGenerator(FileOutputMixin):
    """
    An abstract base class that implements some commonly used functions.
    """
    implements(IDocumentGenerator)

    def __init__(self, project, defaults):
        self.project = project
        self.defaults = defaults

class NetAppCommandsGenerator(CommandGenerator):
    """
    A generator for creating the commandlines required to activate a project
    on NetApp equipment.
    """

    def emit(self, outfile=None, ns={}):

        ns['iscsi_prefix'] = self.defaults.get('global', 'iscsi_prefix')

        cmdlist = []
        cmdlist.extend( self.build_activation_commands(ns) )
        book = '\n'.join(cmdlist)
        book += '\n'

        if outfile is None:
            outfile = sys.stdout
            sys.stdout.write(book)
        else:
            outfile.write(book)
            
    def build_activation_commands(self, ns):
        """
        Build the activation commands for all the filers.
        """
        activation_commands = []

        # Build the commands for all filers
        # FIXME: Divide them up by type or site later

        for filer in self.project.get_filers():
            for vfiler in filer.get_vfilers():
                log.debug("Building activation commands for %s:%s", filer, vfiler)
                activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )
            
        # Build the commands for all primary filers
#         for filer in [ x for x in self.project.get_filers() if x.site.type == 'primary' and x.type == 'primary' ]:
#             vfiler = filer.vfilers.values()[0]
#             activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

#         for filer in [ x for x in self.project.get_filers() if x.site.type == 'primary' and x.type == 'secondary' ]:
#             # My vfiler is the vfiler from the primary
#             vfiler = filer.secondary_for.vfilers.values()[0]
#             activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

#         for filer in [ x for x in self.project.get_filers() if x.site.type == 'primary' and x.type == 'nearstore' ]:
#             vfiler = filer.vfilers.values()[0]
#             activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

#         # Build the commands for all secondary filers
#         for filer in [ x for x in self.project.get_filers() if x.site.type == 'secondary' and x.type == 'primary' ]:
#             vfiler = filer.vfilers.values()[0]
#             activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

#         for filer in [ x for x in self.project.get_filers() if x.site.type == 'secondary' and x.type == 'secondary' ]:
#             # My vfiler is the vfiler from the primary
#             vfiler = filer.secondary_for.vfilers.values()[0]
#             activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

#         for filer in [ x for x in self.project.get_filers() if x.site.type == 'secondary' and x.type == 'nearstore' ]:
#             vfiler = filer.vfilers.values()[0]
#             activation_commands.extend( self.build_filer_activation_commands(filer, vfiler, ns) )

        return activation_commands

    def build_filer_activation_commands(self, filer, vfiler, ns):
        """
        Build the various command sections for a specific filer.
        """
        log.debug("Adding activation commands for %s", filer.name)
        commands = []

        commands.append( "\n#\n# Activation commands for %s\n#" % filer.name)

        # Volumes are not created on non-active filers
        if filer.is_active_node:
            commands.append( "\n# Volume Creation\n" )
            commands.extend( self.filer_vol_create_commands(filer) )

        #
        # Create qtrees
        #
        cmds = self.filer_qtree_create_commands(filer)
        if len(cmds) > 0:
            commands.append( "\n# Qtree Creation\n" )
            commands.extend( cmds )

        # Create the vfiler VLAN
        commands.append("\n# VLAN Creation\n")
        commands.extend( self.vlan_create_commands(filer, vfiler) )

        # Create the vfiler IPspace
        commands.append("\n# IP Space Creation\n")
        commands.extend( self.ipspace_create_commands(filer) )

        # Only create the vfiler on active cluster nodes
        if filer.is_active_node:
            commands.append("\n# vFiler Creation\n")
            commands.extend( self.vfiler_create_commands(filer, vfiler) )

        # Don't add volumes on secondary filers
        if filer.is_active_node:
            commands.append("\n# vFiler Volume Addition\n")
            commands.extend( self.vfiler_add_volume_commands(filer, vfiler) )

        # Add interfaces
        commands.append("\n# Interface Configuration\n")
        commands.extend( self.vfiler_add_storage_interface_commands(filer, vfiler) )

        # Configure secureadmin
        if filer.is_active_node:
            commands.append("\n# SecureAdmin Configuration\n")
            commands.extend( self.vfiler_setup_secureadmin_ssh_commands(vfiler) )

        # Inter-project routing
##         cmds = '\n'.join( self.project.vfiler_add_inter_project_routing(vfiler) )
##         cmd_ns['commands'] += """<section>
##         <title>Inter-Project Routing</title>
##         <screen>%s</screen>
##         </section>""" % cmds


        if filer.is_active_node:
            commands.append("\n# Allowed Protocols\n")
            commands.extend( self.vfiler_set_allowed_protocols_commands(vfiler) )

        # Careful! Quotas file is the verbatim file contents, not a list!
        if filer.is_active_node:
            commands.append("\n# Quota File Contents\n")
            commands.extend(self.vfiler_quotas_add_commands(filer, vfiler) )

            commands.append("\n# Quota Enablement Commands\n")
            commands.extend(self.vfiler_quotas_enable_commands(filer, vfiler))

        # Set the snapreserves for all the volumes
        if filer.is_active_node and filer.type == 'filer':
            commands.append("\n# Snap Reserve Configuration\n")
            commands.extend( self.filer_snapreserve_commands(filer) )

        # Set up the local snapshot schedules
        if filer.is_active_node and filer.type == 'filer':
            commands.append("\n# Snapshot Configuration\n")
            commands.extend( self.filer_snapshot_commands(filer) )

        # initialise the snapvaults to the nearstore
        if filer.is_active_node and filer.type == 'nearstore':
            commands.append("\n# SnapVault Initialisation\n")
            commands.extend( self.filer_snapvault_init_commands(filer) )

        # Set up the primary side of the snapvault configuration
        # and any transfer schedules on the destination
        if filer.is_active_node:
            commands.append("\n# SnapVault Schedule Configuration\n")
            commands.extend( self.filer_snapvault_commands(filer) )

        # initialise the snapmirrors to the DR site
        # FIXME: Detect multiple site configuration somehow
        if True:
            if filer.is_active_node:
                log.debug("Adding snapmirror config for '%s'", filer.name)
                commands.append("\n# SnapMirror Initialisation")
                commands.extend( self.filer_snapmirror_init_commands(filer) )

        # Add default route
        if filer.is_active_node:
            title, cmds = self.default_route_command(filer, vfiler)
            commands.append("\n# %s\n" % title)
            commands.extend(cmds)

        # Add services vlan routes if required
        if filer.is_active_node:
            services_vlans = self.project.get_services_vlans(filer.site)
            if len(services_vlans) > 0:
                cmds = self.project.services_vlan_route_commands(vfiler)
                commands.append("\n# VLAN routes\n")
                commands.extend(cmds)

                pass
            pass

        # /etc/snapmirror.conf additions
        if filer.is_active_node:
            commands.append("\n# Filer /etc/snapmirror.conf\n")
            commands.extend( self.filer_etc_snapmirror_conf_commands(filer) )

        # /etc/hosts additions
        if filer.is_active_node and filer.type == 'filer':
            commands.append("\n# vFiler /etc/hosts\n")
            commands.extend( self.vfiler_etc_hosts_commands(filer, vfiler) )

        #
        # The /etc/rc file needs certain pieces of configuration added to it
        # to make the configuration persistent.
        #
        cmds = self.filer_etc_rc_commands(filer, vfiler)

        commands.append("\n# Filer /etc/rc Additions\n")
        commands.extend(cmds)

        # NFS exports are only configured on primary filers.
        # NearStores are only exported temporarily for restore purposes.
        # FIXME: defaults configurable?
        if filer.is_active_node and filer.type == 'filer':
            cmdlist = self.vfiler_nfs_exports_commands(filer, vfiler)

            # Only add the section if NFS commands exist
            if len(cmdlist) == 0:
                log.debug("No NFS exports defined.")
            else:
                commands.append("\n# NFS Exports Configuration\n")
                commands.extend( self.vfiler_nfs_exports_commands(filer, vfiler) )
                pass
            pass

        #
        # DNS commands
        #
        # Only enabled if CIFS is a protocol in the vfiler
        if 'cifs' in vfiler.get_allowed_protocols():
            # Set up DNS
            if filer.is_active_node:
                log.debug("Added DNS commands for %s", filer.name)

                commands.append("\n# DNS Configuration\n")
                commands.extend( self.vfiler_cifs_dns_commands(vfiler) )

        #
        # Filer options
        #
        if filer.is_active_node:
            commands.append("\n# vFiler Options\n")
            commands.extend( self.vfiler_set_options_commands(vfiler, ns) )

        #
        # CIFS configuration
        #
        if 'cifs' in vfiler.get_allowed_protocols():
            # Set up CIFS in the vFiler
            if filer.is_active_node:
                commands.append("\n# Set up CIFS")
                commands.extend( ['vfiler run %s cifs setup' % vfiler.name] )

                # Remove extra shares created during 'cifs setup'
                commands.append("\n# Remove auto-created shares")
                commands.extend( ['vfiler run %s cifs shares -delete ETC$' % vfiler.name] )
                commands.extend( ['vfiler run %s cifs shares -delete HOME' % vfiler.name] )
                commands.extend( ['vfiler run %s cifs shares -delete C$' % vfiler.name] )

            # Set up CIFS shares
            if filer.is_active_node and filer.type == 'filer':
                commands.append("\n# CIFS Share Configuration")
                commands.extend( self.project.vfiler_cifs_shares_commands(vfiler) )

        #
        # iSCSI commands
        #
        if 'iscsi' in vfiler.get_allowed_protocols():
            if filer.is_active_node and filer.type == 'filer':

                # iSCSI CHAP configuration
                title, cmds = self.project.vfiler_iscsi_chap_enable_commands(filer, vfiler, prefix=ns['iscsi_prefix'])
                commands.append("\n# %s" % title)
                commands.extend(cmds)

                # iSCSI iGroup configuration
                title, cmds = self.project.vfiler_igroup_enable_commands(filer, vfiler)
                if len(cmds) > 0:
                    commands.append("\n# %s" % title)
                    commands.extend(cmds)

                # iSCSI LUN configuration
                title, cmds = self.project.vfiler_lun_enable_commands(filer, vfiler)
                if len(cmds) > 0:
                    commands.append("\n# %s" % title)
                    commands.extend(cmds)
                    pass
                pass
            pass
        return commands

    def filer_vol_size_commands(self, filer):
        """
        The volume size commands. Useful for doing volume resizing.
        """
        cmdset = []

        for vol in filer.get_volumes():

            # If a volume is a snapmirror destination, you need to
            # do a snapmirror update before resizing it.
            if vol.type in ['snapmirrordst',]:
                cmdset.append("snapmirror update %s" % vol.name)
                
            # Volume size
            cmd = "vol size %s %s" % (vol.name, vol.get_create_size())
            cmdset.append(cmd)

        return cmdset

    def vfiler_create_commands(self, filer, vfiler):
        cmdset = []
        try:
            log.debug("IP addresses: %s", vfiler.get_ipaddresss())
            
            ipaddress = [ x for x in vfiler.get_ipaddresss() if x.type == 'primary' ][0]
            cmdset.append("vfiler create %s -n -s ips-%s -i %s /vol/%s_root" % (vfiler.name,
                                                                                vfiler.name,
                                                                                ipaddress.ip,
                                                                                vfiler.name,
                                                                                ) )
        except IndexError:
            raise IndexError("No Primary IP Address found for vfiler: %s:%s" % (filer.name, vfiler.name))
            
        for vlan,ipaddr in vfiler.services_ips:
            cmdset.append("vfiler add %s -i %s" % (vfiler.name, ipaddr,) )
        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def _vfiler_add_inter_project_routing(self, vfiler):
        """
        Provide the routing commands required to route to services VLANs
        FIXME: Look at the services VLANs in the configuration. Add to vfiler?
        """
        cmdset = []        

        # Add inter-project route if required?
        cmdset.append("vfiler run %s route add default %s 1" % (vfiler.vlan.number,
                                                                vfiler.gateway) )

        return cmdset

    def default_route_command(self, filer, vfiler):
        """
        The default route points to the VRF address for the primary VLAN.
        It may not exist yet, but having this here means no additional
        routing needs to be configured if the VRF is configured at some point.
        """
        cmdset = []
        title = "Default Route"
        proj_vlan = self.project.get_project_vlan(filer.site)
        log.debug("project vlan: %s", proj_vlan)
        cmdset.append("vfiler run %s route add default %s 1" % (vfiler.name, proj_vlan.get_networks()[0].gateway) )
        return title, cmdset
    
    def filer_vol_create_commands(self, filer):
        """
        Build the filer vol create and options commands for a filer
        """
        cmdset = []

        for vol in filer.get_volumes():
            
            # volume creation
            cmd = "vol create %s -s %s %s %s" % (vol.name, vol.space_guarantee, vol.parent.name, vol.get_create_size())
            cmdset.append(cmd)

            # volume options
            dict = vol.get_options()
            for key, value in dict.items():
                cmd = "vol options %s %s" % (key, value)
                cmdset.append(cmd)
                pass

            # volume autosize settings
            if vol.autosize:
                cmdset.extend(vol.autosize.command_add())
            pass
                
        return cmdset

    def filer_qtree_create_commands(self, filer):
        """
        Build the qtree creation commands for qtrees on volumes on filers
        """
        cmdset = []
        for vol in [ vol for vol in filer.get_volumes() if vol.type not in ['snapvaultdst', 'snapmirrordst'] ]:
            for qtree in vol.get_qtrees():
                cmdset.append( "qtree create /vol/%s/%s" % (qtree.volume.name, qtree.name) )
                cmdset.append( "qtree security /vol/%s/%s %s" % (qtree.volume.name, qtree.name, qtree.security) )
                if qtree.oplocks == False:
                    cmdset.append( "qtree oplocks /vol/%s/%s disable" % (qtree.volume.name, qtree.name) )
                pass
            pass
        return cmdset

    def vlan_create_commands(self, filer, vfiler):
        """
        Find the project VLAN for the filer's site,
        and return the command for how to create it.
        """
        cmdset = []
        vlan = self.project.get_project_vlan(filer.site)
        cmdset.append("vlan add svif0 %s" % vlan.number)

        for vlan,ipaddr in vfiler.services_ips:
            cmdset.append("vlan add svif0 %s" % vlan.number)

        return cmdset

    def ipspace_create_commands(self, filer):
        """
        Determine how to create the ipspace for the filer.
        """
        cmdset = []
        vlan = self.project.get_project_vlan(filer.site)
        cmdset.append("ipspace create ips-%s" % self.project.name)
        cmdset.append("ipspace assign ips-%s svif0-%s" % (self.project.name, vlan.number) )

        for vlan in self.project.get_services_vlans(filer.site):
            cmdset.append("ipspace assign ips-%s svif0-%s" % (self.project.name, vlan.number) )
            pass
        
        return cmdset

    def vfiler_add_volume_commands(self, filer, vfiler):
        cmdset = []
        for vol in filer.get_volumes():

            # Skip the root volume, because it's already part of the vfiler
            if vol.name.endswith("root"):
                continue
            
            cmdset.append("vfiler add %s /vol/%s" % (vfiler.name, vol.name))
            pass
        
        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_add_storage_interface_commands(self, filer, vfiler):
        cmdset = []

        mtu = vfiler.vlan.mtu

        if filer.type == 'secondary':
            cmd = "ifconfig svif0-%s mtusize %s" % ( vfiler.vlan.number, mtu )
            #cmd = "ifconfig svif0-%s 0.0.0.0 netmask %s mtusize 9000 up" % ( vfiler.vlan.number, vfiler.netmask)

        else:
            try:
                ipaddress = [ x for x in vfiler.get_ipaddresss() if x.type == 'primary' ][0]
                cmd = "ifconfig svif0-%s %s netmask %s mtusize %s up" % (vfiler.vlan.number,
                                                                         ipaddress.ip,
                                                                         ipaddress.netmask,
                                                                         mtu)
            except IndexError:
                raise IndexError("No primary IP address defined for vfiler: %s:%s" % (filer.name, vfiler.name))

        # Add partner clause if this is a primary or secondary filer
        if filer.type in [ 'primary', 'secondary' ]:
            cmd += " partner svif0-%s" % self.get_project_vlan(filer.site.type).number
        cmdset.append(cmd)

        #
        # Aliases, if applicable
        #
        for ipaddr in [ x for x in vfiler.get_ipaddresss() if x.type == 'alias' ]:
            if filer.type == 'secondary':
                # cluster partner doesn't configure the alias IPs.
                pass
            else:
                cmdset.append("ifconfig svif0-%s alias %s netmask %s mtusize %s up" % (vfiler.vlan.number, ipaddr.ip, ipaddr.netmask, mtu))

        #
        # Services VLAN interfaces
        #
        for ipaddr in [ x for x in vfiler.get_ipaddresss() if x.type == 'service' ]:
            vlan = [ x for x in filer.site.get_vlans() if x.number == ipaddr.vlan_number ][0]
            if filer.type == 'secondary':
                cmd = "ifconfig svif0-%s mtusize 1500" % ( vlan.number )
                pass
            else:
                cmd = "ifconfig svif0-%s %s netmask %s mtusize 1500 up" % (vlan.number,
                                                                           ipaddr.ip,
                                                                           vlan.get_networks()[0].netmask)
                pass

            # Add partner clause if this is a primary or secondary filer
            if filer.type in [ 'primary', 'secondary' ]:
                cmd += " partner svif0-%s" % vlan.number
                pass
            
            cmdset.append(cmd)            

        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_setup_secureadmin_ssh_commands(self, vfiler):
        """
        Setup the vfiler for secure administration.
        """
        cmdset = []
        cmdset.append('vfiler run %s secureadmin setup -q ssh 768 512 768' % vfiler.name)
        return cmdset

    def filer_snapreserve_commands(self, filer):
        cmdset = []

        for vol in filer.get_volumes():
            # snapreserve must be a non-negative integer
            cmdset.append("snap reserve %s %s" % ( vol.name, int(vol.snapreserve) ) )
            pass

        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapshot_commands(self, filer):
        """
        Filer snapshot configuration commands for the project
        """
        cmdset = []

        for vol in filer.get_volumes():
            # Do snapshot schedules
            if len(vol.snaps) > 0:
                for snap in vol.snaps:
                    cmdset.append("snap sched %s %s %s %s" % (vol.name, snap.numweekly, snap.numdaily, snap.hourly_schedule))
                pass
            else:
                cmdset.append("snap sched %s 0 0 0" % (vol.name) )
                pass

            if vol.autodelete:
                cmdset.extend(vol.autodelete.command_add())
            # Add snapshot autodelete commands, if required
            pass
                
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapvault_commands(self, filer):
        cmdset = []
        for vol in filer.get_volumes():
            if len(vol.snapvaults) > 0:
                for snap in vol.snapvaults:
                    # If the snapvault sourcevol == the volume, this is a source snapvault schedule
                    if snap.sourcevol == vol:
                        # Only create a snapvault on the source if a source schedule exists
                        if snap.src_schedule is not None:
                            cmdset.append("snapvault snap sched %s %s %s" % (vol.name, snap.basename, snap.src_schedule))
                        
                    elif snap.targetvol == vol:
                        if snap.dst_schedule is not None:
                            # Use a transfer schedule if the snapvault has a corresponding snapschedule
                            if snap.src_schedule is not None:
                                cmdset.append("snapvault snap sched -x %s %s %s" % (vol.name, snap.basename, snap.dst_schedule))
                                pass

                            # Otherwise, do a local snapvault snap on the device
                            else:
                                cmdset.append("snapvault snap sched %s %s %s" % (vol.name, snap.basename, snap.dst_schedule))
                                pass
                            pass
                        pass
                            
                    else:
                        log.error("snapvault target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            else:
                # No command to set up a blank schedule required.
                #cmdset.append("snapvault snap sched %s 0" % (vol.name) )
                pass
            
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapvault_init_commands(self, filer):
        """
        Commands used to initialise the snapvaults.
        We need to make sure we only attempt to initilise each
        snapvault once: One snapvault relationship per qtree, regardless
        of how many schedules it may have.
        """
        cmdset = []
        donelist = []
        log.debug("Initialising snapvaults...")
        for vol in filer.get_volumes():
            log.debug("found volume: %s", vol)
            if len(vol.snapvaults) > 0:
                log.debug("Setting up snapvault initialisation...")
                for snap in vol.snapvaults:
                    # If the snapvault sourcevol == the volume, this is a source snapvault schedule
                    if snap.sourcevol == vol:
                        log.error("You cannot initialise the snapvaults from the source filer.")
                        
                    elif snap.targetvol == vol:
                        # Grab the target address to use for the source
                        try:
                            source_patt = self.defaults.get('snapvault', 'source_name')
                            ns = {}
                            ns['filer_name'] = snap.sourcevol.get_filer().name
                            source_name = source_patt % ns
                        except (NoSectionError, NoOptionError):
                            source_name = "%s" % snap.sourcevol.get_filer().name
                        
                        if snap.sourcevol.name.endswith('root'):
                            if (snap.sourcevol.filer, snap.sourcevol, 'root') not in donelist:
                                cmdset.append("snapvault start -S %s:/vol/%s/- /vol/%s/%s" % (source_name, snap.sourcevol.name, snap.targetvol.name, snap.sourcevol.name ))
                                
                                donelist.append( (snap.sourcevol.get_filer(), snap.sourcevol, 'root') )

                        # Snapvault relationships are done at the qtree level
                        for qtree in snap.sourcevol.get_qtrees():
                            if (snap.sourcevol.get_filer(), snap.sourcevol, qtree) not in donelist:
                                log.debug("Not in donelist. Initialising %s:/vol/%s/%s", snap.sourcevol.get_filer().name, snap.sourcevol.name, qtree.name)
                                cmdset.append("snapvault start -S %s:/vol/%s/%s /vol/%s/%s" % (source_name, snap.sourcevol.name, qtree.name, snap.targetvol.name, qtree.name ))
                                donelist.append( (snap.sourcevol.get_filer(), snap.sourcevol, qtree) )
                            else:
                                log.debug("Skipping duplicate snapvault initialisation for %s:/vol/%s/%s", snap.sourcevol.get_filer().name, snap.sourcevol.name, qtree.name)
                    else:
                        log.error("snapvault target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_snapmirror_init_commands(self, filer):
        """
        Commands used to initialise the snapmirrors.
        We need to make sure we only attempt to initilise each
        snapmirror once: One snapmirror relationship per volume, regardless
        of how many schedules it may have.
        """
        cmdset = []
        donelist = []
        for vol in filer.get_volumes():
            if len(vol.snapmirrors) > 0:
                for snap in vol.snapmirrors:
                    # If the sourcevol == the volume, this is a source snapmirror schedule
                    if snap.sourcevol == vol:
                        log.error("You cannot initialise the snapmirror from the source filer.")
                        
                    elif snap.targetvol == vol:
                        if (snap.sourcevol, snap.targetvol) not in donelist:
                            cmdset.append("vol restrict %s" % snap.targetvol.name)
                            cmdset.append("snapmirror initialize -S %s-svif0-2000:%s %s" % (snap.sourcevol.filer.name, snap.sourcevol.name, snap.targetvol.name))
                                
                            donelist.append( (snap.sourcevol, snap.targetvol) )
                    else:
                        log.error("snapmirror target and source are not for '%s'" % vol.name)
                        pass
                    pass
                pass
            pass
        
        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_etc_snapmirror_contents(self, filer):
        """
        Returns the lines to append to the /etc/snapmirror file
        on the filer for this project.
        """
        cmdset = []
        for vol in filer.get_volumes():
            for snap in vol.snapmirrors:
                # If the sourcevol == the volume, this is the source side, so ignore it
                if snap.sourcevol == vol:
                    log.warn("/etc/snapmirror not used on the source filer.")
                        
                elif snap.targetvol == vol:
                    # Use a transfer schedule
                    cmdset.append("%s-svif0-2000:%s %s:%s %s %s" % (snap.sourcevol.filer.name, snap.sourcevol.name, snap.targetvol.filer.name, snap.targetvol.name, snap.arguments, snap.etc_snapmirror_conf_schedule()))
                else:
                    log.error("snapmirror target and source are not for '%s'" % vol.name)
                    pass
                pass
            pass

        if len(cmdset) > 0:
            cmdset.insert(0, "#")
            cmdset.insert(0, "# %s" % self.shortname)
            cmdset.insert(0, "#")

        #log.debug('\n'.join(cmdset))
        return cmdset

    def filer_etc_snapmirror_conf_commands(self, filer):
        """
        Returns a list of commands that can be used to append to
        the /etc/snapmirror file on the filer for this project.
        """
        cmdset = []
        file_contents = self.filer_etc_snapmirror_contents(filer)
        
        for line in file_contents:
            if len(line) == 0:
                continue
            line = line.replace('#', '##')

            cmdset.append('wrfile -a /etc/snapmirror.conf "%s"' % (line))
            pass

        return cmdset

    def vfiler_etc_hosts_contents(self, filer, vfiler):
        """
        Generate the additions for the /etc/hosts file on the
        vfiler that are specific to this project.
        """
        ipaddress = [ x for x in vfiler.get_ipaddresss() if x.type == 'primary' ][0]
        file = """#
# %s
#
%s %s-svif0-%s
""" % (vfiler.name, ipaddress.ip, filer.name, vfiler.vlan.number )

        for ipaddress in [ x for x in vfiler.get_ipaddresss() if x.type == 'service' ]:
            file += '\n%s %s-svif0-%s' % (ipaddress.ip, filer.name, ipaddress.vlan.number)
        return file

    def vfiler_etc_hosts_commands(self, filer, vfiler):
        """
        Returns a list of commands that can be used to create the /etc/hosts
        file within a particular vfiler for the project.
        """
        cmdset = []
        file_contents = self.vfiler_etc_hosts_contents(filer, vfiler)
        for line in file_contents.split('\n'):
            if len(line) == 0:
                continue
            line = line.replace('#', '##')

            cmdset.append('wrfile -a /vol/%s_root/etc/hosts "%s"' % (vfiler.name, line))
            pass

        return cmdset

    def filer_etc_rc_commands(self, filer, vfiler):
        """
        Returns a list of commands that can be used to add the /etc/rc
        entries to the filer.
        """
        cmdset = []
        cmds = [ '#', '# %s' % vfiler.name, '#' ] 
        cmds += self.vlan_create_commands(filer, vfiler)
        cmds += self.vfiler_add_storage_interface_commands(filer, vfiler)
        cmds += self.services_vlan_route_commands(vfiler)
        title, routecmds = self.default_route_command(filer, vfiler)
        cmds += routecmds
        
        for line in cmds:
            if len(line) == 0:
                continue
            line = line.replace('#', '##')
            cmdset.append('wrfile -a /vol/vol0/etc/rc "%s"' % line)

        return cmdset

    def services_vlan_route_commands(self, vfiler):
        """
        Services VLANs are different from VRFs. Services VLANs are actual VLANs
        that are routed via firewalls into the main corporate network to provide
        access to services, such as Active Directory.
        """
        cmdset = []
        log.debug("vfiler services vlans: %s", vfiler.services_ips)

        known_dests = []
        for (vlan, ipaddress) in vfiler.services_ips:
            log.debug("Adding services routes: %s", vlan)
            for ipaddr in vfiler.nameservers:
                if ipaddr not in known_dests:
                    cmdset.append("vfiler run %s route add host %s %s 1" % (vfiler.name, ipaddr, vlan.networks[0].gateway) )
                    known_dests.append(ipaddr)
                    pass
                pass
            
            for ipaddr in vfiler.winsservers:
                if ipaddr not in known_dests:
                    cmdset.append("vfiler run %s route add host %s %s 1" % (vfiler.name, ipaddr, vlan.networks[0].gateway) )
                    known_dests.append(ipaddr)
                    pass
                pass
            pass

        if len(vfiler.services_ips) > 0:
            # add the cifs prefdc commands to prefer domain controllers in the right order
            cmdset.append( "vfiler run %s cifs prefdc add %s %s" % (vfiler.name, vfiler.dns_domain_name, ' '.join(vfiler.winsservers)))
            pass
        
        return cmdset
            
    def vfiler_set_allowed_protocols_commands(self, vfiler):
        cmdset = []

        # first, disallow everything
        cmdset.append("vfiler disallow %s proto=rsh proto=http proto=ftp proto=iscsi proto=nfs proto=cifs" % vfiler.name)

        # then, allow the ones we want
        for proto in vfiler.get_allowed_protocols():
            cmdset.append("vfiler allow %s proto=%s" % (vfiler.name, proto) )

        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_set_options_commands(self, vfiler, ns):
        cmdset = []

        options = [
            # not required, since we snapvault in vfiler0
            #'snapvault.enable on',
            'nfs.tcp.recvwindowsize 65536',
            'nfs.tcp.xfersize 65536',
            'cifs.tcp_window_size 64240',
            'cifs.neg_buf_size 33028',
            'iscsi.max_ios_per_session 256',
            'nfs.udp.enable off',
            ]

        for vol in vfiler.filer.get_volumes():
            if len(vol.snapmirrors) > 0:
                options.append('snapmirror.enable on')
                break

        # DNS enablement options for CIFS capable vfilers
        if 'cifs' in vfiler.get_allowed_protocols():
            if vfiler.dns_domain is None:
                raise ValueError("CIFS protocol enabled, but DNS domain not set for vFiler %s:%s" % (vfiler.parent.name, vfiler.name))
            else:
                options.append("dns.domainname %s" % vfiler.dns_domain)
                options.append("dns enable on")
            
        for opt in options:
            cmdset.append("vfiler run %s options %s" % (vfiler.name, opt) )
            pass
        
        #log.debug( '\n'.join(cmdset) )
        return cmdset

    def vfiler_quotas_file_contents(self, filer, vfiler):
        """
        Generate the /etc/quotas file contents for the vfiler
        """
        quota_file = """#
# Quotas for %s
#
""" % vfiler.name

        for vol in [x for x in filer.get_volumes() if x.type not in ['snapmirrordst']]:
            if not vol.name.endswith('root'):
                quota_file += '*    tree@/vol/%s    -    -    -    -    -\n' % vol.name
                pass
            pass

        #log.debug(quota_file)
        return quota_file

    def vfiler_quotas_add_commands(self, filer, vfiler):
        """
        Return a list of commands that can be used to activate the quotas
        """
        cmdset = []
        file_contents = self.vfiler_quotas_file_contents(filer, vfiler)
        for line in file_contents.split('\n'):
            if len(line) == 0:
                continue
            line = line.replace('#', '##')

            cmdset.append('wrfile -a /vol/%s_root/etc/quotas "%s"' % (vfiler.name, line))
            pass

        return cmdset
        
    def vfiler_quotas_enable_commands(self, filer, vfiler):
        cmdset = []
        for vol in [x for x in filer.get_volumes() if x.type not in ['snapmirrordst']]:
            if not vol.name.endswith('root'):
                cmdset.append("vfiler run %s quota on %s" % (vfiler.name, vol.name))
                pass
            pass
        return cmdset
    
    def vfiler_nfs_exports_commands(self, filer, vfiler):
        """
        Provide a list of nfs export commands.
        We need to change into the vfiler context to run these commands.
        """
        cmdset = []
        #cmdset.append("vfiler context %s" % vfiler.name)
        log.debug("Finding NFS exports for filer: %s", filer.name)

        try:
            export_security = self.defaults.getboolean('nfs', 'export_security')
        except (NoSectionError, NoOptionError):
            export_security = True
        
        # Do we do exports to each IP, or to the entire subnet?
        try:
            subnet_exports = self.defaults.getboolean('nfs', 'subnet_exports')
        except (NoSectionError, NoOptionError):
            subnet_exports = False
        
        for vol in [ x for x in filer.get_volumes() if x.protocol == 'nfs' ]:
            log.debug("Found volume: %s", vol)
            for qtree in vol.get_qtrees():
                log.debug("exporting qtree: %s", qtree)

                # Find read/write exports
                rw_export_to = []
                if export_security:
                    for export in qtree.get_rw_exports():
                        if export.toip is not None:
                            rw_export_to.append( export.toip )
                        else:
                            if subnet_exports:
                                raise NotImplementedError("Subnet exports not yet supported")
                                pass
                            else:
                                rw_export_to.extend([x.ip for x in export.tohost.get_storage_ips()])
                                pass
                            pass
                        pass
                    pass
                else:
                    # Export to everything
                    rw_export_to.append( '*' )
                    pass
                
                # Find read-only exports
                ro_export_to = []
                if export_security:
                    for export in qtree.get_ro_exports():
                        if export.toip is not None:
                            ro_export_to.append( export.toip )
                        else:
                            ro_export_to.extend([x.ip for x in export.tohost.get_storage_ips()])
                            pass
                        pass
                
                if len(ro_export_to) > 0:
                    #log.debug("Read only exports required!")
                    ro_export_str = "ro=%s," % ':'.join(ro_export_to)
                else:
                    ro_export_str = ''

                if len(rw_export_to) > 0:
                    rw_export_str = "rw=%s," % ':'.join(rw_export_to)
                else:
                    rw_export_str = ''

                # allow root mount of both rw and ro hosts
                root_exports = rw_export_to + ro_export_to

                aliases = qtree.get_exportaliass()
                if len(aliases) > 0:
                    log.debug("Aliases exist. Using 'actual' export option.")
                    for alias in aliases:
                        export_line = "vfiler run %s exportfs -p actual=/vol/%s/%s,%s%sroot=%s %s" % (
                            vfiler.name,
                            vol.name,
                            qtree.name,
                            rw_export_str,
                            ro_export_str,
                            ':'.join(root_exports),
                            alias,
                            )
                else:
                    export_line = "vfiler run %s exportfs -p %s%sroot=%s /vol/%s/%s" % (
                        vfiler.name,
                        rw_export_str,
                        ro_export_str,
                        ':'.join(root_exports),
                        vol.name, qtree.name,
                        )
                    pass
                cmdset.append(export_line)
                
                # Manual linewrap setup
##                 if len(export_line) > 90:
##                     wraplines = textwrap.wrap(export_line, 90)
##                     cmdset.append( '\\\n'.join(wraplines))
            pass
        #log.debug('\n'.join(cmdset))
        #cmdset.append("vfiler context vfiler0")
        return cmdset

    def vfiler_cifs_dns_commands(self, vfiler):
        """
        Return the commands for configuring DNS for CIFS access
        """
        cmds = []
        for nameserver in vfiler.get_nameservers():
            cmds.append("wrfile -a /vol/%s_root/etc/resolv.conf nameserver %s" % (vfiler.name, nameserver))

        return cmds

    def vfiler_cifs_shares_commands(self, vfiler):
        """
        For all the CIFS qtrees in the VFiler, return the commands
        used to configure the shares.
        """
        cmds = []
        volumes = [ x for x in vfiler.filer.get_volumes() if x.proto == 'cifs' ]
        for vol in volumes:
            for qtree in vol.qtrees.values():
                log.debug("Determining CIFS config commands for %s", qtree)
                cmds.append("vfiler run %s cifs shares -add %s %s -f" % (vfiler.name, qtree.cifs_share_name(), qtree.full_path()) )
                cmds.append("vfiler run %s cifs access -delete %s everyone" % (vfiler.name, qtree.cifs_share_name() ) )

                cmds.append('vfiler run %s cifs access %s \"domain admins\" rwx' % (vfiler.name, qtree.cifs_share_name() ) )

##                 for host in qtree.rwexports:
##                     cmds.append("vfiler run %s cifs access %s CORP\%s Full Control" % (vfiler.name, qtree.cifs_share_name(), host.name ) )
##                 for host in qtree.roexports:
##                     cmds.append("vfiler run %s cifs access %s CORP\%s rx" % (vfiler.name, qtree.cifs_share_name(), host.name ) )

        return cmds

    def vfiler_iscsi_chap_enable_commands(self, filer, vfiler, prefix):
        """
        Return the commands required to enable the vfiler configuration
        """
        title = "iSCSI CHAP Configuration for %s" % filer.name
        cmds = []
        cmds.append("vfiler run %s iscsi security default -s CHAP -n %s -p %s" % (vfiler.name, vfiler.name, self.get_iscsi_chap_password(prefix) ) )
        return title, cmds

    def vfiler_igroup_enable_commands(self, filer, vfiler):
        """
        Return the commands required to enable the vfiler iGroup configuration
        """
        title = "iSCSI iGroup Configuration for %s" % filer.name
        cmds = []
        for igroup in self.get_filer_iscsi_igroups(filer):
            if igroup.exportlist[0].tohost.iscsi_initiator is None:
                raise ValueError("Host %s in igroup has no iSCSI initiator defined" % igroup.exportlist[0].tohost.name)
            cmds.append("vfiler run %s igroup create -i -t %s %s %s" % (vfiler.name, igroup.type, igroup.name, igroup.exportlist[0].tohost.iscsi_initiator) )
            if len(igroup.exportlist) > 1:
                for export in igroup.exportlist[1:]:
                    cmds.append("vfiler run %s igroup add %s %s" % (vfiler.name, igroup.name, export.tohost.iscsi_initiator) )
        return title, cmds

    def vfiler_lun_enable_commands(self, filer, vfiler):
        """
        Return the commands required to enable the vfiler LUN configuration
        """
        title = "iSCSI LUN Configuration for %s" % filer.name
        cmds = []
        for igroup in self.get_filer_iscsi_igroups(filer):
            for lun in igroup.lunlist:
                # Don't create LUNs on snapmirror destination volumes
                if lun.qtree.volume.type not in ['snapmirrordst']:
                    cmds.append("vfiler run %s lun create -s %s -t %s %s" % (vfiler.name, lun.get_create_size(), lun.ostype, lun.full_path()) )
                cmds.append("vfiler run %s lun map %s %s %s" % (vfiler.name, lun.full_path(), igroup.name, lun.lunid) )
                pass
            pass

        return title, cmds

class VolumeSizeCommandsGenerator(NetAppCommandsGenerator):
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
            commands.extend( self.project.filer_vol_size_commands(filer) )
        return commands
        

