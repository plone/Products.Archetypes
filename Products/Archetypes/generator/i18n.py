try:
    # XXX Depends on 2.6
    from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService, \
         DummyTranslationService
except ImportError:
    class DummyTranslationService:
        """ A very very dummy translation service """
        pass

    def getGlobalTranslationService():
        return DummyTranslationService

service = None
translate = None

def translate_wrapper(domain, msgid, mapping=None, context=None, target_language=None, default=None):
    # wrapper for calling the translate() method with a fallback value

    try:
        res = service.translate(domain, msgid, mapping=mapping, context=context, target_language=target_language, default=default)
    except TypeError:
        #Localizer does not take a default param
        res = service.translate(domain, msgid, mapping=mapping, context=context, target_language=target_language)

    if res is None or res is msgid:
        return default
    return res

def null_translate(domain, msgid, mapping=None, context=None, target_language=None, default=None):
    return default

def initialize():
    # IMPORTANT: this module is unusable before this is called
    # this must be so because we want to make sure all products
    # (eg, whatever translation service we're supposed to use)
    # is already there and ready
    global service, translate
    service = getGlobalTranslationService()
    if service is DummyTranslationService:
        translate = null_translate
    elif hasattr(service, '_fallbacks'):
        # it accepts the "default" argument
        translate = service.translate
    else:
        translate = translate_wrapper

def initial_translate(domain, msgid, mapping=None, context=None, target_language=None, default=None):
    initialize()
    return translate(domain, msgid, mapping, context, target_language, default)

translate = initial_translate
