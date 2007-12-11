<?xml version="1.0" encoding="iso-8859-1"?>
<xsl:stylesheet  
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform" 
    xmlns:fo="http://www.w3.org/1999/XSL/Format"
    version="1.0">

<xsl:import href="http://docbook.sensis.com.au/sensis-docgen/base_styles.xsl"/>
<xsl:import href="http://docbook.sensis.com.au/sensis-docgen/admon_graphics.xsl" />
<xsl:import href="http://docbook.sensis.com.au/sensis-docgen/titlepage.xsl"/>

<xsl:param name="corp.logo.top.right" select="'/usr/local/docgen/sensis-logo-doco.png'"/>

<xsl:param name="sensis.color.sand">#f2e8bb</xsl:param>
<xsl:param name="sensis.color.aqua">#26bcd6</xsl:param>
<xsl:param name="sensis.color.sensis.blue.40">#95b8e1</xsl:param>
<!--
    Sensis colours:
    Sensis Blue: #0055c3 RGB: 0,85,195
    Sensis Blue 40%: #95b8e1 RGB: 149,184,225
    Sand: #f2e8bb RGB: 242,232,187
    Aqua: #26bcd6 RGB: 38,188,214
    Turquoise: #2dafa4 RGB: 45,175,164
-->


<!-- Enable PDF bookmarks to be generated -->
<xsl:param name="fop1.extensions">1</xsl:param>

<xsl:param name="xep.extensions">1</xsl:param>

<!-- Don't use draft mode. May need to replace this with a runtime
     parameter to xsltproc if we want to use draft/publish workflow.
-->
<xsl:param name="draft.mode">no</xsl:param>

<xsl:param name="page.margin.inner">2cm</xsl:param>
<xsl:param name="page.margin.outer">2cm</xsl:param>
<xsl:param name="body.start.indent">2pc</xsl:param>


<!-- Make all URL links coloured blue for FO output (eg: PDFs) -->
<xsl:attribute-set name="xref.properties">
  <xsl:attribute name="color">
    <xsl:choose>
      <xsl:when test="self::ulink">blue</xsl:when>
      <xsl:otherwise>inherit</xsl:otherwise>
    </xsl:choose>
  </xsl:attribute>
</xsl:attribute-set>

<!-- Turn off the Chapter prefix for numbered chapter titles -->
<xsl:param name="local.l10n.xml" select="document('')"/>
<l:i18n xmlns:l="http://docbook.sourceforge.net/xmlns/l10n/1.0">
  <l:l10n language="en">
    <l:context name="title-numbered">
      <l:template name="chapter" text="%n.&#160;%t"/>
    </l:context>    
  </l:l10n>
</l:i18n>

<!-- Wrap long lines in program listings -->
<xsl:attribute-set name="monospace.verbatim.properties">
  <xsl:attribute name="wrap-option">wrap</xsl:attribute>
</xsl:attribute-set>

<!-- Make program listing background color yellow -->
<xsl:param name="shade.verbatim">1</xsl:param>
<xsl:attribute-set name="shade.verbatim.style">
  <xsl:attribute name="border">0.5pt solid gray</xsl:attribute>
  <xsl:attribute name="background-color"><xsl:value-of select="$sensis.color.sand"/></xsl:attribute>
  <xsl:attribute name="padding-left">0.5em</xsl:attribute>
  <xsl:attribute name="padding-right">0.5em</xsl:attribute>
  <xsl:attribute name="font-weight">normal</xsl:attribute>
  <xsl:attribute name="font-size">
    <xsl:choose>
      <xsl:when test="processing-instruction('db-font-size')">
	<xsl:value-of select="processing-instruction('db-font-size')"/>
      </xsl:when>
      <xsl:otherwise>75%</xsl:otherwise>
    </xsl:choose>
  </xsl:attribute>
</xsl:attribute-set>

<!-- Work around a bug in fop that causes an extra blank
     page to be generated after the title pages.
-->
<xsl:template name="book.titlepage.separator"/>

<!-- Allow long tables to span pages -->
<xsl:attribute-set name="table.properties">
  <xsl:attribute name="keep-together.within-column">auto</xsl:attribute>
</xsl:attribute-set>

<!-- Custom table style -->
<xsl:template name="table.cell.properties"> 
  <xsl:param name="bgcolor.pi" select="''"/>
  <xsl:param name="rowsep.inherit" select="1"/>
  <xsl:param name="colsep.inherit" select="1"/>
  <xsl:param name="col" select="1"/>
  <xsl:param name="valign.inherit" select="''"/>
  <xsl:param name="align.inherit" select="''"/>
  <xsl:param name="char.inherit" select="''"/>

<!--
  <xsl:message>Column number is: <xsl:value-of select="$col"/>
  </xsl:message>
