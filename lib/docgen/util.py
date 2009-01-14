#
# $Id$
# 
"""
Utility functions.
"""
import sys

import debug
import logging
log = logging.getLogger('docgen')

def import_module(klass_name):
    """
    Custom dynamic import function to import modules.
    """
    components = klass_name.split('.')
    module_name = '.'.join(components[:-1])

    mod = __import__(module_name)
    for comp in components[1:]:
        mod = getattr(mod, comp)
        pass
    return mod

def load_doc_plugins(defaults):
    """
    Load modules that will generate output documents.
    This allows people to write their own 'plugins' that
    define an output document type that conforms to the
    DocGen IDocumentGenerator interface.

    Which modules to load is defined in the configuration file,
    which is passed to this function as an argument.
    """
    plugins = {}
    items = defaults.items('document_plugins')
    for name, module in items:
        plugins[name] = import_module(module)

    return plugins
