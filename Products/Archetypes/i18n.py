from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService, \
                                                            DummyTranslationService

service = None
translate = None

def translate_wrapper(domain, msgid, data, request, target, default):
    # wrapper for calling the translate() method with a fallback value
    res = service.translate(domain, msgid, data, request, target)
    if res is None or res is msgid:
        return default
    return res

def null_translate(domain, msgid, data, request, target, default):
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

def initial_translate(domain, msgid, data, request, target, default):
    initialize()
    return translate(domain, msgid, data, request, target, default)

translate = initial_translate