-->

  <xsl:variable name="tabstyle" select="ancestor::table[1]/@tabstyle
                          | ancestor::informaltable[1]/@tabstyle"/>

  <xsl:variable name="bgcolor">
    <xsl:choose>

      <!-- Make header background coloured for table style 'techtable-01' -->
      <xsl:when test="$tabstyle = 'techtable-01'
                     and ancestor::thead">
        <xsl:value-of select="$sensis.color.sensis.blue.40"/>
      </xsl:when>

      <!-- Make header background coloured for table style 'techtable-02' -->
      <xsl:when test="$tabstyle = 'techtable-02'
                     and ancestor::thead">
        <xsl:value-of select="$sensis.color.sensis.blue.40"/>
      </xsl:when>

      <!-- Make header background coloured for table style 'techtable-03' -->
      <xsl:when test="$tabstyle = 'techtable-03'
                     and ancestor::thead">
        <xsl:value-of select="$sensis.color.sensis.blue.40"/>
      </xsl:when>

      <!-- Make left column background yellow for table style 'techtable-03' -->
      <xsl:when test="$tabstyle = 'techtable-03'
                     and $col = 1">
        <xsl:value-of select="$sensis.color.sensis.blue.40"/>
      </xsl:when>

      <xsl:when test="$bgcolor.pi != ''">
        <xsl:value-of select="$bgcolor.pi"/>
      </xsl:when>
    </xsl:choose>
  </xsl:variable>

  <xsl:if test="$bgcolor != ''">
    <xsl:attribute name="background-color">
      <xsl:value-of select="$bgcolor"/>
    </xsl:attribute>
  </xsl:if>

  <!-- make left column text bold for techtable-03 -->
  <xsl:if test="$tabstyle = 'techtable-03'
		and $col = 1">
    <xsl:attribute name="font-weight">bold</xsl:attribute>
  </xsl:if>
	  

<!-- style pieces from the original template -->

        <xsl:if test="$rowsep.inherit &gt; 0">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'bottom'"/>
          </xsl:call-template>
        </xsl:if>

        <xsl:if test="$colsep.inherit &gt; 0 and
                      $col &lt; ancestor::tgroup/@cols">
          <xsl:call-template name="border">
            <xsl:with-param name="side" select="'right'"/>
          </xsl:call-template>
        </xsl:if>

        <xsl:if test="$valign.inherit != ''">
          <xsl:attribute name="display-align">
            <xsl:choose>
              <xsl:when test="$valign.inherit='top'">before</xsl:when>
              <xsl:when test="$valign.inherit='middle'">center</xsl:when>
              <xsl:when test="$valign.inherit='bottom'">after</xsl:when>
              <xsl:otherwise>
                <xsl:message>
                  <xsl:text>Unexpected valign value: </xsl:text>
                  <xsl:value-of select="$valign.inherit"/>
                  <xsl:text>, center used.</xsl:text>
                </xsl:message>
                <xsl:text>center</xsl:text>
              </xsl:otherwise>
            </xsl:choose>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$align.inherit != ''">
          <xsl:attribute name="text-align">
            <xsl:value-of select="$align.inherit"/>
          </xsl:attribute>
        </xsl:if>

        <xsl:if test="$char.inherit != ''">
          <xsl:attribute name="text-align">
            <xsl:value-of select="$char.inherit"/>
          </xsl:attribute>
        </xsl:if>

</xsl:template>

<!-- make headers and footers for tables bold -->
<xsl:template name="table.cell.block.properties">
  <xsl:if test="ancestor::thead">
    <xsl:attribute name="font-weight">bold</xsl:attribute>
  </xsl:if>
  <xsl:if test="ancestor::tfoot">
    <xsl:attribute name="font-weight">bold</xsl:attribute>
  </xsl:if>

</xsl:template>

<!-- row colouring based on row position and table style -->
<xsl:template match="row">
  <xsl:param name="spans"/>

  <xsl:variable name="tabstyle" select="ancestor::table[1]/@tabstyle
                          | ancestor::informaltable[1]/@tabstyle"/>

  <xsl:variable name="bgcolor">
    <xsl:variable name="rownum" select="count(preceding-sibling::*)"/>
    <xsl:choose>
      <!-- colour even rows in table style techtable-01 -->
      <xsl:when test="$tabstyle = 'techtable-01' and $rownum mod 2">
        <xsl:value-of select="$sensis.color.sand"/>
      </xsl:when>

      <!-- colour every even group of 3 rows in techtable-02 -->
      <xsl:when test="$tabstyle = 'techtable-02' and ($rownum mod 6 >= 3)">
        <xsl:value-of select="$sensis.color.sand"/>
      </xsl:when>

      <!-- otherwise, do the usual template thing -->
      <xsl:otherwise>
	<xsl:call-template name="dbfo-attribute">
	  <xsl:with-param name="pis" select="processing-instruction('dbfo')"/>
	  <xsl:with-param name="attribute" select="'bgcolor'"/>
	</xsl:call-template>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <fo:table-row>
    <xsl:call-template name="anchor"/>
    <xsl:if test="$bgcolor != ''">
      <xsl:attribute name="background-color">
        <xsl:value-of select="$bgcolor"/>
      </xsl:attribute>
    </xsl:if>

    <xsl:apply-templates select="(entry|entrytbl)[1]">
      <xsl:with-param name="spans" select="$spans"/>
    </xsl:apply-templates>
  </fo:table-row>

  <xsl:if test="following-sibling::row">
    <xsl:variable name="nextspans">
      <xsl:apply-templates select="(entry|entrytbl)[1]" mode="span">
        <xsl:with-param name="spans" select="$spans"/>
      </xsl:apply-templates>
    </xsl:variable>

    <xsl:apply-templates select="following-sibling::row[1]">
      <xsl:with-param name="spans" select="$nextspans"/>
    </xsl:apply-templates>
  </xsl:if>
