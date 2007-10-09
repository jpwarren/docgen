#
# $Id$
#

from zope.interface import Interface

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
