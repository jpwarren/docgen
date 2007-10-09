<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet  
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:fo="http://www.w3.org/1999/XSL/Format"
    version="1.0">

<!-- Use graphics for the admonitions -->
<xsl:param name="admon.graphics" select="1"/>
<xsl:param name="admon.textlabel" select="0"/>

<xsl:param name="admon.graphics.path">/usr/share/xml/docbook/stylesheet/nwalsh/images/</xsl:param>
<!--
<xsl:param name="admon.graphics.extension">.svg</xsl:param>
-->

</xsl:stylesheet>