</xsl:template>

<!--
 Custom titlepage layout using fo:table
-->
<xsl:template name="book.titlepage.recto">
  <fo:block>
    <fo:table inline-progression-dimension="100%" table-layout="fixed">
      <fo:table-column column-number="1" column-width="100%"/>
      <fo:table-body>

        <fo:table-row >

          <fo:table-cell column-number="1">
            <fo:block text-align="right"
		      padding-top="4pc">
	      <xsl:if test="$corp.logo.top.right">
	      <fo:external-graphic width="auto" height="auto">
		<xsl:attribute name="src">
		  <xsl:text>url(</xsl:text>
		  <xsl:value-of select="$corp.logo.top.right" />
		  <xsl:text>)</xsl:text>
		</xsl:attribute>
	      </fo:external-graphic>
	      </xsl:if>
	    </fo:block>
	  </fo:table-cell>

	</fo:table-row>

        <fo:table-row >
          <fo:table-cell column-number="1">
            <fo:block text-align="right"
		      padding-top="6pc">
              <xsl:choose>
                <xsl:when test="bookinfo/title">
                  <xsl:apply-templates 
                         mode="book.titlepage.recto.auto.mode" 
                         select="bookinfo/title"/>
                </xsl:when>
                <xsl:when test="title">
                  <xsl:apply-templates 
                         mode="book.titlepage.recto.auto.mode" 
                         select="title"/>
                </xsl:when>
              </xsl:choose>
            </fo:block>
          </fo:table-cell>
        </fo:table-row>

        <fo:table-row>
          <fo:table-cell column-number="1">
            <fo:block text-align="right"
		      padding-top="0.25pc">
	      
	      <xsl:choose>
                <xsl:when test="bookinfo/subtitle">
                  <xsl:apply-templates 
                         mode="book.titlepage.recto.auto.mode" 
                         select="bookinfo/subtitle"/>
                </xsl:when>
                <xsl:when test="subtitle">
                  <xsl:apply-templates 
                         mode="book.titlepage.recto.auto.mode" 
                         select="subtitle"/>
                </xsl:when>
	      </xsl:choose>
            </fo:block>
          </fo:table-cell>
        </fo:table-row>

<!-- Build this into a table with a single row and cell, with a border
     centered in the middle of the page, near the bottom.
 -->
        <fo:table-row>
          <fo:table-cell column-number="1">
            <fo:block text-align="center"
		      padding-top="20pc">
	      <fo:table inline-progression-dimension="100%" table-layout="fixed"
			border-left-style="solid"
			border-right-style="solid"
			border-top-style="solid"
			border-bottom-style="solid"
			border-left-width="1pt"
			border-right-width="1pt"
			border-top-width="1pt"
			border-bottom-width="1pt"
			border-left-color="black"
			border-right-color="black"
			border-top-color="black"
			border-bottom-color="black">
		<fo:table-column column-number="1" column-width="100%"/>
		<fo:table-body>
		  <fo:table-row>
		    <fo:table-cell column-number="1">
		      <fo:block text-align="center">

	      <xsl:choose>
		<xsl:when test="bookinfo/legalnotice">
		  <xsl:apply-templates 
                     mode="book.titlepage.recto.mode" 
                     select="bookinfo/legalnotice"/>
		</xsl:when>
	      </xsl:choose>

			
		      </fo:block>
		    </fo:table-cell>
		  </fo:table-row>
		</fo:table-body>
	      </fo:table>

            </fo:block>
          </fo:table-cell> 
        </fo:table-row >  

      </fo:table-body> 
    </fo:table>
  </fo:block>
</xsl:template>

<!-- verso titlepage -->
<xsl:template name="book.titlepage.verso">

  <xsl:apply-templates mode="book.titlepage.verso.mode" select="bookinfo/copyright"/>

</xsl:template>

