## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
Snapshot related design objects
"""

class Snapshot:
    """
    A Snapshot is a local snapshot backup.
    SnapVaults and SnapMirrors are different objects, defined below.
    """
    def __init__(self, sourcevol, numweekly, numdaily, hourly_schedule):
        self.sourcevol = sourcevol
        self.numweekly = numweekly
        self.numdaily = numdaily
        self.hourly_schedule = hourly_schedule

        self.sourcevol.snaps.append(self)

    def __str__(self):
        return '<Snapshot: %s -> %s, %s, %s>' % (self.sourcevol.namepath(),
                                                  self.targetvol.namepath(),
                                                  self.basename,
                                                  self.schedule,
                                                  )

class SnapVault:
    """
    A SnapVault is a special kind of snapshot that requires a baseline
    to be taken on the source volume, which is then transferred to a
    SnapVault secondary device at some later time.

    A variant of the SnapVault is a destination only SnapVault snapshot,
    which assumes there is another SnapVault defined that will cause
    data to be transferred from a primary device. This destination only
    SnapVault is the mechanism recommended in the NetApp Best Practices Guide
    for doing weekly snapshots when you transfer data daily.
    """

    def __init__(self, sourcevol, targetvol, basename, src_schedule=None, dst_schedule=None):

        self.sourcevol = sourcevol
        self.targetvol = targetvol
        self.basename = basename
        self.src_schedule = src_schedule
        self.dst_schedule = dst_schedule

        self.sourcevol.snapvaults.append(self)
        self.targetvol.snapvaults.append(self)

    def __str__(self):
        return '<SnapVault: %s -> %s, %s, %s, %s>' % (self.sourcevol.namepath(),
                                                      self.targetvol.namepath(),
                                                      self.basename,
                                                      self.src_schedule,
                                                      self.dst_schedule,
                                                      )

class SnapMirror:

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

