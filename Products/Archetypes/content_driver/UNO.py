from Products.Archetypes.debug import log, log_exc
from Globals import package_home
import os

setup_ini = 'file://%s/uno.ini' % package_home(globals())
try:
    import PyUNO
except:
    log_exc()

class UNO:

    def __init__ ( self, connection='socket,host=localhost,port=2002;urp', setup=setup_ini ):
        """ do the bootstrap

                connection can be one or more of the following:

                socket,
                host = localhost | <hostname> | <ip-addr>,
                port = <port>,
                service = soffice,
                user = <username>,
                password = <password>
                ;urp

        """

        self.XComponentContext = PyUNO.bootstrap ( setup )
        self.XUnoUrlResolver, o = \
                self.XComponentContext.ServiceManager.createInstanceWithContext ( 'com.sun.star.bridge.UnoUrlResolver', self.XComponentContext )
        self.XNamingService, o = self.XUnoUrlResolver.resolve ( 'uno:%s;StarOffice.NamingService' % connection )
        self.XMultiServiceFactory, o = self.XNamingService.getRegisteredObject ('StarOffice.ServiceManager')
        self.XComponentLoader, o = \
                self.XMultiServiceFactory.createInstance ( 'com.sun.star.frame.Desktop' )


    def new ( self, what, where='_blank', no=0, propertyValues=() ):
        return self.XComponentLoader.loadComponentFromURL (
                what, where, no, propertyValues )


    def newIdlStruct ( self, type ):
        return PyUNO.createIdlStruct ( self.XMultiServiceFactory, type )


    def newCalc (self):
        return self.new ('private:factory/scalc')


    def newWriter (self):
        return self.new ('private:factory/swriter')


    def newImpress (self):
        return self.new ('private:factory/simpress')


    def newDraw (self):
        return self.new ('private:factory/sdraw')


    def newPropertyValue (self, propertyValue={} ):
        property = self.newIdlStruct  ( 'com.sun.star.beans.PropertyValue' )

        if propertyValue.has_key('Name'):
            property.Name = propertyValue['Name']

        if propertyValue.has_key('Value'):
            property.Value = propertyValue['Value']

        if propertyValue.has_key('State'):
            property.State = propertyValue['State']

        if propertyValue.has_key('Handle'):
            property.Handle = propertyValue['Handle']

        return property


    def newPropertyValues ( self, propertyValues=[] ):
        list = ()

        l = len(propertyValues)
        for p in range (l):
            list = list + ( self.newPropertyValue ( propertyValues.pop(0) ), )

        return list


    def newBoolean ( self, bool=0 ):
        if bool:
            return PyUNO.true()
        else:
            return PyUNO.false()

# vim:ts=4
