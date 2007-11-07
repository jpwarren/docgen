#
# Sensis DocGen options configuration module
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

        help_config = "XML project definition file"
        help_outfile = "Write output to this file, instead of STDOUT"
        help_not_versioned = "Disable auto-versioning of output filenames"
        help_doctype = "What sort of document to create"

        self.add_option('', '--license',       dest='license', action='store_true', help=help_license)    
        self.add_option('', '--debug',         dest='debug', type='choice', choices=('debug', 'info', 'warn', 'error', 'critical'), metavar='LEVEL', default='info', help=help_debug)
        self.add_option('', '--logfile',       dest='logfile', type='string', help=help_logfile)
        self.add_option('', '--no-logfile',    dest='no-logfile', action='store_true', default=False, help=help_no_logfile)

        self.add_option('-c', '--config',      dest='configfile', type='string', help=help_config)
        self.add_option('-o', '--outfile',     dest='outfile', type='string', help=help_outfile)
        self.add_option('', '--not-versioned', dest='versioned', action='store_false', default=True, help=help_not_versioned)
        self.add_option('-d', '--doctype',     dest='doctype', type='choice', choices=['ipsan-storage-design',
                                                                                       'ipsan-storage-cip',
                                                                                       'ipsan-activation-advice',
                                                                                       'ipsan-modipy-config',
                                                                                       'ipsan-commands',
                                                                                       'vol-sizes',
                                                                                       ], default='ipsan-storage-design', help=help_doctype)
        
        self.addOptions()

    def addOptions(self):
        """
        Override this method in subclasses to add more options.
        This enables multiple inheritence from the common base class.
        """
        pass
        
    def parseOptions(self):
        """
        Emulate the twisted options parser API.
        """
        options, args = self.parse_args(sys.argv[1:])
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

        if not self.options.configfile:
            try:
                self.options.configfile = self.args[0]
            except IndexError:
                self.error("No configuration file specified")