<xsl:template match="bookinfo/copyright" mode="book.titlepage.verso.mode">
  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" xsl:use-attribute-sets="book.titlepage.verso.style" font-size="14.4pt" font-weight="bold" font-family="{$title.fontset}" space-before="0.5em" space-after="0.5em">Copyright</fo:block>

  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" text-align="center">This document is the property of Sensis Pty Ltd.</fo:block>
  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" text-align="center">222 Lonsdale St</fo:block>
  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" text-align="center">MELBOURNE</fo:block>
  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" text-align="center">Victoria 3000</fo:block>
  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" text-align="center" space-after="3cm">www.sensis.com.au</fo:block>

  <fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format" text-align="center">
    <xsl:apply-templates select="." mode="titlepage.mode"/>
  </fo:block>
</xsl:template>

<!-- Running header content -->
<xsl:param name="header.column.widths" select="'1 4 1'"/>
<xsl:param name="region.before.extent" select="'3cm'"/>
<xsl:param name="body.margin.top" select="'3cm'"/>
<xsl:param name="header.table.height" select="'2cm'"/>
<xsl:param name="header.rule">0</xsl:param>

<xsl:attribute-set name="header.content.properties">
  <xsl:attribute name="font-family"><xsl:value-of select="$title.fontset"/></xsl:attribute>
  <xsl:attribute name="font-weight">bold</xsl:attribute>
  <xsl:attribute name="font-size">12pt</xsl:attribute>
</xsl:attribute-set>

<xsl:template name="header.table">
  <xsl:param name="pageclass" select="''"/>
  <xsl:param name="sequence" select="''"/>
  <xsl:param name="gentext-key" select="''"/>

  <!-- default is a single table style for all headers -->
  <!-- Customize it for different page classes or sequence location -->

  <xsl:choose>
      <xsl:when test="$pageclass = 'index'">
          <xsl:attribute name="margin-left">0pt</xsl:attribute>
      </xsl:when>
  </xsl:choose>

  <xsl:variable name="column1">
    <xsl:choose>
      <xsl:when test="$double.sided = 0">1</xsl:when>
      <xsl:when test="$sequence = 'first' or $sequence = 'odd'">1</xsl:when>
      <xsl:otherwise>3</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="column3">
    <xsl:choose>
      <xsl:when test="$double.sided = 0">3</xsl:when>
      <xsl:when test="$sequence = 'first' or $sequence = 'odd'">3</xsl:when>
      <xsl:otherwise>1</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <xsl:variable name="candidate">
    <fo:table table-layout="fixed" width="100%"
			border-left-style="solid"
			border-right-style="solid"
			border-top-style="solid"
			border-bottom-style="solid"
			border-left-width="1pt"
			border-right-width="1pt"
			border-top-width="1pt"
			border-bottom-width="1pt"
			border-left-color="black"
			border-right-color="black"
			border-top-color="black"
			border-bottom-color="black">

      <xsl:call-template name="head.sep.rule">
        <xsl:with-param name="pageclass" select="$pageclass"/>
        <xsl:with-param name="sequence" select="$sequence"/>
        <xsl:with-param name="gentext-key" select="$gentext-key"/>
      </xsl:call-template>

      <fo:table-column column-number="1">
        <xsl:attribute name="column-width">
          <xsl:text>proportional-column-width(</xsl:text>
          <xsl:call-template name="header.footer.width">
            <xsl:with-param name="location">header</xsl:with-param>
            <xsl:with-param name="position" select="$column1"/>
          </xsl:call-template>
          <xsl:text>)</xsl:text>
        </xsl:attribute>
      </fo:table-column>
      <fo:table-column column-number="2">
        <xsl:attribute name="column-width">
          <xsl:text>proportional-column-width(</xsl:text>
          <xsl:call-template name="header.footer.width">
            <xsl:with-param name="location">header</xsl:with-param>
            <xsl:with-param name="position" select="2"/>
          </xsl:call-template>
          <xsl:text>)</xsl:text>
        </xsl:attribute>
      </fo:table-column>
      <fo:table-column column-number="3">
        <xsl:attribute name="column-width">
          <xsl:text>proportional-column-width(</xsl:text>
          <xsl:call-template name="header.footer.width">
            <xsl:with-param name="location">header</xsl:with-param>
            <xsl:with-param name="position" select="$column3"/>
          </xsl:call-template>
          <xsl:text>)</xsl:text>
        </xsl:attribute>
      </fo:table-column>

      <fo:table-body>
        <fo:table-row>
          <xsl:attribute name="block-progression-dimension.minimum">
            <xsl:value-of select="$header.table.height"/>
          </xsl:attribute>
          <fo:table-cell text-align="left"
                         display-align="center">
            <xsl:if test="$fop.extensions = 0">
              <xsl:attribute name="relative-align">baseline</xsl:attribute>
            </xsl:if>
            <fo:block>
              <xsl:call-template name="header.content">
                <xsl:with-param name="pageclass" select="$pageclass"/>
                <xsl:with-param name="sequence" select="$sequence"/>
                <xsl:with-param name="position" select="'left'"/>
                <xsl:with-param name="gentext-key" select="$gentext-key"/>
              </xsl:call-template>
            </fo:block>
          </fo:table-cell>
          <fo:table-cell text-align="center"
                         display-align="center"
			 background-color="{$sensis.color.sensis.blue.40}"
			 border-left-style="solid"
			 border-left-width="1pt"
			 border-left-color="black"
			 border-right-style="solid"
			 border-right-width="1pt"
			 border-right-color="black"
			 >
            <xsl:if test="$fop.extensions = 0">
              <xsl:attribute name="relative-align">baseline</xsl:attribute>
            </xsl:if>
            <fo:block>
              <xsl:call-template name="header.content">
                <xsl:with-param name="pageclass" select="$pageclass"/>
                <xsl:with-param name="sequence" select="$sequence"/>
                <xsl:with-param name="position" select="'center'"/>
                <xsl:with-param name="gentext-key" select="$gentext-key"/>
              </xsl:call-template>
            </fo:block>
          </fo:table-cell>
          <fo:table-cell text-align="right"
                         display-align="center">
            <xsl:if test="$fop.extensions = 0">
              <xsl:attribute name="relative-align">baseline</xsl:attribute>
            </xsl:if>
            <fo:block>
              <xsl:call-template name="header.content">
                <xsl:with-param name="pageclass" select="$pageclass"/>
                <xsl:with-param name="sequence" select="$sequence"/>
                <xsl:with-param name="position" select="'right'"/>
                <xsl:with-param name="gentext-key" select="$gentext-key"/>
              </xsl:call-template>
            </fo:block>
          </fo:table-cell>
        </fo:table-row>
      </fo:table-body>
    </fo:table>
  </xsl:variable>

  <!-- Really output a header? -->
  <xsl:choose>

    <xsl:when test="$pageclass = 'titlepage' and $gentext-key = 'book'">
      <!-- No header on any book titlepage, both first and second -->
    </xsl:when>

    <xsl:when test="$sequence = 'blank' and $headers.on.blank.pages = 0">
      <!-- no output on blank pages -->
    </xsl:when>
    <xsl:otherwise>
      <xsl:copy-of select="$candidate"/>
    </xsl:otherwise>
  </xsl:choose>
