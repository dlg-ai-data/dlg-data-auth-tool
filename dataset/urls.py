from django.conf.urls import url
from .views import *

app_name = 'dataset'
app_category_name = '데이터세트'

urlpatterns = [
# View

    # Dataset
    url(r'^datasets/$', DatasetsView.as_view(), name='datasets', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '데이터세트 관리'}),
    url(r'^datasets/(?P<id>[0-9]+)/overall/setting/$', DatasetOverallSettingView.as_view(), name='datasets_overall_setting', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '데이터세트 종합 설정'}),

    url(r'^dataset_info_set/$', DatasetSetView.as_view(), name='dataset_set', kwargs={'app_name': app_name}),
    url(r'^dataset_info_display/$', DatasetDisplayView.as_view(), name='dataset_display', kwargs={'app_name': app_name}),
# Ajax

    # Dataset
    url(r'^ajax/dataset/dataset/modify$', modify_dataset, name='modify_dataset'),
    url(r'^ajax/dataset/dataset/register', register_dataset, name='ajax_register_dataset'),
    url(r'^ajax/dataset/dataset/approve$', approve_dataset, name='approve_dataset'),
    url(r'^ajax/dataset/dataset/reject$', reject_dataset, name='reject_dataset'),
    url(r'^ajax/dataset/dataset/label/register', modify_dataset_label, name='modify_dataset_label'),

    url(r'^ajax/dataset_info_set/html/return', dataset_info_set_html_return, name='dataset_info_set_html_return'),
    url(r'^ajax/dataset_info_display/html/return', dataset_info_display_html_return, name='dataset_info_display_html_return'),

]