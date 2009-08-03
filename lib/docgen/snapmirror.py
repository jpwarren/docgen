## $Id$

"""
SnapMirror related object definitions
"""
import debug
import logging
log = logging.getLogger('docgen')

class SnapMirror:
    """
    An abstract representation of a SnapMirror relationship.
    Volume snapmirror only.
    """
    type = 'volume'
    
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
        """
        return self.arguments