</xsl:template>

<xsl:template name="header.content">  
  <xsl:param name="pageclass" select="''"/>
  <xsl:param name="sequence" select="''"/>
  <xsl:param name="position" select="''"/>
  <xsl:param name="gentext-key" select="''"/>

  <xsl:variable name="candidate">
    <!-- sequence can be odd, even, first, blank -->
    <!-- position can be left, center, right -->
    <xsl:choose>

      <xsl:when test="$position = 'left' or $position = 'right'">
	<xsl:if test="$corp.logo.top.right">
	  <fo:block text-align="center">
	    <fo:external-graphic width="auto" height="auto">
	      <xsl:attribute name="src">
		<xsl:text>url(</xsl:text>
		<xsl:value-of select="$corp.logo.top.right" />
		<xsl:text>)</xsl:text>
	      </xsl:attribute>
	    </fo:external-graphic>
	  </fo:block>
	</xsl:if>
      </xsl:when>

      <xsl:when test="$position = 'center'">

	<fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format">
	  <xsl:value-of select="ancestor-or-self::book/bookinfo/title"/>
	</fo:block>

	<fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format">for</fo:block>

	<fo:block xmlns:fo="http://www.w3.org/1999/XSL/Format">
	  <xsl:value-of select="ancestor-or-self::book/bookinfo/subtitle"/>
	</fo:block>
      </xsl:when>

    </xsl:choose>
  </xsl:variable>

    <!-- Does runtime parameter turn off blank page headers? -->
    <xsl:choose>
      <xsl:when test="$sequence='blank' and $headers.on.blank.pages=0">
        <!-- no output -->
      </xsl:when>
    <!-- titlepages have no headers -->
      <xsl:when test="$pageclass = 'titlepage'">  
        <!-- no output -->
      </xsl:when>
      <xsl:otherwise>
        <xsl:copy-of select="$candidate"/>
      </xsl:otherwise>
    </xsl:choose>

</xsl:template>

