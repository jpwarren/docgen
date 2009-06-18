#!/usr/bin/python
# $Id$
#
##COPYRIGHT##

__version__ = '$Revision$'

#from ez_setup import use_setuptools
#use_setuptools()

import sys
import time
import os
import os.path
import re
import glob
import fileinput
import string

from stat import ST_MODE
from distutils.core import setup
from setuptools import setup, find_packages

from distutils.core import Extension
from distutils.command.build_scripts import build_scripts
from distutils.command.build_py import build_py
from distutils.command.install_lib import install_lib
from distutils.dist import Distribution
from distutils import sysconfig, log
from distutils.dep_util import newer
from distutils.util import convert_path
from distutils.cmd import Command

packages = ['docgen']

## Release version

version_major=1
version_minor=1
version_micro=2
version_devel='%s' % __version__.split(':')[1].split()[0]
#version_devel='-dev-' + time.strftime('%Y-%m-%d-%H%M')

#version='%d.%d.%d' % (version_major, version_minor, version_micro)
version='%d.%d.%dr%s' % (version_major, version_minor, version_micro, version_devel)

try:
    username = os.getlogin()
except OSError:
    # Not running interactively, so this is an automated build
    username = 'buildbot'

TAGDICT = {
    '_application_version': version,
    '_application_build_date': time.ctime(),
    '_application_system': ' '.join(os.uname()),
    '_application_build_user': username,
    }

first_line_re = re.compile('^#!.*python[0-9.]*([ \t].*)?$')

def replace_tags(filenames, tagdict={}, dry_run=False):
    """
    Update known tags in a list of files by modifying
    them in place.
    Always updates the ##COPYRIGHT## tag with the
    contents of the COPYRIGHT file.
    @param tagdict: a dictionary of tags to search for
    and the value that the tag should be replaced with.

    Only one tag should be used per line as this function
    is quite stupid and looks for a line starting with the
    tag, ignoring the rest of the line and replacing the
    whole line with tag = tag_value.
    """
    copyright_file = 'COPYRIGHT'
    copydata = open(copyright_file).read()

    for line in fileinput.input(filenames, inplace=True):
        matched = False

        # replace python #! line
        if fileinput.isfirstline():
            match = first_line_re.match(line)
            if match:
                matched = True
                post_interp = match.group(1) or ''
                if not dry_run:
                    sys.stdout.write("#!%s%s\n" % (os.path.join(
                        sysconfig.get_config_var("BINDIR"),
                        "python" + sysconfig.get_config_var("EXE")),
                                                   post_interp))
                    pass
                pass
            else:
                if not dry_run:
                    sys.stdout.write(line)
                    pass
                continue
            pass
        
        
        if line.startswith('##COPYRIGHT##'):
            if not dry_run:
                sys.stdout.write(copydata)
            matched = True
            continue

        for tag in tagdict:
            if line.startswith(tag):
                if not dry_run:
                    sys.stdout.write("%s = '%s'\n" % (tag, tagdict[tag]))
                matched = True
                break

        # this only happens if nothing matches
        if not matched:
            if not dry_run:
                sys.stdout.write(line)

def copy_std_file(self, infile, outfile, preserve_mode=1, preserve_times=1, link=None, level=1, tagdict={}):
    """
    Override of basic copy file method in distutil.cmd to
    perform tag replacements for most files.
    """
    Command.copy_file(self, infile, outfile, preserve_mode, preserve_times, link, level)
    # Now update the outfile with tags
    tagdict['_application_name'] = os.path.basename(infile)

    for key in TAGDICT:
        if key not in tagdict.keys():
            tagdict[key] = TAGDICT[key]

    replace_tags(outfile, tagdict, self.dry_run)

def copy_script_file(self, infile, outfile, preserve_mode=1, preserve_times=1, link=None, level=1, tagdict={}):
    """
    Override of basic copy file method in distutil.cmd to
    perform tag replacements for script files.
    """
    Command.copy_file(self, infile, outfile, preserve_mode, preserve_times, link, level)
    self.set_undefined_options('install', ('install_base', 'install_base') )

    # Now update the outfile with tags
    tagdict['_application_prefix'] = self.install_base
    tagdict['_application_name'] = os.path.basename(infile)
    
    for key in TAGDICT:
        if key not in tagdict.keys():
            tagdict[key] = TAGDICT[key]

    replace_tags(outfile, tagdict, self.dry_run)

