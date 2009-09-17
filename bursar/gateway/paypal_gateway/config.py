from livesettings import *
from django.utils.translation import ugettext_lazy as _

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_PAYPAL', _('Paypal Payment Settings')))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_PAYPAL', 
    _('Paypal Payment Module Settings'), 
    requires=GATEWAY_MODULES,
    ordering = 101)

config_register_list(

StringValue(GATEWAY_GROUP,
    'CURRENCY_CODE',
    description=_('Currency Code'),
    help_text=_('Currency code for Paypal transactions.'),
    default = 'USD'),
    
StringValue(GATEWAY_GROUP,
    'POST_URL',
    description=_('Post URL'),
    help_text=_('The Paypal URL for real transaction posting.'),
    default="https://www.paypal.com/cgi-bin/webscr"),

StringValue(GATEWAY_GROUP,
    'POST_TEST_URL',
    description=_('Post URL'),
    help_text=_('The Paypal URL for test transaction posting.'),
    default="https://www.sandbox.paypal.com/cgi-bin/webscr"),

StringValue(GATEWAY_GROUP,
    'BUSINESS',
    description=_('Paypal account email'),
    help_text=_('The email address for your paypal account'),
    default=""),

StringValue(GATEWAY_GROUP,
    'BUSINESS_TEST',
    description=_('Paypal test account email'),
    help_text=_('The email address for testing your paypal account'),
    default=""),

StringValue(GATEWAY_GROUP,
    'RETURN_ADDRESS',
    description=_('Return URL'),
    help_text=_('Where Paypal will return the customer after the purchase is complete.  This can be a named url and defaults to the standard checkout success.'),
    default="satchmo_checkout-success"),
    
BooleanValue(GATEWAY_GROUP, 
    'SSL', 
    description=_("Use SSL for the module checkout pages?"), 
    default=False),
    
BooleanValue(GATEWAY_GROUP, 
    'LIVE', 
    description=_("Accept real payments"),
    help_text=_("False if you want to be in test mode"),
    default=False),
    
ModuleValue(GATEWAY_GROUP,
    'MODULE',
    description=_('Implementation module'),
    hidden=True,
    default = 'payment.modules.paypal'),
    
StringValue(GATEWAY_GROUP,
    'KEY',
    description=_("Module key"),
    hidden=True,
    default = 'PAYPAL'),

StringValue(GATEWAY_GROUP,
    'LABEL',
    description=_('English name for this group on the checkout screens'),
    default = 'PayPal',
    help_text = _('This will be passed to the translation utility')),

StringValue(GATEWAY_GROUP,
    'URL_BASE',
    description=_('The url base used for constructing urlpatterns which will use this module'),
    default = '^paypal/'),
    
BooleanValue(GATEWAY_GROUP,
    'EXTRA_LOGGING',
    description=_("Verbose logs"),
    help_text=_("Add extensive logs during post."),
    default=False)
)

GATEWAY_GROUP['TEMPLATE_OVERRIDES'] = {
    'shop/checkout/confirm.html' : 'shop/checkout/paypal/confirm.html',
}
