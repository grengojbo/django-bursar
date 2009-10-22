# this is an extremely simple Satchmo standalone store.

import logging
import os, os.path

LOCAL_DEV = True
DEBUG = True
TEMPLATE_DEBUG = DEBUG

if LOCAL_DEV:
    INTERNAL_IPS = ('127.0.0.1',)

DIRNAME = os.path.dirname(os.path.abspath(__file__))

# for most "normal" projects, you should directly set the SATCHMO_DIRNAME, and skip the trick
_parent = lambda x: os.path.normpath(os.path.join(x, '..'))
SATCHMO_DIRNAME = os.path.join(_parent(_parent(_parent(DIRNAME))), 'satchmo/satchmo')
    
# since we don't have any custom media for this project, lets just use Satchmo's
MEDIA_ROOT = os.path.join(SATCHMO_DIRNAME, 'static/')

gettext_noop = lambda s:s

LANGUAGE_CODE = 'en-us'
LANGUAGES = (
   ('en', gettext_noop('English')),
)

# Only set these if Satchmo is part of another Django project
#These are used when loading the test data
SITE_NAME = "test"
DJANGO_PROJECT = 'tests'
DJANGO_SETTINGS_MODULE = 'tests.settings'

# "simple" doesn't have any custom templates, usually you'd have one here for your site.
TEMPLATE_DIRS = (
    os.path.join(DIRNAME, "templates"),
)

DATABASE_ENGINE = 'sqlite3'
DATABASE_NAME = os.path.join(DIRNAME, 'test.db')
SECRET_KEY = '2d6bad268c243cb7ce1f62634d14f5e7'

##### For Email ########
# If this isn't set in your settings file, you can set these here
#EMAIL_HOST = 'host here'
#EMAIL_PORT = 587
#EMAIL_HOST_USER = 'your user here'
#EMAIL_HOST_PASSWORD = 'your password'
#EMAIL_USE_TLS = True

#These are used when loading the test data
SITE_DOMAIN = "localhost"
SITE_NAME = "Bursar Satchmo Test"

# not suitable for deployment, for testing only, for deployment strongly consider memcached.
CACHE_BACKEND = "locmem:///"
CACHE_TIMEOUT = 60*5
CACHE_PREFIX = "Z"

ACCOUNT_ACTIVATION_DAYS = 7

BURSAR_SETTINGS = {
    'CYBERSOURCE_TEST' : {
         'LIVE': False,
         'MERCHANT_ID' : "zefamily", #Your Cybersource merchant ID - REQUIRED
         'TRANKEY': "Ww/xasElmB5X5FTwYLH/Bnb8dXwNp+/aOogskyIApmZ2j0Ly0zl7fu2rE2Mla/8VyQJAUeS+YZ02M3obf2bhzsrIb7fEsH5ONBm6RXu/H9aXf/XxTvKu9af5Nnsi2a9bGwTl27giGdcpW9oSgX1jUryQ1zCCAnYCAQAwDQYJKob+qet4f8O2yLSzhwEBBQAEggJgMIICXAIBAAKBgQCV+GCZCP21UYPwoFSOFAir49ag658dFJOqAC+6qeZ51Nr9D1jEJLw6WF1hY6kk4BAZ3K9PptvTj3pG7NY3TmrKlmI3RbMKBYIUVrKnku91mBqDxJupmXZRSZ7i+2Zvl8oTHQ==",
         'EXTRA_LOGGING': True
     },
}

#Configure logging
LOGFILE = "satchmo.log"
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S')

#fileLog = logging.FileHandler(os.path.join(DIRNAME, LOGFILE), 'w')
#fileLog.setLevel(logging.DEBUG)
# add the handler to the root logger
#logging.getLogger('').addHandler(fileLog)
logging.getLogger('keyedcache').setLevel(logging.INFO)
logging.getLogger('l10n').setLevel(logging.INFO)
logging.info("Satchmo Started")
