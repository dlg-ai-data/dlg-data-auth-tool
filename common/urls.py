from django.conf.urls import url
from .views import *

app_name = 'common'
app_category_name = '공통'

urlpatterns = [
    url(r'^file_IsExist/$', file_IsExist, name='file_IsExist'),
    url(r'^filedownload/$', filedownload, name='filedownload'),
    url(r'^pdf_view/(?P<id>[\w\-]+)/$', pdf_file_view, name='pdf_file_view'),
    url(r'^email_is_exist/$', email_is_exist, name='email_is_exist'),
    url(r'^access_restriction/$', check_auth_valid.as_view(), name='check_auth_valid'),
]