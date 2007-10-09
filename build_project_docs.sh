#!/bin/sh
#
# Script to convert a project definition into the appropriate
# DocBook sources, which are then compiled into required outputs.

# Default values
EBR_STYLESHEET="ebr_design_styles.xsl"
EBR_CIP_STYLESHEET="ebr_cip_styles.xsl"
NAS_STYLESHEET="nas_design_styles.xsl"
NAS_CIP_STYLESHEET="nas_cip_styles.xsl"

# Check usage

if [ $# -ne 2 ]; then
    echo "Usage: $0 <project_name> <definition_file.xml>"
    exit 1
fi

project_name=$1
project_defn=$2

# Check the project definition for validity against the DTD
xmllint --valid --noout $project_defn
if [ $? -ne 0 ]; then
    echo "Definition file invalid. Please fix the above errors and retry."
    exit 1
fi

# EBR document conversion
echo "Creating DocBook sources..."
basedir=`dirname $project_defn`
filename=`basename $project_defn`

echo "Creating DocBook source for EBR design..."
xsltproc -o $basedir/$project_name.ebr-design.xml project-ebr-design-conversion.xsl $basedir/$filename

echo "Building EBR design..."
./compile_doc.sh $basedir/$project_name.ebr-design.xml ./$EBR_STYLESHEET

echo "Creating DocBook source for EBR CIP..."
xsltproc -o $basedir/$project_name.ebr-cip.xml project-ebr-cip-conversion.xsl $basedir/$filename

echo "Building EBR CIP..."
./compile_doc.sh $basedir/$project_name.ebr-cip.xml ./$EBR_CIP_STYLESHEET

#echo "Creating DocBook source for NAS design..."
#xsltproc -o $basedir/$project_name.nas-design.xml project-nas-design-conversion.xsl $basedir/$filename

#echo "Building NAS design..."
#./compile_doc.sh $basedir/$project_name.nas-design.xml ./$NAS_STYLESHEET

#echo "Creating DocBook source for NAS CIP..."
#xsltproc -o $basedir/$project_name.nas-cip.xml project-nas-cip-conversion.xsl $basedir/$filename

#echo "Building NAS CIP..."
#./compile_doc.sh $basedir/$project_name.nas-cip.xml ./$NAS_CIP_STYLESHEET
