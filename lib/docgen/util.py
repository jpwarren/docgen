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

def import_module(mod_name):
    """
    Custom dynamic import function to import modules.
    """
    #log.debug("looking for module: %s", mod_name)
    components = mod_name.split('.')
    #module_name = '.'.join(components[:-1])
    module_name = mod_name
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

def get_create_size(size):
    """
    Utility function
    Get the raw size in a format acceptable to the vol or lun create command,
    ie: integer amounts, and the appropriate scale (0.02g == 20m)
    """
    # Figure out if the raw volume size is fractional.
    # NetApps won't accept fractional numbers for the vol create command,
    # so we convert it from the default gigabytes to megabytes.
    if 0 < float(size) - int(size) < 1:
        log.debug("size %s is fractional gigabytes, using megabytes for create command", size)
        # Note: This uses 1000 megabytes per gigabytes, which is not true.
        # It should be base 2, not base 10, == 1024, but most humans prefer base 10.
        roundsize = round(size * 1000)
        if roundsize == 0:
            log.error("Size error: %s", size)
            raise ValueError("Attempting to create Volume/LUN of size 0!")
        return '%dm' % roundsize

    return '%dg' % round(size)
    