<!-- Running footer content -->
<xsl:template name="footer.content">  
  <xsl:param name="pageclass" select="''"/>
  <xsl:param name="sequence" select="''"/>
  <xsl:param name="position" select="''"/>
  <xsl:param name="gentext-key" select="''"/>

  <xsl:variable name="candidate">
    <!-- sequence can be odd, even, first, blank -->
    <!-- position can be left, center, right -->
    <xsl:choose>

      <xsl:when test="$position = 'left'">
	<fo:block>
        <xsl:if test="$pageclass != 'titlepage'">
          <xsl:choose>
            <xsl:when test="ancestor::book">
              <fo:retrieve-marker retrieve-class-name="section.head.marker"
                                  retrieve-position="first-including-carryover"
                                  retrieve-boundary="page-sequence"/>
            </xsl:when>
            <xsl:otherwise>
              <xsl:apply-templates select="." mode="titleabbrev.markup"/>
            </xsl:otherwise>
          </xsl:choose>
        </xsl:if>
	</fo:block>
	<!-- Don't include the biblioid at the bottom at this stage.
	<fo:block>
	  <xsl:value-of select="ancestor-or-self::book/bookinfo/biblioid"/>
	</fo:block>
	-->
      </xsl:when>

      <xsl:when test="$position = 'center'">
	<fo:page-number/>
      </xsl:when>

      <xsl:when test="$position = 'right'">
	<fo:block>
	  <xsl:value-of select="ancestor-or-self::book/bookinfo/releaseinfo"/>
	</fo:block>
	<fo:block>
	  <xsl:value-of select="ancestor-or-self::book/bookinfo/pubdate"/>
	</fo:block>
      </xsl:when>


    </xsl:choose>
  </xsl:variable>

    <!-- Does runtime parameter turn off blank page headers? -->
    <xsl:choose>
      <xsl:when test="$sequence='blank' and $headers.on.blank.pages=0">
        <!-- no output -->
      </xsl:when>
    <!-- titlepages have no headers -->
      <xsl:when test="$pageclass = 'titlepage'">  
        <!-- no output -->
      </xsl:when>
      <xsl:otherwise>
        <xsl:copy-of select="$candidate"/>
      </xsl:otherwise>
    </xsl:choose>

</xsl:template>

<!-- allow use of symbols -->
<xsl:template match="symbol[@role = 'symbolfont']">
  <fo:inline font-family="Symbol">
    <xsl:call-template name="inline.charseq"/>
  </fo:inline>
</xsl:template>

<!-- custom formatting of revision history information -->
<xsl:template match="revhistory" mode="titlepage.mode">

  <xsl:variable name="explicit.table.width">
    <xsl:call-template name="dbfo-attribute">
      <xsl:with-param name="pis"
                      select="processing-instruction('dbfo')"/>
      <xsl:with-param name="attribute" select="'table-width'"/>
    </xsl:call-template>
  </xsl:variable>

  <xsl:variable name="table.width">
    <xsl:choose>
      <xsl:when test="$explicit.table.width != ''">
        <xsl:value-of select="$explicit.table.width"/>
      </xsl:when>
      <xsl:when test="$default.table.width = ''">
        <xsl:text>100%</xsl:text>
      </xsl:when>
      <xsl:otherwise>
        <xsl:value-of select="$default.table.width"/>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:variable>

  <fo:block font-family="sans-serif,Symbol,ZapfDingbats"
	    font-weight="bold"
	    font-size="20.736pt"
	    hyphenate="false">
    <xsl:call-template name="gentext">
      <xsl:with-param name="key" select="'RevHistory'"/>
    </xsl:call-template>
  </fo:block>

<!-- FIXME: The table parameters should be paramaterised correctly -->
  <fo:table table-layout="fixed" width="{$table.width}"
		     border-left-style="solid"
		     border-right-style="solid"
		     border-top-style="solid"
		     border-bottom-style="solid"
		     border-left-width="0.5pt"
		     border-right-width="0.5pt"
		     border-top-width="0.5pt"
		     border-bottom-width="0.5pt"
		     border-left-color="black"
		     border-right-color="black"
		     border-top-color="black"
		     border-bottom-color="black">
    <fo:table-column column-number="1" column-width="proportional-column-width(0.5)"/>
    <fo:table-column column-number="2" column-width="proportional-column-width(1)"/>
    <fo:table-column column-number="3" column-width="proportional-column-width(0.5)"/>
    <fo:table-column column-number="4" column-width="proportional-column-width(2)"/>
    <fo:table-header start-indent="0pt">
      <fo:table-row>
	<fo:table-cell padding-left="2pt"
		       padding-top="2pt"
		       padding-right="2pt"
		       padding-bottom="2pt"
		       background-color="#EEEE00"
		       border-bottom-width="0.5pt"
		       border-bottom-style="solid"
		       border-bottom-color="black"
		       border-right-width="0.5pt"
		       border-right-style="solid"
		       border-right-color="black"
		       text-align="center">
	  <fo:block font-weight="bold">
	    Revision
	  </fo:block>
	</fo:table-cell>
	<fo:table-cell padding-left="2pt"
		       padding-top="2pt"
		       padding-right="2pt"
		       padding-bottom="2pt"
		       background-color="#EEEE00"
		       border-bottom-width="0.5pt"
		       border-bottom-style="solid"
		       border-bottom-color="black"
		       border-right-width="0.5pt"
		       border-right-style="solid"
		       border-right-color="black"
		       text-align="center">
	  <fo:block font-weight="bold">Date</fo:block>
	</fo:table-cell>
	<fo:table-cell padding-left="2pt"
		       padding-top="2pt"
		       padding-right="2pt"
		       padding-bottom="2pt"
		       background-color="#EEEE00"
		       border-bottom-width="0.5pt"
		       border-bottom-style="solid"
		       border-bottom-color="black"
		       border-right-width="0.5pt"
		       border-right-style="solid"
		       border-right-color="black"
		       text-align="center">
	  <fo:block font-weight="bold">Author</fo:block>
	</fo:table-cell>
	<fo:table-cell padding-left="2pt"
		       padding-top="2pt"
		       padding-right="2pt"
		       padding-bottom="2pt"
		       background-color="#EEEE00"
		       border-bottom-width="0.5pt"
		       border-bottom-style="solid"
		       border-bottom-color="black"
		       border-right-width="0.5pt"
		       border-right-style="solid"
		       border-right-color="black">
	  <fo:block font-weight="bold">Comment</fo:block>
	</fo:table-cell>
      </fo:table-row>
    </fo:table-header>
    <fo:table-body>
      <xsl:apply-templates mode="titlepage.mode"/>
    </fo:table-body>
  </fo:table>
