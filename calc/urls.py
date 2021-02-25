from django.conf.urls import url
from .views import *


app_name = 'calc'
app_category_name = '정산관리'

urlpatterns = [
    # View
    url(r'^current_state_board/$', CalcCurrentStateBoardView.as_view(), name='current_state_board', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '정산현황'}),

    # AJAX
    url(r'^ajax/calc/current_state_board/excel$', current_state_board_excel, name='current_state_board_excel'),
    url(r'^ajax/calc/current_state_board/confirm_calc_pay', confirm_calc_pay, name='confirm_calc_pay'),
]