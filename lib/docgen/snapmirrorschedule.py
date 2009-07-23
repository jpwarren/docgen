## $Id: config.py 189 2009-01-14 23:42:53Z daedalus $

"""
SnapMirrorSchedule object
"""
from docgen.base import DynamicNamedXMLConfigurable

import debug
import logging
log = logging.getLogger('docgen')

class SnapMirrorSchedule(DynamicNamedXMLConfigurable):
    """
    A definition of a snapmirror schedule
    """
    xmltag = 'snapmirrorschedule'

    mandatory_attribs = [
        'minute',
        'hour',
        'dayofmonth',
        'dayofweek',
        ]

def create_snapmirrorschedule_from_node(node, defaults, parent):

    obj = SnapMirrorSchedule()
    obj.configure_from_node(node, defaults, parent)
    return obj
