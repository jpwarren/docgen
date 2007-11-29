#
# $Id$
# This module defines a document generator for creating ModiPY templates
# that can implement a given design.
# ModiPY is a Python based framework for executing commands on remote devices
# to implement a series of changes. http://modipy.seafelt.com
#

import zope.interface
from string import Template

import logging
import debug
log = logging.getLogger('docgen')

from docgen import IDocumentGenerator
from commands import IPSANCommandsGenerator

class ModiPYGenerator:
    """
    An abstract base class that implements some commonly used functions.
    """
    zope.interface.implements(IDocumentGenerator)

    def __init__(self, conf):
        self.conf = conf

class IPSANModiPYGenerator(ModiPYGenerator):
    """
    A generator for creating ModiPY templates to implement an IPSAN design.
    """

    def emit(self, outfile=None, versioned=None, ns={}):
        
        log.debug("My configuration: %s", self.conf)

        self.command_config = IPSANCommandsGenerator(self.conf)

        config_xml = self.create_modipy_config()

        if outfile is None:
            outfile = sys.stdout
        else:
##             if versioned:
##                 outfile = self.version_filename(outfile, self.conf)
##                 pass
            outfile = open(outfile, "w")
            pass
        outfile.write(config_xml)

    def create_modipy_config(self):
        """
        Output a ModiPY config file you could use to run the command list.
        """
        log.debug("Building config file...")
        config_file = Template("""
<config xmlns:xi='http://www.w3.org/2001/XInclude'>
  <provisioner
    name='netapp_provisioner'
    type='MultiConnectingProvisioner'
    command_timeout='30'>
<!--
    <command>ssh -i /home/daedalus/.ssh/configulator -o BatchMode=yes -o ServerAliveInterval=0 root@%(device.ipaddress)s "%(command.send)s"</command>
-->

  <command>/bin/bash -c "echo %(command.send)s >> /home/daedalus/testing_output"</command>


  </provisioner>

$devices

<!-- changes begin here -->
$changes
</config>
    """)

        ns = {}
        ns['devices'] = ''
    
        for filer in self.conf.filers.values():
            ns['devices'] += "<device name='%s'>\n  <ipaddress>%s</ipaddress>\n</device>\n\n" % (filer.name, filer.name)
            pass
        ns['changes'] = '\n'.join(self.get_modipy_changes())
        config_output = config_file.safe_substitute(ns)
        #log.debug("config: %s", config_output)
        return config_output
    
    def get_modipy_changes(self):
        """
        This is a really stupid demo that just runs all the commands as a
        single change, not a change tree, and doesn't use any templates.
        """
        changes = []
        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'primary' ]:
            log.debug("Building ModiPY commands for %s", filer.name)
            commands = self.generic_filer_commands(filer)

            # Convert the commands into ModiPY commands
            commandset = []
            for command in commands:
                log.debug("checking command: %s", command)
                if not command.startswith('#'):
                    commandset.append("<command>\n  <send>%s</send>\n</command>" % command)
                    pass
                pass
            commandstrings = '\n'.join(commandset)

            change = "<change name='commands_for_%s' type='CommandChange'>\n  <target>%s</target>\n<impl>\n%s\n</impl></change>" % (filer.name, filer.name, commandstrings)
            changes.append(change)
            pass
        return changes

    def generic_filer_commands(self, filer):
        vfiler = filer.vfilers[self.conf.shortname]        
        return self.command_config.build_filer_activation_commands(filer, vfiler, {})
