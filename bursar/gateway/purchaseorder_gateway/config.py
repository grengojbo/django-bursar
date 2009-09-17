from livesettings import *
from django.utils.translation import ugettext_lazy as _
import logging

log = logging.getLogger('purchaseorder.config')

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_PURCHASEORDER', _('Purchase Order')))
log.debug('added purchase order payments')

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_PURCHASEORDER', 
    _('Purchase Order Module Settings'), 
    requires=GATEWAY_MODULES,
    ordering = 100)

config_register_list(    
    BooleanValue(GATEWAY_GROUP, 
        'LIVE', 
        description=_("Accept real payments"),
        help_text=_("False if you want to be in test mode"),
        default=False),
        
    ModuleValue(GATEWAY_GROUP,
        'MODULE',
        description=_('Implementation module'),
        hidden=True,
        default = 'payment.modules.purchaseorder'),
        
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'PURCHASEORDER'),

    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'Purchase Order',
        help_text = _('This will be passed to the translation utility')),

    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = '^po/'),
        
    BooleanValue(GATEWAY_GROUP, 
        'EXTRA_LOGGING', 
        description=_("Verbose logging?"),
        default=False),
        
    BooleanValue(GATEWAY_GROUP, 
        'SSL', 
        description=_("Use SSL for the checkout pages?"), 
        default=False),
)
