from django.conf.urls import url
from .views import *

app_name = 'member'
app_category_name = '회원관리'

urlpatterns = [
    # View
    url(r'^login/$', LoginView.as_view(), name='login', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '로그인'}),
    url(r'^register/$', MemberRegister.as_view(), name='register', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '회원 등록'}),
    url(r'^list/$', MemberList.as_view(), name='list', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '회원 목록'}),
    url(r'^(?P<id>[0-9]+)/modify/$', MemberModify.as_view(), name='modify', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '정보 수정'}),
    url(r'^grade_list/$', GradeListView.as_view(), name='grade_list', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '등급 & 역할 관리'}),

    # Ajax
    url(r'^ajax/join/$', join_member, name='join'),
    url(r'^ajax/member/register$', member_register, name='member_register'),
    url(r'^ajax/member/modify$', member_modify, name='member_modify'),
    url(r'^ajax/member/delete$', member_delete, name='member_delete'),
    url(r'^ajax/member/approve$', member_approve, name='member_approve'),
    url(r'^ajax/member/grade/update', member_grade_update, name='member_grade_update'),

    url(r'^ajax/member/excel$', member_list_excel, name='member_list_excel'),
]

