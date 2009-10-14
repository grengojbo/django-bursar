from livesettings import config_get_group
from payment.views import confirm, payship
    
def pay_ship_info(request):
    return payship.credit_pay_ship_info(request, config_get_group('PAYMENT_TRUSTCOMMERCE'))
    
def confirm_info(request):
    return confirm.payment_confirm_info(request, config_get_group('PAYMENT_TRUSTCOMMERCE'))