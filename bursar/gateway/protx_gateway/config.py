from livesettings import *
from django.utils.translation import ugettext_lazy as _

# this is so that the translation utility will pick up the string
gettext = lambda s: s
_strings = (gettext('CreditCard'), gettext('Credit Card'), gettext('Prot/X Secure Payments'))

# These cards require the issue number and start date fields filled in.
REQUIRES_ISSUE_NUMBER = ('MAESTRO', 'SOLO')

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_PROTX', 'Prot/X VSP Direct'))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_PROTX', 
    _('Prot/X Payment Settings'), 
    requires=GATEWAY_MODULES,
    ordering=101)

config_register_list(

    BooleanValue(GATEWAY_GROUP, 
        'LIVE', 
        description=_("Accept real payments"),
        help_text=_("False if you want to be in test mode"),
        default=False),
        
    BooleanValue(GATEWAY_GROUP, 
        'SIMULATOR', 
        description=_("Simulated Transactions?"),
        help_text=_("Must be false to accept real payments"),
        default=False),

    BooleanValue(GATEWAY_GROUP, 
        'SKIP_POST', 
        description=_("Skip post?"),
        help_text=_("For testing only, this will skip actually posting to Prot/x servers.  This is because their servers restrict IPs of posting servers, even for tests.  If you are developing on a desktop, you'll have to enable this."),
        default=False),
        
    StringValue(GATEWAY_GROUP, 
        'CAPTURE',
        description=_('Payment Capture'),
        help_text=_('This can be "Payment" which captures immediately, or "Deferred".  Note that you can only use the latter if you set option on your Prot/X account first.'),
        choices = (
            (('GATEWAY', 'Payment')),
            (('DEFERRED', 'Deferred')),
        ),
        default = 'GATEWAY'),
    
    
    BooleanValue(GATEWAY_GROUP, 
        'SSL', 
        description=_("Use SSL for the checkout pages?"), 
        default=False),

    ModuleValue(GATEWAY_GROUP,
        'MODULE',
        description=_('Implementation module'),
        hidden=True,
        default = 'payment.modules.protx'),
    
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'PROTX'),

    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'Prot/X Secure Payments',
        help_text = _('This will be passed to the translation utility')),

    MultipleStringValue(GATEWAY_GROUP,
        'CREDITCHOICES',
        description=_('Available credit cards'),
        choices = (
                (('VISA','Visa Credit/Debit')),
                (('UKE','Visa Electron')),
                (('DELTA','Delta')),
                #(('AMEX','American Express')),  # not always available
                #(('DC','Diners Club')), # not always available
                (('MC','Mastercard')),
                (('MAESTRO','UK Maestro')),
                (('SOLO','Solo')),
                (('JCB','JCB')),
            ),
        default = ('VISA', 'MC')),
    
    StringValue(GATEWAY_GROUP, 
        'VENDOR', 
        description=_('Your Vendor Name'),
        default="",
        help_text= _("This is used for Live and Test transactions.  Make sure to add your server IP address to VSP, or it won't work.")),

    StringValue(GATEWAY_GROUP, 
        'VENDOR_SIMULATOR', 
        description=_('Simulator Vendor Name'),
        default="",
        help_text= _("This is used for Live and Test transactions.  Make sure to activate the VSP Simulator (you have to directly request it) and add your server IP address to the VSP Simulator, or it won't work.")),
            
    StringValue(GATEWAY_GROUP, 
        'CURRENCY_CODE',
        description=_('Currency Code'),
        help_text=_('Currency code for Prot/X transactions.'),
        default = 'GBP'),
        
    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = r'^protx/'),
        
    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
)
