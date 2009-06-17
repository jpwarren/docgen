## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Network switching devices
"""

class Switch:

    def __init__(self, name, type, sitename, location, connected_switches=[]):

        self.name = name
        if type not in ['core', 'edge']:
            raise ValueError("Switch '%s' has unknown type '%s'" % (name, type))
        self.type = type
        self.site = None # site is 'primary' or 'secondary'
        self.sitename = sitename
        self.location = location

        self.connected_switches = connected_switches
