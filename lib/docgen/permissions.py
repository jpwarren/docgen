## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Role Based Access Control and storage exports related design objects
"""

class Export:
    """
    An encapsulation of a storage export to a specific host/IP
    """
    def __init__(self, tohost, fromip, type='rw', toip=None):
        """
        An export to a given host, from a particular address
        """
        self.type = type
        self.tohost = tohost
        self.fromip = fromip
        self.toip = toip

    def __eq__(self, export):
        if export.type == self.type and export.tohost == self.tohost and \
           export.fromip == self.fromip and export.toip == self.toip:
            return True
        
        return False

    def __ne__(self, export):
        if self == export:
            return False
        
        return True

