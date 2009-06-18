#
# Activation advice generation
#

import zope.interface
import csv
import datetime
import sys

import logging

from docgen import IDocumentGenerator

import debug
log = logging.getLogger('docgen')

class IPSANActivationAdvice:

    zope.interface.implements(IDocumentGenerator)

    def __init__(self, conf):
        self.conf = conf
        pass

    def emit(self, outfile=None, ns={}):
        """
        Write an activation advice .csv file
        """

        # What information do we want to provide?
        header = [
            'Date',
            'Filer',
            'Usable Storage Allocated (GiB)',
            'Actual Storage Allocated (GiB)',
            ]

        rows = []
        # first row of output is the header
        rows.append( header )

        # figure out the totals for each filer
        usable_total = 0
        raw_total = 0

        # Skip secondary filers, because they never have storage allocated for a project.
        for filer in [ f for f in self.conf.filers.values() if f.type != 'secondary' ]:
            usable_total = sum( [ vol.usable for vol in filer.volumes ] )
            raw_total = sum( [ vol.raw for vol in filer.volumes ] )
            log.debug("Filer %s usable storage: %s", filer.name, usable_total)

            rows.append( (datetime.datetime.now().strftime('%Y-%m-%d'), filer.name, usable_total, raw_total ) )
            pass

        writer = csv.writer(open(outfile, "w"), dialect=csv.excel)
        writer.writerows( rows )
            
