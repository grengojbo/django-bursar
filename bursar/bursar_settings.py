"""A central mechanism for shop-wide settings which have defaults.

Repurposed from Sphene Community Tools: http://sct.sphene.net
"""

from django.conf import settings

working_bursar_settings = {
    'STORE_CREDIT_NUMBERS' : False
}

if hasattr(settings, 'BURSAR_SETTINGS'):
    working_bursar_settings.update(settings.BURSAR_SETTINGS)

def add_setting_defaults(newdefaults):
    """
    This method can be used by other applications to define their
    default values.
    
    newdefaults has to be a dictionary containing name -> value of
    the settings.
    """
    global working_bursar_settings
    bursar_settings_defaults.update(newdefaults)

def set_bursar_setting(name, value):
    global working_bursar_settings
    working_bursar_settings[name] = value
    
def get_bursar_setting(name, default_value = None):
    global working_bursar_settings
    return working_bursar_settings.get(name, default_value)

