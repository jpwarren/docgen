#!/usr/bin/python
# $Id$
# Create a document for the IP-SAN
#
import sys
import textwrap

from datetime import datetime
from zope.interface import Interface
from string import Template
from lxml import etree
from ConfigParser import RawConfigParser

from docgen.util import load_doc_plugins
from docgen.project import Project

#from docgen.config import ProjectConfig, ConfigInvalid
from docgen.options import BaseOptions

import logging
import docgen.debug

log = logging.getLogger('docgen')

if __name__ == '__main__':

    usage = "create_document.py [options] <definition_file.xml>"

    optparser = BaseOptions(usage=usage)
    optparser.parseOptions()

    # Dynamic namespace information that is passed into document generators
    ns = {}

    # Load configuration file
    defaults = RawConfigParser()
    parsedfiles = defaults.read(optparser.options.configfile)
    if len(parsedfiles) == 0:
        raise ValueError("Cannot load configuration file: %s" % optparser.options.configfile)

    # Load the document generation plugins
    doc_plugins = load_doc_plugins(defaults)

    try:
        # load the configuration from a config file
        proj = Project()
        tree = etree.parse(optparser.options.definitionfile)
        proj.configure_from_node(tree.getroot(), defaults, None)

    except:
        log.critical("Cannot load configuration. Unhandled error condition:")
        import traceback
        traceback.print_exc()
        sys.exit(1)
        pass

    # Use the '-d' option to determine which document to generate
    docgen = doc_plugins[optparser.options.doctype](proj, defaults)
    #raise NotImplementedError("DocType of '%s' is not handled yet." % optparser.options.doctype)
    if optparser.options.outfile is not None:
        outf = open(optparser.options.outfile, "w")
        docgen.emit(outf, ns=ns)
        outf.close()
    else:
        docgen.emit(ns=ns)
