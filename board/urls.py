from django.conf.urls import url
from .views import *

app_name = 'board'
app_category_name = '게시판'

urlpatterns = [
# View
    # Notice
    url(r'^notice/$', NoticeView.as_view(), name='notice', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '공지사항'}),

    # Reference
    url(r'^reference/$', ReferenceView.as_view(), name='reference', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '자료실'}),

# Ajax
    # Notice
    url(r'^ajax/board/notice/register$', notice_register, name='notice_register'),
    url(r'^ajax/board/notice/modify$', notice_modify, name='notice_modify'),
    url(r'^ajax/board/notice/change_status$', notice_change_status, name='notice_change_status'),
    url(r'^ajax/board/notice/delete', notice_delete, name='notice_delete'),

    # Reference
    url(r'^ajax/board/reference/register$', reference_register, name='reference_register'),
    url(r'^ajax/board/reference/modify$', reference_modify, name='reference_modify'),
    url(r'^ajax/board/reference/delete', reference_delete, name='reference_delete'),
]
