<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
    <xsl:template match="/">
        <window xmlns="http://www.mozilla.org/keymaster/gatekeeper/there.is.only.xul">
            <hbox id="ab-main">
                <vbox>
                    <groupbox>
                        <caption label="Types" style="font-size: large"/>
                        <listbox>
                            <listhead>
                                <listheader label="Name"/>
                                <listheader label="Read-only?"/>
                            </listhead>
                            <listcols>
                                <listcol flex="1"/>
                            </listcols>
                            <xsl:apply-templates select="/registry/types/type"/>
                        </listbox>
                    </groupbox>
                </vbox>
                <vbox flex="3">
                    <xsl:apply-templates mode="currenttype" select="//type[@selected]"/>
                </vbox>
                <vbox flex="2">
                    <groupbox>
                        <caption label="Properties" style="font-size: large"/>
                        <xsl:apply-templates mode="propertyview" select="/registry/types/type[@selected]/schema/schemata/field[@selected]/properties/property"/>
                    </groupbox>
                </vbox>
            </hbox>
        </window>
    </xsl:template>
    <xsl:template match="fieldelement">
        <menuitem label="{title}"/>
    </xsl:template>
    <xsl:template match="widgetelement">
        <vbox>
            <label value="Widget: {title}"/>
            <xsl:value-of select="title"/>
        </vbox>
    </xsl:template>
    <xsl:template match="type[@selected]" mode="currenttype">
        <groupbox>
            <caption label="Working Type: {portaltype}" style="font-size: large"/>
            <label value="Base Type: {basetype}"/>
            <xsl:apply-templates select="schema/schemata"/>
        </groupbox>
    </xsl:template>
    <xsl:template match="type">
        <listitem>
            <xsl:if test="@selected">
                <xsl:attribute name="checked">1</xsl:attribute>
            </xsl:if>
            <listcell label="{portaltype}"/>
            <listcell label="{readonly}"/>
        </listitem>
    </xsl:template>
    <xsl:template match="schemata">
        <groupbox>
            <caption label="Subschema: {name}"/>
            <listbox style="height: 50px; min-height: 2ex; max-height: 300px">
                <listhead>
                    <listheader label="Name"/>
                </listhead>
                <listcols>
                    <listcol flex="1"/>
                </listcols>
                <xsl:apply-templates select="field"/>
            </listbox>
            <hbox>
                <button label="Add Field..." type="menu">
                    <menupopup>
                        <xsl:apply-templates select="/registry/fieldelements/fieldelement"/>
                    </menupopup>
                </button>
                <spacer flex="1"/>
            </hbox>
        </groupbox>
    </xsl:template>
    <xsl:template match="property" mode="propertyview">
        <xsl:variable name="thistype" select="type"/>
        <xsl:apply-templates mode="listproperty" select="/registry/fieldelements/fieldelement[@id=$thistype]/properties/property"/>
    </xsl:template>
    <xsl:template match="field">
        <listitem>
            <listcell label="{name}"/>
        </listitem>
    </xsl:template>
    <xsl:template match="property" mode="listproperty">
        <xsl:call-template name="propertyrow">
            <xsl:with-param name="field" select="."/>
            <xsl:with-param name="property" select="."/>
        </xsl:call-template>
        <!--        <xsl:choose>
            <xsl:when test="type='boolean'"><checkbox id="case-sensitive"/><xsl:attribute name="checked">
            <xsl:choose>
                <xsl:when test=""></xsl:when>
            </xsl:choose>
            </xsl:attribute></xsl:when>
        </xsl:choose>
        
        <label value="{type}"/>
-->
    </xsl:template>
    <xsl:template name="propertyrow">
        <xsl:param name="field"/>
        <xsl:param name="property"/>
        <xsl:variable name="propertyname" select="property/name"/>
        <label value="{$propertyname}"/>
    </xsl:template>
</xsl:stylesheet>