## replace the python with an explicit version of python and
## add the tagdict of buildtime variables.

class BuildScripts(build_scripts):
    
    copy_file = copy_script_file

    def run(self):
        if not self.scripts:
            return

        self.install_base = None
        self.copy_scripts()

    def copy_scripts(self):
        """
        Override the default distutils copy_scripts to
        call replace_tags if it's marked as a Python
        script.
        """
        self.mkpath(self.build_dir)
        outfiles = []
        for script in self.scripts:
            adjust = 0
            script = convert_path(script)
            outfile = os.path.join(self.build_dir, os.path.basename(script))
            outfiles.append(outfile)

            if not self.force and not newer(script, outfile):
                log.debug("not copying %s (up-to-date)", script)
                continue

            self.copy_file(script, outfile, self.dry_run)

        if os.name == 'posix':
            for file in outfiles:
                if self.dry_run:
                    log.info("changing mode of %s", file)
                else:
                    oldmode = os.stat(file)[ST_MODE] & 07777
                    newmode = (oldmode | 0555) & 07777
                    if newmode != oldmode:
                        log.info("changing mode of %s from %o to %o",
                                 file, oldmode, newmode)
                        os.chmod(file, newmode)
                        
class BuildPy(build_py):
    """
    A custom build_by that will update tags when building.
    """
    copy_file = copy_std_file

class InstallLib(install_lib):
    """
    A custom lib installer that doesn't install the .py files, only .pyc or .pyo files
    """
    def run (self):

        # Make sure we have built everything we need first
        self.build()

        # Install everything: simply dump the entire contents of the build
        # directory to the installation directory (that's the beauty of
        # having a build directory!)
        outfiles = self.install()

        # (Optionally) compile .py to .pyc
        if outfiles is not None and self.distribution.has_pure_modules():
            self.byte_compile(outfiles)

        # Remove source library files
        for filepath in outfiles:
            os.unlink(filepath)

def install_docgen():
    """
    A custom function that installs DocGen resources into the docgen tree
    """
    print "=== This is a custom install function, inserted via an entry point."
    
class myDistribution(Distribution):
    def __init__(self, *attrs):
        Distribution.__init__(self, *attrs)
        self.cmdclass['build_scripts'] = BuildScripts
        self.cmdclass['build_py'] = BuildPy
        self.cmdclass['install_lib'] = InstallLib
        return
    pass

setup(
    name="DocGen",
    version=version,

    #packages = find_packages('lib'),
    packages = packages,
    package_dir = {'':'lib'},

    scripts = [ 'bin/build_project_docs.sh',
                'bin/compile_doc.sh',
                'bin/create_document.py',
                ],
      
    data_files = [ ('etc', glob.glob('etc/*')),
                   ('docbook', glob.glob('docbook/*')),
                   ('doc', [ 'doc/EXAMPLE.project-definition.xml',
                             'doc/EXAMPLE.multi-network-vlan.project-definition.xml',
                             'doc/EXAMPLE.vmfarm.project-definition.xml',
                             'doc/EXAMPLE.vmfarm-includes.xml',
                             ]),
                   # Make sure the binary builds contain licensing, copyright, etc. information
                   ('', [ 'LICENSE',
                          'COPYRIGHT',
                          'README',
                          'INSTALL',
                          ]),
                   ],

    #eager_resources = [ 'etc', 'docbook', 'doc' ],
      
    distclass = myDistribution,

    author="Justin Warren",
    author_email="daedalus@eigenmagic.com",
    description="DocGen document generation system",
    long_description="""DocGen automates the creation of standardised IT documentation.""",
    license='Proprietary',
    keywords = "document generator",
    url='http://docgen.eigenmagic.com',

    classifiers = [
    "Development Status :: 5 - Stable",
    "Environment :: Console",
    "Intended Audience :: System Administrators",
    "Intended Audience :: Developers",
    "Intended Audience :: Information Technology",
    "License :: Proprietary :: eigenmagic End User License",
    "Natural Language :: English",
    "Operating System :: POSIX",
    "Programming Language :: Python",
    "Topic :: System :: Systems Administration",
    "Topic :: Utilities",
    ],

##     entry_points = { "distutils.commands":
##                      [ "docgen_install = docgen.setup:docgen_install",
##                        ],
    
##     }
    
    )
