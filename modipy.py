#
# $Id$
# This module defines a document generator for creating ModiPY templates
# that can implement a given design.
# ModiPY is a Python based framework for executing commands on remote devices
# to implement a series of changes. http://modipy.seafelt.com
#
import sys
import os.path
import zope.interface
import logging
import debug

from lxml import etree

from string import Template

log = logging.getLogger('docgen')

from docgen import IDocumentGenerator

class ModiPYGenerator:
    """
    An abstract base class that implements some commonly used functions.
    """
    zope.interface.implements(IDocumentGenerator)

    def __init__(self, conf, template_path=None):
        self.conf = conf
        self.template_path = template_path

class IPSANStorageModiPYGenerator(ModiPYGenerator):
    """
    A generator for creating ModiPY templates to implement an IPSAN storage design.
    """

    # Define some important Templates
    config_template = Template("""<config xmlns:xi='http://www.w3.org/2001/XInclude'>
    <!-- Include change templates -->
    $includes

    <!-- Define provisioners -->
    $provisioners
    
    <!-- Define devices -->
    $devices

    <!-- Define iterators that are used by changes -->
    $iterators

    <!-- Define changes that use pre-defined templates -->
    $templated_changes

    <!-- Define changes that do not use pre-defined templates -->
    $non_templated_changes

</config>""")
    
    def emit(self, outfile=None, versioned=True, ns={}):
    #def emit(self, outfile=None, ns={}):

        if outfile is None:
            outfile = sys.stdout
        else:
            if versioned:
                outfile = self.version_filename(outfile, self.conf)
                pass
            outfile = open(outfile, "w")
            pass
    
        ns['includes'] = self.build_includes()
        ns['provisioners'] = self.build_provisioners()
        ns['devices'] = self.build_devices()
        ns['iterators'] = self.build_iterators()
        ns['templated_changes'] = self.build_templated_changes()
        ns['non_templated_changes'] = self.build_non_templated_changes()

        output = self.config_template.safe_substitute(ns)
        output = etree.fromstring( output, parser=etree.XMLParser() )
        #log.debug("output: %s", output )
        outfile.write( etree.tostring(output, pretty_print=True) )
        #outfile.write(output)
        outfile.write('\n')

    def build_includes(self):
        """
        Build a list of all the includes we need to be able to access
        pre-defined change templates.
        FIXME: Need to somehow deal with the template location path
        for modipy. May need to patch modipy.
        """
        retstr = ''
        # A set of the hrefs needed to find the templates
        includes = [
            "netapp-create-volume.zapi.change-template.xml",
            "netapp-set-volume-option.zapi.change-template.xml",            
            ]

        if self.template_path is not None:
            include_list = [ "<xi:include href='%s'/>" % os.path.join(self.template_path, x) for x in includes ]
        else:
            include_list = [ "<xi:include href='%s'/>" % x for x in includes ]
        return '\n'.join(include_list)
            
    def build_provisioners(self):
        """
        Build the provisioner definition section for a changeset configuration.
        """
        return """
        <!-- A command provisioner for cmdline provisioning -->
        <provisioner name='netapp_provisioner'
                     module='modipy.provisioner_command'
                     type='MultiConnectingProvisioner'
                     command_timeout='60'>

          <command>ssh -o BatchMode=yes -o ServerAliveInterval=0 root@%(device.ipaddress)s "%(command.send)s"</command>
        </provisioner>
        
        <!-- A ZAPI provisioner -->
        <provisioner name='netapp_zapi_provisioner'
                     module='modipy.netapp'
                     type='ZAPIProvisioner'
                     command_timeout='30'>
        </provisioner>
        """

    def build_devices(self):
        """
        Build the device definition section for a changeset
        """
        retstr = ''
        for filer in self.conf.filers.values():
            retstr += "\n<device name='%s'/>" % filer.name
            pass
        return retstr

    def build_iterators(self):
        """
        Build dictionaries of iteration values that can be used with changes
        or change templates.
        """
        iterator_template = Template("""<iterator name='$itername'>$iterdicts</iterator>""")
        iterators = []
        # We need an iterator for the volumes to be created on each filer
        for filer in self.conf.filers.values():
            volumes = []
            voloptions = []
            for vol in filer.volumes:
                voldict = {}
                voldict['volname'] = vol.name
                voldict['volaggr'] = vol.aggregate
                voldict['volsize'] = vol.get_create_size()
                volumes.append( self.dict_to_iterator_dict(voldict) )

                # Add an iterator for the volume options
                for opt in vol.voloptions:
                    odict = {}
                    key, value = opt.split('=')
                    odict['volname'] = vol.name
                    odict['option_name'] = key
                    odict['option_value'] = value
                    voloptions.append( self.dict_to_iterator_dict(odict) )

            iterators.append( iterator_template.substitute(itername='iter.%s.volumes' % filer.name, iterdicts=''.join(volumes)) )
            iterators.append( iterator_template.substitute(itername='iter.%s.volume-options' % filer.name, iterdicts=''.join(voloptions)) )
            
        return '\n'.join(iterators)

    def build_templated_changes(self):
        """
        Build the change definitions that make use of change templates.
        """
        changes = []

        # A change to sync all change implementations to a common root dependency
        changes.append("""<change name='start' type='CommandChange'><target>ALL_TARGETS</target></change>""")

        # Do all the stuff on the primary filers first
        for filer in [ x for x in self.conf.filers.values() if x.site == 'primary' and x.type == 'primary' ]:
            vfiler = filer.vfilers.values()[0]
            changes.extend( self.build_filer_templated_changes(filer, vfiler) )
        
        return '\n'.join(changes)

    def build_filer_templated_changes(self, filer, vfiler):
        """
        Build a list of all the templated changes to use for this filer.
        """
        change_tmpl = Template("""<change name='$name' template='$template' iterator='$iterator'>
          <depends on='$prereq'/>
          <target>$target</target>
        </change>""")

        changes = []

        #
        # Create volumes
        # Volumes are not created on secondary filers
        if not filer.type == 'secondary':
            changename = '%s-create-volumes' % filer.name
            itername = 'iter.%s.volumes' % filer.name
            changes.append( change_tmpl.substitute(name=changename,
                                                   iterator=itername,
                                                   target=filer.name,
                                                   prereq='start',
                                                   template='create_netapp_volume')
                            )
            # We use the previous changename as a dependency so that we step through changes
            # in the correct order.
            prev_changename = changename

            # Set volume options
            changename = '%s-set-volume-options' % filer.name
            itername = 'iter.%s.volume-options' % filer.name
            changes.append( change_tmpl.substitute(name=changename,
                                                   iterator=itername,
                                                   target=filer.name,
                                                   prereq=prev_changename,
                                                   template='netapp_set_volume_option')
                            )
            pass

        #
        # Create qtrees
        #

        return changes
    
    def build_non_templated_changes(self):
        """
        Build the change definitions that do not make use of change templates.
        """
        changes = []

##         changes.append("""<change name='dummy' type='CommandChange'>
##           <target>wibble</target>
##         </change>
##         """)
        
        return ''.join(changes)

    def dict_to_iterator_dict(self, dict):
        """
        Convert a Python dictionary to a ModiPy iterator
        """
        dict_template = Template("""<dict>$entries</dict>""")
        entry_template = Template("""<entry name='$key'>$value</entry>""")

        entries = []
        for key in dict:
            entries.append( entry_template.substitute(key=key, value=dict[key]) )
            #log.debug("entries is: %s", entries)
            pass

        return dict_template.substitute(entries=''.join(entries))
            
