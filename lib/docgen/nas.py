## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Network Attached Storage objects.
FIXME: Might not really be necessary.
"""

class NAS:

    def __init__(self, vlan, protocols=['NFS',]):

        self.vlan = vlan
        self.protocols = protocols
        self.filers = {}
