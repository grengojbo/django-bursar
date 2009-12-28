from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'example/', 'tests.localsite.views.example', {}),
)
