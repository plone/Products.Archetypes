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
                        <xsl:apply-templates mode="propertyview" select="/registry/types/type[@selected]/schema/schemata/field[@selected]/properties/*"/>
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
    <xsl:template match="properties/*" mode="propertyview">
        <xsl:variable name="thistype" select="../../type"/>
        <xsl:variable name="propertyname" select="local-name()"/>
        <xsl:variable name="propertyelement" select="/registry/fieldelements/fieldelement[@id=$thistype]/properties/property[name=$propertyname]"/>
        <xsl:variable name="allowedwidgets" select="/registry/fieldelements/fieldelement[@id=$thistype]/allowedwidgetelements/*"/>
        <label value="{$propertyname}"/>
        <xsl:choose>
            <xsl:when test="$propertyelement/type='boolean'">
                <checkbox id="case-sensitive">
                    <xsl:attribute name="checked">
                        <xsl:choose>
                            <xsl:when test=". = 1">true</xsl:when>
                            <xsl:otherwise>false</xsl:otherwise>
                        </xsl:choose>
                    </xsl:attribute>
                </checkbox>
            </xsl:when>
            <xsl:when test="$propertyelement/type='widget'">
                <hbox>
                    <menulist>
                        <menupopup>
                            <xsl:variable name="widgettype" select="./type"/>
                            <xsl:for-each select="$allowedwidgets">
                                <menuitem label="{.}">
                                    <xsl:if test=". = $widgettype">
                                        <xsl:attribute name="selected">true</xsl:attribute>
                                    </xsl:if>
                                </menuitem>
                            </xsl:for-each>
                        </menupopup>
                    </menulist>
                    <spacer flex="1"/>
                </hbox>
            </xsl:when>
            <xsl:otherwise>
                <label value="otherwidget"/>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>
    <xsl:template match="field">
        <listitem>
            <listcell label="{name}"/>
        </listitem>
    </xsl:template>
</xsl:stylesheet>
