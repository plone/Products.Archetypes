from Products.Archetypes.validation.validators.RegexValidator import RegexValidator
from Products.Archetypes.validation.validators.RangeValidator import RangeValidator

baseValidators = [
    RangeValidator('inNumericRange', title='', description=''),
    RegexValidator('isDecimal',
                   r'^([+-]?)(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?$',
                   title='', description='',
                   errmsg='is not a decimal number.'),
    RegexValidator('isInt', r'^([+-])?\d+$', title='', description='',
                   errmsg='is not an integer.'),
    RegexValidator('isPrintable', r'[a-zA-Z0-9\s]+$', title='', description='',
                   errmsg='contains unprintable characters'),
    RegexValidator('isSSN', r'^\d{9}$', title='', description='',
                   errmsg='is not a well formed SSN.'),
    RegexValidator('isUSPhoneNumber', r'^\d{10}$', ignore='[\(\)\-\s]',
                   title='', description='',
                   errmsg='is not a valid us phone number.'),
    RegexValidator('isInternationalPhoneNumber', r'^\d+$', ignore='[\(\)\-\s\+]',
                   title='', description='',
                   errmsg='is not a valid international phone number.'),
    RegexValidator('isZipCode', r'^(\d{5}|\d{9})$',
                   title='', description='',
                   errmsg='is not a valid zip code.'),
    RegexValidator('isURL', r'(ht|f)tps?://[^\s\r\n]+',
                   title='', description='',
                   errmsg='is not a valid url (http, https or ftp).'),
    RegexValidator('isEmail', "^([0-9a-zA-Z_&.+-]+!)*[0-9a-zA-Z_&.+-]+@(([0-9a-z]([0-9a-z-]*[0-9a-z])?\.)+[a-z]{2,6}|([0-9]{1,3}\.){3}[0-9]{1,3})$",
                   title='', description='',
                   errmsg='is not a valid email address.'),

    RegexValidator('isUnixLikeName', '^[A-Za-z][\w\d\-\_]{0,7}',
                   title="", description="",
                   errmsg="this name is not a valid identifier"),
    ]

__all__ = ('baseValidators', )
