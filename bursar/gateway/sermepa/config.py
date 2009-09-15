#
#   SERMEPA / ServiRed payments module for Satchmo
#
#   Author: Michal Salaban <michal (at) salaban.info>
#   with a great help of Fluendo S.A., Barcelona
#
#   Based on "Guia de comercios TPV Virtual SIS" ver. 5.18, 15/11/2008, SERMEPA
#   For more information about integration look at http://www.sermepa.es/
#
#   TODO: SERMEPA interface provides possibility of recurring payments, which
#   could be probably used for SubscriptionProducts. This module doesn't support it.
#
from livesettings import *
from django.utils.translation import ugettext_lazy as _

GATEWAY_MODULES = config_get('GATEWAY', 'MODULES')
GATEWAY_MODULES.add_choice(('GATEWAY_SERMEPA', _('SERMEPA (ServiRed) Payment')))

GATEWAY_GROUP = ConfigurationGroup('GATEWAY_SERMEPA', 
    _('SERMEPA (ServiRed) Payment Module Settings'), 
    requires=GATEWAY_MODULES,
    ordering = 101)

config_register_list(
    ModuleValue(GATEWAY_GROUP,
        'MODULE',
        description=_('Implementation module'),
        hidden=True,
        default = 'payment.modules.sermepa'
        ),
    StringValue(GATEWAY_GROUP,
        'KEY',
        description=_("Module key"),
        hidden=True,
        default = 'SERMEPA'
        ),
    StringValue(GATEWAY_GROUP,
        'LABEL',
        description=_('English name for this group on the checkout screens'),
        default = 'Credit Card (via SERMEPA)',
        help_text = _('This will be passed to the translation utility'),
        ordering=10
        ),
    StringValue(GATEWAY_GROUP,
        'URL_BASE',
        description=_('The url base used for constructing urlpatterns which will use this module'),
        default = '^sermepa/',
        ordering=20
        ),
    BooleanValue(
        GATEWAY_GROUP,
        'LIVE',
        description=_("Accept real payments"),
        help_text=_("False if you want to be in test mode"),
        default=False,
        ordering=30
        ),
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_CURRENCY',
        description=_('Currency'),
        default='978',
        choices=[
            ('978', _("EUR (Euro)")),
            ('840', _("USD (US Dollar)")),
            ('826', _("GBP (British Pound)")),
            ('392', _("JPY (Japanese Yen)")),
            ],
        ordering=40
        ),
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_FUC',
        description=_('Merchant FUC'),
        help_text=_('Your FUC code'),
        ordering=50
        ),
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_TITULAR',
        description=_('Merchant title'),
        help_text=_('Description of your shop which will be visible on payment confirmation screen'),
        ordering=60,
        ),

    # signature
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_SIGNATURE_CODE',
        description=_('Signature code'),
        help_text=_('Your secret code used to sign transaction data'),
        ordering=100,
        ),
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_TEST_SIGNATURE_CODE',
        description=_('Test signature code'),
        help_text=_('Your secret code used to sign transaction data in test payments'),
        ordering=200,
        ),
    # terminal
    IntegerValue(
        GATEWAY_GROUP,
        'MERCHANT_TERMINAL',
        description=_('Terminal number'),
        default=1,
        ordering=110
        ),
    IntegerValue(
        GATEWAY_GROUP,
        'MERCHANT_TEST_TERMINAL',
        description=_('Test terminal number'),
        default=1,
        help_text=_('Terminal number used for test payments'),
        ordering=210
        ),
    # post url
    StringValue(
        GATEWAY_GROUP,
        'POST_URL',
        description=_('Post URL'),
        help_text=_('The SERMEPA URL for real transaction posting.'),
        default="https://sis.sermepa.es/sis/realizarPago",
        ordering=120
        ),
    StringValue(
        GATEWAY_GROUP,
        'POST_TEST_URL',
        description=_('Test Post URL'),
        help_text=_('The SERMEPA URL for test transaction posting.'),
        default="https://sis-t.sermepa.es:25443/sis/realizarPago",
        ordering=220
        ),

    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_URL_CALLBACK',
        description=_('Callback URL'),
        help_text=_('Callback URL for on-line notifications about payment progress'),
        default='SERMEPA_satchmo_checkout-notify_callback',
        ordering=300
        ),
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_URL_OK',
        description=_('OK URL'),
        help_text=_('URL for customer to return after successful payment'),
        default='SERMEPA_satchmo_checkout-success',
        ordering=310
        ),
    StringValue(
        GATEWAY_GROUP,
        'MERCHANT_URL_KO',
        description=_('Failure URL'),
        help_text=_('URL for customer to return after payment failure'),
        default='SERMEPA_satchmo_checkout-failure',
        ordering=320
        ),
    BooleanValue(
        GATEWAY_GROUP,
        'SSL',
        description=_("Use SSL for the module checkout pages?"),
        default=False,
        ordering=330
        ),
        
    BooleanValue(GATEWAY_GROUP,
        'EXTRA_LOGGING',
        description=_("Verbose logs"),
        help_text=_("Add extensive logs during post."),
        default=False)
    )
