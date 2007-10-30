#
# $Id$
#

from zope.interface import Interface

import os.path

import logging
import debug
log = logging.getLogger('docgen')

class IDocumentGenerator(Interface):
    """
    The IDocumentGenerator is an interface that should be implemented by
    DocumentGenerators.
    """

    def __init__(self, conf):
        """
        A DocumentGenerator requires a parsed configuration as input.
        """

    def emit(self, outfile=None, ns={}):
        """
        emit() sends the output of the generator to an outfile.
        If no output file is specified, it outputs to STDOUT.
        An optional namespace can be provided with values for
        the document generator to use.
        """

class FileOutputMixin:
    """
    A mixin to provide some utility functions for outputing to files.
    """

    def version_filename(self, filename, conf):
        """
        Return a filename that has had the version information from a configuration
        appended to it.
        """
        # Get the revision information from the config
        rev = conf.get_latest_revision()
        
        # Take the filename, and insert the revision information before the suffix
        base, ext = os.path.splitext(filename)
        vers_filename = '%s-v%s.%s%s' % (base, rev.majornum, rev.minornum, ext)
        #log.debug("Versioned filename: %s", vers_filename)
        return vers_filename
