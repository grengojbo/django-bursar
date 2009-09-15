from livesettings import *
from django.utils.translation import ugettext_lazy as _

# this is so that the translation utility will pick up the string
gettext = lambda s: s

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_DUMMY', _('Payment Test Module')))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_DUMMY', 
    _('Payment Test Module Settings'), 
    requires=GATEWAY_MODULES,
    ordering = 100)

config_register_list(
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
        default = 'payment.modules.dummy'),
        
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'DUMMY'),

    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'Payment test module',
        help_text = _('This will be passed to the translation utility')),

    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = '^dummy/'),

    MultipleStringValue(GATEWAY_GROUP,
        'CREDITCHOICES',
        description=_('Available credit cards'),
        choices = (
            (('Visa','Visa')),
            (('Mastercard','Mastercard')),
            (('Discover','Discover')),
            (('American Express', 'American Express'))),
        default = ('Visa', 'Mastercard', 'Discover', 'American Express')),
        
    BooleanValue(GATEWAY_GROUP,
        'CAPTURE',
        description=_('Capture Payment immediately?'),
        default=True,
        help_text=_('IMPORTANT: If false, a capture attempt will be made when the order is marked as shipped."')),
        
    BooleanValue(GATEWAY_GROUP,
        'AUTH_EARLY',
        description=_("Early AUTH"),
        help_text=_("Authenticate on the card entry page, causes an immediate $.01 AUTH and release, allowing errors with the card to show on the card entry page."),
        default=False),

    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
)