</xsl:template>

<xsl:template match="revhistory/revision" mode="titlepage.mode">
  <xsl:variable name="revnumber" select=".//revnumber"/>
  <xsl:variable name="revdate"   select=".//date"/>
  <xsl:variable name="revauthor" select=".//authorinitials"/>
  <xsl:variable name="revremark" select=".//revremark|.//revdescription"/>
  <fo:table-row>
    <fo:table-cell padding-left="2pt"
		   padding-top="2pt"
		   padding-right="2pt"
		   padding-bottom="2pt"
		   border-bottom-width="0.5pt"
		   border-bottom-style="solid"
		   border-bottom-color="black"
		   border-right-width="0.5pt"
		   border-right-style="solid"
		   border-right-color="black"
		   text-align="center">
      <fo:block>
        <xsl:if test="$revnumber">
          <xsl:call-template name="gentext">
            <xsl:with-param name="key" select="'Revision'"/>
          </xsl:call-template>
          <xsl:call-template name="gentext.space"/>
          <xsl:apply-templates select="$revnumber[1]" mode="titlepage.mode"/>
        </xsl:if>
      </fo:block>
    </fo:table-cell>
    <fo:table-cell padding-left="2pt"
		   padding-top="2pt"
		   padding-right="2pt"
		   padding-bottom="2pt"
		   border-bottom-width="0.5pt"
		   border-bottom-style="solid"
		   border-bottom-color="black"
		   border-right-width="0.5pt"
		   border-right-style="solid"
		   border-right-color="black"
		   text-align="center">
      <fo:block>
        <xsl:apply-templates select="$revdate[1]" mode="titlepage.mode"/>
      </fo:block>
    </fo:table-cell>
    <fo:table-cell padding-left="2pt"
		   padding-top="2pt"
		   padding-right="2pt"
		   padding-bottom="2pt"
		   border-bottom-width="0.5pt"
		   border-bottom-style="solid"
		   border-bottom-color="black"
		   border-right-width="0.5pt"
		   border-right-style="solid"
		   border-right-color="black"
		   text-align="center">
      <fo:block>
        <xsl:apply-templates select="$revauthor[1]" mode="titlepage.mode"/>
      </fo:block>
    </fo:table-cell>
    <fo:table-cell padding-left="2pt"
		   padding-top="2pt"
		   padding-right="2pt"
		   padding-bottom="2pt"
		   border-bottom-width="0.5pt"
		   border-bottom-style="solid"
		   border-bottom-color="black"
		   border-right-width="0.5pt"
		   border-right-style="solid"
		   border-right-color="black">

      <fo:block>
	<xsl:apply-templates select="$revremark[1]" mode="titlepage.mode"/>
      </fo:block>
    </fo:table-cell>
  </fo:table-row>
</xsl:template>

<xsl:attribute-set name="table.entry.para.spacing">
  <xsl:attribute name="space-before.optimum">0.1em</xsl:attribute>
  <xsl:attribute name="space-before.minimum">0.1em</xsl:attribute>
  <xsl:attribute name="space-before.maximum">0.1em</xsl:attribute>
</xsl:attribute-set>

<!-- modify paragraph spacing when used within a table entry -->
<xsl:template match="para[ancestor::entry]">
  <fo:block xsl:use-attribute-sets="table.entry.para.spacing">
    <xsl:call-template name="anchor"/>
    <xsl:apply-templates/>
  </fo:block>

</xsl:template>

