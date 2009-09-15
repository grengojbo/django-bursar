from livesettings import *
from django.utils.translation import ugettext_lazy as _

# this is so that the translation utility will pick up the string
gettext = lambda s: s
_strings = (gettext('CreditCard'), gettext('Credit Card'))

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_AUTHORIZENET', 'Authorize.net'))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_AUTHORIZENET', 
    _('Authorize.net Payment Settings'), 
    requires=GATEWAY_MODULES,
    ordering=101)

config_register_list(

    StringValue(GATEWAY_GROUP, 
        'CONNECTION',
        description=_("Submit to URL"),
        help_text=_("""This is the address to submit live transactions."""),
        default='https://secure.authorize.net/gateway/transact.dll'),

    StringValue(GATEWAY_GROUP, 
        'CONNECTION_TEST',
        description=_("Submit to Test URL"),
        help_text=("""A Quick note on the urls.<br/>
If you are posting to https://test.authorize.net/gateway/transact.dll,
and you are not using an account whose API login ID starts with
&quot;cpdev&quot; or &quot;cnpdev&quot;, you will get an Error 13 message. 
Make sure you are posting to https://certification.authorize.net/gateway/transact.dll
for test transactions if you do not have a cpdev or cnpdev.
"""),
        default='https://test.authorize.net/gateway/transact.dll'),


    BooleanValue(GATEWAY_GROUP, 
        'SSL', 
        description=_("Use SSL for the checkout pages?"), 
        default=False),
    
    BooleanValue(GATEWAY_GROUP, 
        'LIVE', 
        description=_("Accept real payments"),
        help_text=_("False if you want to submit to the test urls.  NOTE: If you are testing, then you can use the cc# 4222222222222 to force a bad credit card response.  If you use that number and a ccv of 222, that will force a bad ccv response from authorize.net"),
        default=False),

    BooleanValue(GATEWAY_GROUP, 
        'SIMULATE', 
        description=_("Force a test post?"),
        help_text=_("True if you want to submit to the live url using a test flag, which won't be accepted."),
        default=False),

    ModuleValue(GATEWAY_GROUP,
        'MODULE',
        description=_('Implementation module'),
        hidden=True,
        default = 'payment.modules.authorizenet'),
    
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'AUTHORIZENET'),

    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'Credit Cards',
        help_text = _('This will be passed to the translation utility')),

    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = r'^credit/'),

    MultipleStringValue(GATEWAY_GROUP,
        'CREDITCHOICES',
        description=_('Available credit cards'),
        choices = (
            (('American Express', 'American Express')),
            (('Visa','Visa')),
            (('Mastercard','Mastercard')),
            (('Discover','Discover'))),
        default = ('Visa', 'Mastercard', 'Discover')),
    
    StringValue(GATEWAY_GROUP, 
        'LOGIN', 
        description=_('Your authorize.net transaction login'),
        default=""),
    
    StringValue(GATEWAY_GROUP, 
        'TRANKEY', 
        description=_('Your authorize.net transaction key'),
        default=""),
        
    BooleanValue(GATEWAY_GROUP,
        'CAPTURE',
        description=_('Capture Payment immediately?'),
        default=True,
        help_text=_('IMPORTANT: If false, a capture attempt will be made when the order is marked as shipped."')),

    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
)

ARB_ENABLED = config_register(    
    BooleanValue(GATEWAY_GROUP,
        'ARB',
        description=_('Enable ARB?'),
        default=False,
        help_text=_('Enable ARB processing for setting up subscriptions.  You must have this enabled in your Authorize account for it to work.')))

config_register(
    StringValue(GATEWAY_GROUP, 
        'ARB_CONNECTION',
        description=_("Submit to URL (ARB)"),
        help_text=_("""This is the address to submit live transactions for ARB."""),
        requires=ARB_ENABLED,
        default='https://api.authorize.net/xml/v1/request.api'))

config_register(    
    StringValue(GATEWAY_GROUP, 
        'ARB_CONNECTION_TEST',
        description=_("Submit to Test URL (ARB)"),
        help_text=_("""This is the address to submit test transactions for ARB."""),
        requires=ARB_ENABLED,
        default='https://apitest.authorize.net/xml/v1/request.api'))

