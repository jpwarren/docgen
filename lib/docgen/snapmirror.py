## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
SnapMirror related object definitions
"""
from docgen.base import XMLConfigurable, DynamicNaming
from docgen.snapvaultset import SnapVaultSet

import debug
import logging
log = logging.getLogger('docgen')

class SnapMirrorRelationship(XMLConfigurable, DynamicNaming):
    """
    A definition of a snapmirror relationship
    """
    xmltag = 'snapmirror'

    mandatory_attribs = [
        ]
    
    def configure_from_node(self, node, defaults, parent):
        self.configure_mandatory_attributes(node, defaults)
        self.configure_optional_attributes(node, defaults)

class SnapMirror:
    """
    An actual snapmirror object used by the system.
    """
    def __init__(self, sourcevol, targetvol, minute='*', hour='*', dayofmonth='*', dayofweek='*', arguments='-'):

        self.sourcevol = sourcevol
        self.targetvol = targetvol
        self.minute = minute
        self.hour = hour
        self.dayofmonth = dayofmonth
        self.dayofweek = dayofweek

        self.arguments = arguments

        self.sourcevol.snapmirrors.append(self)
        self.targetvol.snapmirrors.append(self)

    def __str__(self):
        return '<SnapMirror: %s -> %s, %s>' % (self.sourcevol.namepath(),
                                                  self.targetvol.namepath(),
                                                  self.etc_snapmirror_conf_schedule(),
                                                  )
    def etc_snapmirror_conf_schedule(self):
        """
        Returns a string of the schedule part of the /etc/snapmirror.conf
        entry for this SnapMirror.
        """
        return '%s %s %s %s' % (self.minute, self.hour, self.dayofmonth, self.dayofweek)

    def etc_snapmirror_conf_arguments(self):
        """
        Returns the arguments for the snapmirror in the format expected for
        /etc/snapmirror.conf.
        Currently this only supports the default of '-'.
        """
        return self.arguments

def create_snapmirror_from_node(node, defaults, parent):

    sm = SnapMirrorRelationship()
    sm.configure_from_node(node, defaults, parent)
    return sm