<!-- Customise fo output to include a fo:declarations section
     to display PDF author, subject, etc. items, if defined.
 -->
<xsl:template match="*" mode="process.root">
  <xsl:variable name="document.element" select="self::*"/>

  <xsl:call-template name="root.messages"/>

  <xsl:variable name="title">
    <xsl:choose>
      <xsl:when test="$document.element/title[1]">
        <xsl:value-of select="$document.element/title[1]"/>
      </xsl:when>
      <xsl:otherwise>[could not find document title]</xsl:otherwise>
    </xsl:choose>
  </xsl:variable>
  
  <!-- Include all id values in XEP output -->
  <xsl:if test="$xep.extensions != 0">
    <xsl:processing-instruction 
     name="xep-pdf-drop-unused-destinations">false</xsl:processing-instruction>
  </xsl:if>

  <fo:root xsl:use-attribute-sets="root.properties">
    <xsl:attribute name="language">
      <xsl:call-template name="l10n.language">
        <xsl:with-param name="target" select="/*[1]"/>
      </xsl:call-template>
    </xsl:attribute>

    <xsl:if test="$xep.extensions != 0">
      <xsl:call-template name="xep-pis"/>
      <xsl:call-template name="xep-document-information"/>
    </xsl:if>
    <xsl:if test="$axf.extensions != 0">
      <xsl:call-template name="axf-document-information"/>
    </xsl:if>

    <xsl:call-template name="setup.pagemasters"/>

    <xsl:call-template name="setup.pdf.metadata"/>

    <xsl:if test="$fop.extensions != 0">
      <xsl:apply-templates select="$document.element" mode="fop.outline"/>
    </xsl:if>

    <xsl:if test="$fop1.extensions != 0">
      <xsl:variable name="bookmarks">
        <xsl:apply-templates select="$document.element" 
	                     mode="fop1.outline"/>
      </xsl:variable>
      <xsl:if test="string($bookmarks) != ''">
        <fo:bookmark-tree>
          <xsl:copy-of select="$bookmarks"/>
	</fo:bookmark-tree>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$xep.extensions != 0">
      <xsl:variable name="bookmarks">
        <xsl:apply-templates select="$document.element" mode="xep.outline"/>
      </xsl:variable>
      <xsl:if test="string($bookmarks) != ''">
        <rx:outline xmlns:rx="http://www.renderx.com/XSL/Extensions">
          <xsl:copy-of select="$bookmarks"/>
        </rx:outline>
      </xsl:if>
    </xsl:if>

    <xsl:if test="$arbortext.extensions != 0 and $ati.xsl11.bookmarks != 0">
      <xsl:variable name="bookmarks">
	<xsl:apply-templates select="$document.element"
			     mode="ati.xsl11.bookmarks"/>
      </xsl:variable>
      <xsl:if test="string($bookmarks) != ''">
	<fo:bookmark-tree>
	  <xsl:copy-of select="$bookmarks"/>
	</fo:bookmark-tree>
      </xsl:if>
    </xsl:if>

    <xsl:apply-templates select="$document.element"/>
  </fo:root>
</xsl:template>

<xsl:template name="setup.pdf.metadata">
<!--
  <xsl:message>Document element: <xsl:value-of select="/book/bookinfo/title"/>
  </xsl:message>
-->
  <xsl:if test="$fop1.extensions != 0">
    <fo:declarations>
      <x:xmpmeta xmlns:x="adobe:ns:meta/">
	<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
	  <rdf:Description rdf:about=""
			   xmlns:dc="http://purl.org/dc/elements/1.1/">
	    <!-- Dublin Core properties go here -->
	    <dc:title><xsl:value-of select="/book/bookinfo/title"/> - <xsl:value-of select="/book/bookinfo/subtitle"/></dc:title>

	    <xsl:if test="/book/bookinfo/author">
	      <dc:creator>
		<xsl:value-of select="/book/bookinfo/author/firstname"/><xsl:text> </xsl:text>
		<xsl:value-of select="/book/bookinfo/author/surname"/>
		<xsl:if test="/book/bookinfo/author/email">
		  <xsl:text> </xsl:text>&lt;<xsl:value-of select="/book/bookinfo/author/email"/>&gt;
		</xsl:if>
	      </dc:creator>
	    </xsl:if>
	    <dc:subject><xsl:value-of select="/book/bookinfo/title"/></dc:subject>
	  </rdf:Description>
	  <rdf:Description rdf:about=""
			   xmlns:xmp="http://ns.adobe.com/xap/1.0/">
	    <!-- XMP properties go here -->
	    <xmp:CreatorTool>DocGen $Revision$ by Justin Warren &lt;justin@eigenmagic.com&gt;</xmp:CreatorTool>
	  </rdf:Description>
	</rdf:RDF>
      </x:xmpmeta>
    </fo:declarations>

  </xsl:if>

</xsl:template>

</xsl:stylesheet>