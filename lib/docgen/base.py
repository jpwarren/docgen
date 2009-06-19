#$Id$
#

"""
Base definitions
"""

class DynamicNaming:
    """
    A Mixin class used for doing dynamic naming
    using naming conventions loaded in from a
    defaults configuration file.
    """
    def populate_namespace(self, ns={}):
        """
        Take a namespace passed in (or a blank one)
        and add any extra bits to be found at this
        level to the namespace.
        """
        return ns
