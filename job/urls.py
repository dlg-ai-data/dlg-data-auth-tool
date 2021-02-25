from django.conf.urls import url
from .views import *


app_name = 'job'
app_category_name = '작업관리'

urlpatterns = [

# Talk

    #어노테이터 관리
    url(r'^talk/management/annotator/$', TalkAnnotatorJobManagement.as_view(), name='talk_annotator_management', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 어노테이터 작업관리'}),
    url(r'^talk/management/annotator/record/$', TalkAnnotatorJobRecord.as_view(), name='talk_annotator_record', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 어노테이터 작업이력'}),
    url(r'^talk/w/provider/$', TalkProvider.as_view(), name='talk_provider', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화조각 제출'}),
    #어노테이터 작업
    url(r'^talk/w/annotator/list$', TalkAnnotatorJobList.as_view(), name='talk_annotator_list', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '대화조각: 리스트'}),
    url(r'^talk/w/annotator/(?P<id>[0-9]+)/annotate$', TalkAnnotatorJob.as_view(), name='talk_annotator', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': '대화조각: 요약'}),
    #관리 ajax
    url(r'^ajax/talk/annotator/collection$', talk_annotator_collection, name='talk_annotator_collection'),
    url(r'^ajax/talk/annotator/inspection$', talk_annotator_inspection, name='talk_annotator_inspection'),
    url(r'^ajax/talk/annotator/management/excel$', talk_annotator_list_excel, name='talk_annotator_list_excel'),
    url(r'^ajax/talk/annotator/record/tbody$', get_talk_annotator_record_tbody_html, name='get_talk_annotator_record_tbody_html'),
    url(r'^ajax/talk/annotator/limit/modify$', talk_annotator_limit_modify, name='talk_annotator_limit_modify'),
    #저작도구 ajax
    url(r'^ajax/annotator/annotate/jobtalksave$', JobTalkSave, name='JobTalkSave'),
    url(r'^ajax/annotator/annotate/jobassignment$', JobAssignment, name='JobAssignment'),
    url(r'^ajax/provider/save$', ProviderSourceSave, name='ProviderSourceSave'),
    # 리뷰어
    url(r'^talk/management/reviewer/$', TalkReviewerJobManagement.as_view(), name='talk_reviewer_management', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 리뷰어 작업관리'}),
    url(r'^talk/management/reviewer/record/$', TalkReviewerJobRecord.as_view(), name='talk_reviewer_record', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 요약리뷰어 작업이력'}),
    url(r'^talk/management/reviewer/source_record/$', TalkSourceReviewerJobRecord.as_view(), name='talk_source_reviewer_record', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 원문리뷰어 작업이력'}),

    url(r'^talk/w/reviewer/source/list$', TalkReviewerSource.as_view(), name='talk_reviewer_source_list', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화원문목록'}),
    url(r'^talk/w/reviewer/source/(?P<id>[0-9]+)/review$', TalkSourceReview.as_view(), name='talk_reviewer_source', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화원문 검수'}),
    url(r'^talk/w/reviewer/review/list$', TalkReviewerJobList.as_view(), name='talk_reviewer_list', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화요약 검수'}),
    url(r'^talk/w/reviewer/review/(?P<id>[0-9]+)/review$', TalkReviewerJob.as_view(), name='talk_reviewer', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화요약 검수'}),
    #ajax
    url(r'^ajax/talk/reviewer/limit/modify$', talk_reviewer_limit_modify, name='talk_reviewer_limit_modify'),
    url(r'^ajax/talk/reviewer/management/excel$', talk_reviewer_list_excel, name='talk_reviewer_list_excel'),
    url(r'^ajax/talk/reviewer/management/tbody$', get_talk_reviewer_management_tbody_html, name='get_talk_reviewer_management_tbody_html'),
    url(r'^ajax/talk/reviewer/record/tbody$', get_talk_reviewer_record_tbody_html, name='get_talk_reviewer_record_tbody_html'),
    #대화 제공자
    url(r'^talk/management/provider/$', TalkProviderManagement.as_view(), name='talk_provider_management', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화제공자 관리'}),
    url(r'^talk/management/provider/record/$', TalkProviderRecord.as_view(), name='talk_provider_record', kwargs={'app_name': app_name, 'app_category_name': app_category_name, 'page_name': 'Talk: 대화제공자 제출이력'}),
    url(r'^ajax/management/provider/limit/modify$', talk_provider_limit_modify, name='talk_provider_limit_modify'),
    url(r'^ajax/management/provider/excel$', talk_provider_list_excel, name='talk_provider_list_excel'),


    # AJAX
    url(r'^ajax/reviewer/review/sourcesave$', JobSourceSave, name='JobSourceSave'),
    url(r'^ajax/reviewer/review/confirm$', JobTalkConfirm, name='JobTalkConfirm'),
    url(r'^ajax/reviewer/review/reject$', JobTalkReject, name='JobTalkReject'),
    url(r'^ajax/reviewer/review/sourceimpossable$', JobSourceImpossable, name='JobSourceImpossable'),
]