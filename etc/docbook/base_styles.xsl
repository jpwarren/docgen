<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet  
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:fo="http://www.w3.org/1999/XSL/Format"
    version="1.0">

<!--
<xsl:import href="file:///usr/share/xml/docbook/stylesheet/nwalsh/fo/docbook.xsl"/>
-->
<!-- This will be remapped by the catalog to the main stylesheet -->
<xsl:import href="http://docbook.sourceforge.net/release/xsl/current/fo/docbook.xsl"/>

<xsl:param name="paper.type">A4</xsl:param>

<xsl:param name="double.sided">0</xsl:param>

<xsl:param name="section.autolabel" select="1"/>
<xsl:param name="chapter.autolabel" select="1"/>
<xsl:param name="section.label.includes.component.label" select="1"/>

<xsl:param name="hyphenate">false</xsl:param>

<!-- Use the catalog to find the bibliography database -->

<xsl:param name="bibliography.collection" select="'file:///biblio/biblio.xml'"/>
<xsl:param name="biblioentry.item.separator">, </xsl:param>
<xsl:param name="bibliography.numbered" select="1" />

<!-- Default to left justified text -->
<xsl:variable name="alignment" select="'left'"/>

<!-- Define which tables of contents style items we generate -->
<xsl:param name="generate.toc">
/appendix toc,title
article/appendix  nop
/article  toc,title
book      toc,title
/chapter  toc,title
part      toc,title
/preface  toc,title
qandadiv  toc
qandaset  toc
reference toc,title
/sect1    toc
/sect2    toc
/sect3    toc
/sect4    toc
/sect5    toc
/section  toc
set       toc,title
</xsl:param>

<!-- only include the chapter and the first section deep in table of contents -->
<xsl:param name="toc.section.depth" select="'1'"/>

<!-- How deep into the section tree to go when choosing the running header titleabbrev -->
<xsl:param name="marker.section.level" select="'1'"/>

<!-- Exclude appendix sub-sections from the toc -->
<xsl:template match="appendix/section" mode="toc"/>

</xsl:stylesheet>

