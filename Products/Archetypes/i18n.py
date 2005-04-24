""" IMPORTANT: this module is unusable before initialize is called
    this must be so because we want to make sure all products
    (eg, whatever translation service we're supposed to use)
    is already there and ready
"""    
from Products.PageTemplates.GlobalTranslationService import getGlobalTranslationService, \
     DummyTranslationService

service = None
translate = None

def translate_wrapper(domain, msgid, mapping=None, context=None, 
                      target_language=None, default=None):
    # wrapper for calling the translate() method with a fallback value

    if hasattr(service, 'utranslate'):
        res = service.utranslate(domain, msgid, mapping=mapping, context=context, 
                                 target_language=target_language, 
                                 default=default)
    else:
        res = service.translate(domain, msgid, mapping=mapping, context=context, 
                                target_language=target_language, 
                                default=default)

    if res is None or res is msgid:
        return default
    return res

def null_translate(domain, msgid, mapping=None, context=None, 
                   target_language=None, default=None):
    return default

def initialize():
    """ must be calles after Products are there and ready """
    global service, translate
    service = getGlobalTranslationService()
    if service is DummyTranslationService:
        translate = null_translate
    elif hasattr(service, '_fallbacks'):
        # it accepts the "default" argument
        translate = service.translate
    else:
        translate = translate_wrapper

def initial_translate(domain, msgid, mapping=None, context=None, 
                      target_language=None, default=None):
    initialize()
    return translate(domain, msgid, mapping, context, target_language, default)

translate = initial_translate
