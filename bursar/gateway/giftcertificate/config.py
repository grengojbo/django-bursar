from livesettings import *
from django.utils.translation import ugettext_lazy as _

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_GIFTCERTIFICATE', 'Gift Certificates'))

PRODUCTS = config_get('PRODUCT', 'PRODUCT_TYPES')
PRODUCTS.add_choice(('giftcertificate::GiftCertificateProduct', _('Gift Certificate')))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_GIFTCERTIFICATE', 
    _('Gift Certificate Settings'), 
    requires=GATEWAY_MODULES)

config_register_list(
    BooleanValue(GATEWAY_GROUP, 
        'SSL', 
        description=_("Use SSL for the checkout pages?"), 
        default=False),
        
    StringValue(GATEWAY_GROUP,
        'CHARSET',
        description=_("Character Set"),
        default="BCDFGHKPRSTVWXYZbcdfghkprstvwxyz23456789",
        help_text=_("The characters allowable in randomly-generated certficate codes.  No vowels means no unfortunate words.")),
        
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'GIFTCERTIFICATE'),
        
    StringValue(GATEWAY_GROUP,
        'FORMAT',
        description=_('Code format'),
        default="^^^^-^^^^-^^^^",
        help_text=_("Enter the format for your cert code.  Use a '^' for the location of a randomly generated character.")),
        
    ModuleValue(GATEWAY_GROUP,
        'MODULE',
        description=_('Implementation module'),
        hidden=True,
        default = 'payment.modules.giftcertificate'),

    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'Gift Certificate',
        help_text = _('This will be passed to the translation utility')),
        
    BooleanValue(GATEWAY_GROUP, 
        'LIVE', 
        description=_("Accept real payments"),
        help_text=_("False if you want to be in test mode"),
        default=False),

    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = r'^giftcertificate/'),
        
    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
)
