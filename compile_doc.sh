#!/bin/sh
#
# Script to compile a docbook source document into outputs, mainly PDF.
#

# Directory that docgen is installed in
DOCGEN_BASEDIR=/usr/local/docgen

DEFAULT_STYLESHEET=$DOCGEN_BASEDIR/book_fo_styles.xsl

LD_LIBRARY_PATH=/usr/local/lib:/usr/lib
export LD_LIBRARY_PATH

FOP="/usr/local/bin/fop"

XML_CATALOG_FILES="/usr/share/xml/docbook/stylesheet/nwalsh/catalog.xml"

if [ $# -lt 1 ]; then
    echo "Usage: $0 <input_file.xml> [ <stylesheet> [ <outfile> ] ]"
    exit 1
fi

infile=$1
dirbase=`dirname $infile`
filebase=`basename $infile .xml`
fofile="$dirbase/$filebase.fo"

if [ "$2" != "" ]; then
    stylesheet=$2
else
    stylesheet=$DEFAULT_STYLESHEET
fi

if [ "$3" != "" ]; then
    outfile=$3
else
    outfile="$dirbase/$filebase.pdf"
fi

if [ "$4" != "rtf" ]; then
    outfile="$dirbase/$filebase.rtf"
    options="-rtf"
fi

# Build the titlepage xsl from the spec file
#xsltproc --nonet --novalid --output titlepage.xsl /usr/share/xml/docbook/stylesheet/nwalsh/template/titlepage.xsl titlepage.templates.xml
#if [ $? -ne 0 ]; then
#	echo "Failed to generate custom titlepages."
#	exit 1
#fi

echo "Compiling $infile to $fofile with $stylesheet..."

xsltproc --nonet --output $fofile $stylesheet $infile
if [ $? -ne 0 ]; then
	echo "Failed to XSL process xml to .fo"
	exit 1
fi

# pretty print output document
mv $fofile ${fofile}.tmp
xmllint --format ${fofile}.tmp > $fofile

OUTPUT_FORMATS="pdf rtf"
#OUTPUT_FORMATS="pdf"
for format in $OUTPUT_FORMATS; do
    outfile="$dirbase/$filebase.$format"
    echo "Converting $fofile to $outfile..."
    echo "$FOP $fofile -$format $outfile"
    errors=`$FOP $fofile -$format $outfile 2>&1`
    if [ $? -ne 0 ]; then
	echo "Error processing with fop: $errors"
    fi
done

