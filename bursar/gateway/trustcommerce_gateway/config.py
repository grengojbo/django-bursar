from livesettings import *
from django.utils.translation import ugettext_lazy as _

gettext = lambda s:s
_strings = (gettext('CreditCard'), gettext('Credit Card'))

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_TRUSTCOMMERCE', 'TrustCommerce'))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_TRUSTCOMMERCE', 
    _('TrustCommerce Payment Settings'), 
    requires=GATEWAY_MODULES,
    ordering=102)

config_register_list(

    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'TRUSTCOMMERCE'),

    ModuleValue(GATEWAY_GROUP,
        'MODULE',
        description=_('Implementation module'),
        hidden=True,
        default = 'payment.modules.trustcommerce'),
        
    BooleanValue(GATEWAY_GROUP, 
        'SSL', 
        description=_("Use SSL for the checkout pages?"), 
        default=False),
    
    BooleanValue(GATEWAY_GROUP, 
        'AVS', 
        description=_("Use Address Verification System (AVS)?"), 
        default=False),
    
    BooleanValue(GATEWAY_GROUP, 
        'LIVE', 
        description=_("Accept real payments"),
        help_text=_("False if you want to be in test mode"),
        default=False),
    
    StringValue(GATEWAY_GROUP,
        'AUTH_TYPE',
        description=_("Type of authorization to perform."),
        help_text = _("Refer to manual for details on the different types."),
        default = 'sale',
        choices = [('sale', _('Sale')),
                    ('preauth', _('Preauth'))]
        ),
        
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
        description=_('Your TrustCommerce login'),
        default=""),
    
    StringValue(GATEWAY_GROUP, 
        'PASSWORD', 
        description=_('Your TrustCommerce password'),
        default=""),
        
    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
)
