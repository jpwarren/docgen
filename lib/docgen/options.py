#
# DocGen options configuration module
#

import optparse
import sys
import logging
import debug

log = logging.getLogger('docgen')

class BaseOptions(optparse.OptionParser):
    """
    The base options parser class.
    This defines all the base level options and arguments that are
    common to all programs.
    """
    def __init__(self, *args, **kwargs):
        """
        Initialise the parser with all the default things an OptionParser
        would have, plus the base level options common to all
        programs.
        """
        optparse.OptionParser.__init__(self, **kwargs)

        help_license = 'Display the license agreement and exit.'
        help_debug = "Set the output debug level to: debug, info, warn, error, or critical."
        help_logfile = "Log to specified file instead of default logfile"
        help_no_logfile = "Disable logging to logfile"

        help_config_file = "DocGen defaults configuration file"
        help_definition_file = "XML project definition file"
        help_outfile = "Write output to this file, instead of STDOUT"
        help_versioned = "Enable auto-versioning of output filenames"
        help_doctype = "What sort of document to create"
        help_modipy_templates = "Path to ModiPy templates"

        self.add_option('', '--license',       dest='license', action='store_true', help=help_license)    
        self.add_option('', '--debug',         dest='debug', type='choice', choices=('debug', 'info', 'warn', 'error', 'critical'), metavar='LEVEL', default='info', help=help_debug)
        self.add_option('', '--logfile',       dest='logfile', type='string', help=help_logfile)
        self.add_option('', '--no-logfile',    dest='no-logfile', action='store_true', default=False, help=help_no_logfile)

        self.add_option('-c', '--configfile',      dest='configfile', type='string', default='/usr/local/docgen/etc/docgen.conf', help=help_config_file)
        self.add_option('-D', '--definition',      dest='definitionfile', type='string', help=help_definition_file)
        self.add_option('-o', '--outfile',     dest='outfile', type='string', help=help_outfile)
        self.add_option('', '--versioned',     dest='versioned', action='store_true', default=False, help=help_versioned)
        #self.add_option('', '--not-versioned', dest='versioned', action='store_false', default=True, help=help_not_versioned)
        self.add_option('', '--modipy-templates',     dest='modipy_templates', type='string', help=help_modipy_templates)
        self.add_option('-d', '--doctype',     dest='doctype', type='string', default='ipsan-storage-design', help=help_doctype)
        
        self.addOptions()

    def addOptions(self):
        """
        Override this method in subclasses to add more options.
        This enables multiple inheritence from the common base class.
        """
        pass
        
    def parseOptions(self, argv=sys.argv[1:]):
        """
        Emulate the twisted options parser API.
        """
        options, args = self.parse_args(argv)
        self.options = options
        self.args = args
        self.postOptions()

    def postOptions(self):
        """
        Perform post options parsing operations.
        """
        # Set standard logging level
        log.setLevel(logging._levelNames.get(self.options.debug.upper(), logging.INFO))

        if self.options.license:
            raise NotImplementedError("License output not configured.")
            sys.exit(1)
            pass

        if not self.options.definitionfile:
            try:
                self.options.definitionfile = self.args[0]
            except IndexError:
                self.error("No definition file specified")

