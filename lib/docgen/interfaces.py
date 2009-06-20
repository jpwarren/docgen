# $Id$
#

"""
Interface definitions
"""
from zope.interface import Interface

class IXMLConfigurable(Interface):
    """
    Anything that is XMLConfigurable can be used by the system
    to define objects for loading and documentation generation.
    """
    def configure_from_node(self, node, defaults, parent):
        """
        @param node: an L{lxml.Element} encapsulating the XML node
        @param defaults: a L{ConfigParser.RawConfigParser} object containing
        configuration file defaults
        @param parent: the parent object of this object
        """

class IDynamicNaming(Interface):

    def populate_namespace(self, ns={}):
        """
        Take a namespace passed in (or a blank one)
        and add any extra bits to be found at this
        level to the namespace.
        """

class IDocumentGenerator(Interface):
    """
    The IDocumentGenerator is an interface that should be implemented by
    DocumentGenerators.
    """

    def __init__(self, conf):
        """
        A DocumentGenerator requires a parsed configuration as input.
        """

    def emit(self, config=None, outfile=None, ns={}):
        """
        emit() sends the output of the generator to an outfile.
        If no output file is specified, it outputs to STDOUT.
        An optional namespace can be provided with values for
        the document generator to use.
        """
