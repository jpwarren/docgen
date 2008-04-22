#!/bin/sh
#
# Script to convert a project definition into the appropriate
# DocBook sources, which are then compiled into required outputs.
CREATE_DOC_BIN="/usr/local/docgen/create_document.py"
COMPILE_DOC_BIN="/usr/local/docgen/compile_doc.sh"

# Default values
STORAGE_DESIGN_SUFFIX="IPSAN-storage-design.xml"
NETWORK_DESIGN_SUFFIX="IPSAN-network-design.xml"
STORAGE_COMMANDS_SUFFIX="IPSAN-storage-commands.txt"

# Check usage
if [ $# -ne 1 ]; then
    echo "Usage: $0 <PROJECT.project-definition.xml>"
    exit 1
fi

project_defn=$1

project_name=`basename $project_defn .project-definition.xml`

# Check the project definition for validity against the DTD
xmllint --valid --noout $project_defn
if [ $? -ne 0 ]; then
    echo "Project definition file doesn't match the DTD."
    echo "It may be invalid, but check with Justin about any possible bugs."
fi

# Storage design creation
echo "Creating DocBook sources..."
basedir=`dirname $project_defn`
filename=`basename $project_defn`

echo "Creating DocBook source for storage design: $basedir/$project_name.$STORAGE_DESIGN_SUFFIX"
$CREATE_DOC_BIN -d ipsan-storage-design -o $basedir/$project_name.$STORAGE_DESIGN_SUFFIX $basedir/$filename
if [ $? -ne 0 ]; then
    echo "Failed to create storage design."
    exit 1
else
    echo "Compiling storage design..."
    $COMPILE_DOC_BIN $basedir/$project_name.$STORAGE_DESIGN_SUFFIX
fi

echo "Creating DocBook source for network design: $basedir/$project_name.$NETWORK_DESIGN_SUFFIX"
$CREATE_DOC_BIN -d ipsan-network-design -o $basedir/$project_name.$NETWORK_DESIGN_SUFFIX $basedir/$filename
if [ $? -ne 0 ]; then
    echo "Failed to create network design."
    exit 1
else
    echo "Compiling network design..."
    $COMPILE_DOC_BIN $basedir/$project_name.$NETWORK_DESIGN_SUFFIX
fi

echo "Creating storage provisioning commands file: $basedir/$project_name.$STORAGE_COMMANDS_SUFFIX"
$CREATE_DOC_BIN -d ipsan-storage-commands -o $basedir/$project_name.$STORAGE_COMMANDS_SUFFIX $basedir/$filename
