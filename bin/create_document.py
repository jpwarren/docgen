#!/usr/bin/python
#
# Create a document for the IP-SAN
#
import sys
import textwrap

from datetime import datetime
from zope.interface import Interface
from string import Template
from lxml import etree

from docgen.config import ProjectConfig, ConfigInvalid
from docgen.ipsan_storage import IPSANStorageDesignGenerator
from docgen.ipsan_network import IPSANNetworkDesignGenerator
from docgen.modipy import IPSANStorageModiPYGenerator
from docgen.commands import IPSANCommandsGenerator, IPSANVolumeSizeCommandsGenerator
from docgen.activation_advice import IPSANActivationAdvice

from docgen.options import BaseOptions

import logging
import docgen.debug

log = logging.getLogger('docgen')

__version__ = '$Revision$'

if __name__ == '__main__':

    usage = "create_document.py [options] <definition_file.xml>"

    optparser = BaseOptions(usage=usage)
    optparser.parseOptions()

    # Dynamic namespace information that is passed into document generators
    ns = {}

    try:
        # load the configuration from a config file
        proj = ProjectConfig(optparser.options.definitionfile, optparser.options.configfile)

    except ConfigInvalid, e:
        log.critical("Cannot load configuration: %s.", e)
        sys.exit(1)
        
    except:
        log.critical("Cannot load configuration. Unhandled error condition:")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Use the configuration document to decide what goes into the generated document
    if optparser.options.doctype == 'ipsan-storage-design':
        docgen = IPSANStorageDesignGenerator(proj)
        ns['title'] = 'IPSAN Storage Design'

    elif optparser.options.doctype == 'ipsan-network-design':
        docgen = IPSANNetworkDesignGenerator(proj)
        ns['title'] = 'IPSAN Network Design'
    
    elif optparser.options.doctype == 'ipsan-storage-modipy':
        docgen = IPSANStorageModiPYGenerator(proj, template_path=optparser.options.modipy_templates)

    elif optparser.options.doctype == 'ipsan-storage-commands':
        docgen = IPSANCommandsGenerator(proj)

    elif optparser.options.doctype == 'vol-sizes':
        docgen = IPSANVolumeSizeCommandsGenerator(proj)

    elif optparser.options.doctype == 'ipsan-activation-advice':
        docgen = IPSANActivationAdvice(proj)
        
    else:
        raise NotImplementedError("DocType of '%s' is not handled yet." % optparser.options.doctype)

    docgen.emit(optparser.options.outfile, optparser.options.versioned, ns=ns)
