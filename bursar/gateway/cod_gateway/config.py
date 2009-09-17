from livesettings import *
from django.utils.translation import ugettext_lazy as _

# this is so that the translation utility will pick up the string
gettext = lambda s: s

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_COD', _('COD')))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_COD', 
    _('COD Payment Module Settings'), 
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
        default = 'payment.modules.cod'),
        
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'COD'),

    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'COD Payment',
        help_text = _('This will be passed to the translation utility')),

    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = '^cod/'),
        
    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
)
