import json
import traceback
import urllib.request as urllib
from datetime import datetime

import xlwt
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models.functions import RowNumber
from django.db.models import Subquery, Count, OuterRef, Count, F, Window
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView,TemplateView
from collections import namedtuple
from common.choices import JobStatus, InspectionStatus, MemberJoinSource, MemberGrade_Choice, UseType, JobSourceType, WorkType,MemberRole
from common.templatetags.html_extras import return_start_end_date
from common.utils import get_page_range, convert_dict_to_queryset
from dataset.models import Reviewer, Dataset
from job.forms import TalkJobManagementForm
from job.models import JobTalk, JobTalkSource, JobTalkSummary, JobReviewerHistory
from vaiv.view import LoginRequiredMixin
from django.db.models import Q, Sum
from django.template.loader import render_to_string
from member.models import MemberAddition, MemberGrade, User


class TalkSourceReviewerJobRecord(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/source_record.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkSourceReviewerJobRecord, self).get_context_data(**kwargs)

        searched_reviewer_info_word = self.request.GET.get('reviewer_info', '')
        dataset_ids = self.request.GET.getlist('dataset_ids', None)
        reg_date = self.request.GET.get('reg_date', None)
        searched_reviewer_domain_info_word = self.request.GET.get('domain', '')
        searched_reviewer_category_info_word = self.request.GET.get('category', '')
        searched_reviewer_talk_info_word = self.request.GET.get('talk', '')

        is_selected, is_searched = False, False

        condition = Q()
        condition.add(~Q(inspection_status=InspectionStatus.Initial), Q.AND)
        
        if not self.request.user.is_admin:
            condition.add(Q(reviewer__member_id=self.request.user.id), Q.AND)
            
        if isinstance(reg_date, str) and reg_date != "":
            is_selected = True
            start_job_date, end_job_date = return_start_end_date(reg_date)
            if start_job_date == end_job_date:
                condition.add(Q(reg_date__icontains=start_job_date), Q.AND)
            else:
                condition.add(Q(reg_date__range=[start_job_date, end_job_date]), Q.AND)

        if searched_reviewer_info_word is not None and searched_reviewer_info_word != '':
            is_searched = True
            condition.add(Q(reviewer__member__name__icontains=searched_reviewer_info_word) | Q(
                reviewer__member__tel_no__icontains=searched_reviewer_info_word), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

            

        if searched_reviewer_domain_info_word != "" :
            is_searched = True
            condition.add(Q(domain__contains=searched_reviewer_domain_info_word), Q.AND)
        if searched_reviewer_category_info_word != "" :
            is_searched = True
            condition.add(Q(category__contains=searched_reviewer_category_info_word), Q.AND)
        if searched_reviewer_talk_info_word != "":
            is_searched = True
            condition.add(Q(de_identificated_talk__contains=searched_reviewer_talk_info_word), Q.AND)

        job_talk_qs = JobTalkSource.objects\
            .prefetch_related('dataset').filter(condition).order_by('id', '-reg_date')
        print(job_talk_qs.query)
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(job_talk_qs, 12)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['jobtalksource_list'] = page_list
        context['paginator_range'] = paginator_range
        context['total_count'] = job_talk_qs.count()
        context['dataset_ids'] = dataset_ids
        context['searched_reviewer_info_word'] = searched_reviewer_info_word
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_domain_word'] = searched_reviewer_domain_info_word
        context['searched_category_word'] = searched_reviewer_category_info_word
        context['searched_talk_word'] = searched_reviewer_talk_info_word
        context['page'] = page
        context['job_date'] = reg_date
        context['blank_count'] \
            = 12 - (job_talk_qs.count() - 12 * (page - 1)) if job_talk_qs.count() - 12 * (page - 1) < 12 else 0
        return context

class TalkReviewerJob(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/talk_review.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkReviewerJob, self).get_context_data(**kwargs)

        source_id = self.kwargs.get('id')
        condition = Q()
        condition.add(Q(job_talk_id=source_id), Q.AND)

        jobtalksummary = JobTalkSummary.objects.filter(condition)

        condition = Q()
        condition.add(Q(id=source_id), Q.AND)

        jobtalk = JobTalk.objects.filter(condition)
        context['selected_deidentification_status'] = jobtalk[0].job_talk_source.de_identificated_status
        context['source_detail'] = jobtalk[0].job_talk_source.talk
        context['talker_count'] = jobtalk[0].job_talk_source.talker_count
        context['turn_talk_count'] = jobtalk[0].job_talk_source.turn_talk_count
        context['speechbubble_count'] = jobtalk[0].job_talk_source.speechbubble_count

        if len(jobtalksummary) == 0:
            context['table_count'] = jobtalk[0].job_talk_source.speechbubble_count
        else:
            context['jobtalksummary'] = jobtalksummary
            context['table_count'] = 0
        context['inspection_status'] = jobtalk[0].inspection_status
        context['job_status'] = jobtalk[0].job_status
        context['source_id'] = self.kwargs.get('id')
        context['member_id'] = self.request.user.id
        return context

class TalkReviewerJobList(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/talk_review_list.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkReviewerJobList, self).get_context_data(**kwargs)
        searched_word = self.request.GET.get('word')
        dataset_ids = self.request.GET.getlist('dataset_id', None)
        member_id = self.request.user.id
        inspection_status = self.request.GET.get('inspection_status', 'all')
        search_date = self.request.GET.get('search_date')
        condition = Q()
        condition.add(Q(annotator__isnull=False), Q.AND)
        condition.add(Q(job_status=JobStatus.Complete), Q.AND)

        if not self.request.user.is_admin:
            condition.add(Q(reviewer__member_id=self.request.user.id) | Q(reviewer_id__isnull=True), Q.AND)

        if isinstance(search_date, str) and search_date != "":
            start_join_date, end_join_date = return_start_end_date(search_date)
            if start_join_date == end_join_date:
                condition.add(Q(inspection_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(inspection_date__range=[start_join_date, end_join_date]), Q.AND)
        if inspection_status is not None and inspection_status != "all":
            condition.add(Q(inspection_status=inspection_status), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)
        if searched_word is not None and searched_word != "":
            condition.add(Q(dataset__dataset_name__icontains=searched_word) , Q.AND)

        job_talk_qs = JobTalk.objects.filter(condition) \
            .extra(tables=['dataset'], select={'dataset_name': 'dataset.dataset_name'}
                   , where=['job_talk.dataset_id=dataset.id']) \
            .select_related('job_talk_source') \
            .order_by('inspection_status','job_date')
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(job_talk_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['inspection_status'] = inspection_status
        context['search_date'] = search_date
        context['jobtalk_list'] = page_list
        context['paginator_range'] = paginator_range
        context['total_count'] = job_talk_qs.count()
        context['dataset_ids'] = dataset_ids
        context['searched_word'] = searched_word
        context['page'] = page
        context['blank_count'] \
            = 15 - (job_talk_qs.count() - 15 * (page - 1)) if job_talk_qs.count() - 15 * (page - 1) < 15 else 0
        return context




def JobTalkConfirm(request):
    if request.is_ajax():
        tasks = request.GET.getlist('list[]')
        source_id = request.GET.get('source_id')
        member_id = request.GET.get('member_id')
        try:
            role_code = User.objects.get(id=member_id, role_code=MemberRole.SummaryReviewer)
        except Exception as e:
            return JsonResponse({'result': False, 'msg': '요약검수자로 등록된 회원이 아닙니다.'})
        try:

            reviewer = Reviewer.objects.get(member_id=member_id, valid_yn=UseType.Y)

            limit_yn = reviewer.limit_yn
            limit_count = reviewer.limit_count
            check_datetime = datetime.now()
            current_submit_count = JobTalk.objects \
                .filter(inspection_date__year=check_datetime.year,
                        inspection_date__month=check_datetime.month,
                        inspection_date__day=check_datetime.day,
                        inspection_status__in=[InspectionStatus.Complete, InspectionStatus.Reject],
                        reviewer=reviewer)
            if limit_yn == UseType.Y:
                return JsonResponse({'result': False, 'msg': '작업제한 상태입니다.'})

            if limit_count > 0 and (limit_count <= len(current_submit_count)):
                return JsonResponse({'result': False, 'msg': '일일작업량을 초과하였습니다.'})

            with transaction.atomic():
                jobtalk = JobTalk.objects.get(id=source_id)

                if jobtalk.reviewer is not None and int(jobtalk.reviewer.member_id) != int(member_id):
                    return JsonResponse({'result': False, 'msg': '다른 리뷰어가 작업한 목록입니다.', 'type': 'not'})
                if jobtalk.reviewer is None:
                    condition = Q()
                    condition.add(Q(member_id=member_id), Q.AND)
                    condition.add(Q(dataset_id=jobtalk.dataset_id), Q.AND)
                    jobtalk.reviewer = Reviewer.objects.get(condition)
                jts_del = JobTalkSummary.objects.filter(job_talk=source_id)
                jts_del.delete()
                for i in range(0, len(tasks)):
                    json_val = json.loads(tasks[i])
                    # {"rowIndex":1,"talker":"","summary":"","intent":"","qatype":"BA01"}

                    jobtalksummary = JobTalkSummary()
                    jobtalksummary.job_talk_id = source_id
                    jobtalksummary.talker = json_val['talker']
                    jobtalksummary.talk_summary = json_val['summary']
                    jobtalksummary.seq = json_val['rowIndex']
                    jobtalksummary.qa_type = json_val['qatype']
                    jobtalksummary.intent = json_val['intent']
                    jobtalksummary.save()

                jobtalk.inspection_status = InspectionStatus.Complete
                jobtalk.inspection_date = datetime.now()
                jobtalk.save()

                JobReviewerHistory.objects.create(job_id=source_id, reviewer_id=jobtalk.reviewer.id,
                                                    job_source_type=JobSourceType.TalkInspection,
                                                    work_type=WorkType.Update,
                                                    work_text='검수완료',
                                                    job_status=JobStatus.Complete,
                                                    inspection_status=InspectionStatus.Complete)

                #어ㅏ노테이터 정산 / 요약 리뷰어 정산
                return JsonResponse({'result': True, 'msg': '승인되었습니다.', 'type': 'save'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def JobTalkReject(request):
    if request.is_ajax():
        msg = request.GET.get('msg')
        source_id = request.GET.get('source_id')
        member_id = request.GET.get('member_id')
        try:
            role_code = User.objects.get(id=member_id, role_code__in=[MemberRole.Reviewer, MemberRole.SummaryReviewer])
        except Exception as e:
            return JsonResponse({'result': False, 'error': '검수자로 등록된 회원이 아닙니다.'})
        try:
            reviewer = Reviewer.objects.get(member_id=member_id, valid_yn=UseType.Y)

            limit_yn = reviewer.limit_yn
            limit_count = reviewer.limit_count
            check_datetime = datetime.now()
            current_submit_count = JobTalk.objects \
                .filter(inspection_date__year=check_datetime.year,
                        inspection_date__month=check_datetime.month,
                        inspection_date__day=check_datetime.day,
                        inspection_status__in=[InspectionStatus.Complete, InspectionStatus.Reject],
                        reviewer=reviewer)
            if limit_yn == UseType.Y:
                return JsonResponse({'result': False, 'msg': '작업제한 상태입니다.'})

            if limit_count > 0 and (limit_count <= len(current_submit_count)):
                return JsonResponse({'result': False, 'msg': '일일작업량을 초과하였습니다.'})
            with transaction.atomic():
                jobtalk = JobTalk.objects.get(id=source_id)

                if jobtalk.reviewer is not None and int(jobtalk.reviewer.member_id) != int(member_id):
                    return JsonResponse({'result': False, 'msg': '다른 리뷰어가 작업한 목록입니다.', 'type': 'not'})
                if jobtalk.reviewer is None:
                    condition = Q()
                    condition.add(Q(member_id=member_id), Q.AND)
                    condition.add(Q(dataset_id=jobtalk.dataset_id), Q.AND)
                    jobtalk.reviewer = Reviewer.objects.get(condition)

                jobtalk.inspection_status = 'AL02'
                jobtalk.inspection_date = datetime.now()
                jobtalk.reject_msg = msg
                jobtalk.reject_count = jobtalk.reject_count+1
                jobtalk.save()

                JobReviewerHistory.objects.create(job_id=source_id, reviewer_id=jobtalk.reviewer.id,
                                                  job_source_type=JobSourceType.TalkInspection,
                                                  work_type=WorkType.Update,
                                                  work_text='반려',
                                                  job_status=JobStatus.Complete,
                                                  inspection_status=InspectionStatus.Reject)
                return JsonResponse({'result': True, 'msg': '반려되었습니다.', 'type': 'save'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})




class TalkReviewerJobManagement(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/management.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkReviewerJobManagement, self).get_context_data(**kwargs)

        context['selected_grade'] = self.request.GET.get('grade', 'all')
        context['searched_word'] = self.request.GET.get('word', None)
        context['dataset_ids'] = self.request.GET.getlist('dataset_ids', 'all')
        context['selected_join_source'] = self.request.GET.get('join_source', 'all')
        context['join_date'] = self.request.GET.get('join_date', None)
        context['modf_date'] = self.request.GET.get('modf_date', None)
        context['inspection_date'] = self.request.GET.get('inspection_date', None)
        context['selected_limit_yn'] = self.request.GET.get('limit_yn', None)
        return context

class TalkReviewerSource(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/talk_source_list.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkReviewerSource, self).get_context_data(**kwargs)

        inspection_status = self.request.GET.get('inspection_status', 'all')

        searched_word = self.request.GET.get('word')
        dataset_ids = self.request.GET.getlist('dataset_ids', None)
        search_date = self.request.GET.get('search_date', None)

        member_id = self.request.user.id
        condition = Q()
        if isinstance(search_date, str) and search_date != "":
            start_join_date, end_join_date = return_start_end_date(search_date)
            if start_join_date == end_join_date:
                condition.add(Q(inspection_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(inspection_date__range=[start_join_date, end_join_date]), Q.AND)
        if inspection_status is not None and inspection_status != "all":
            condition.add(Q(inspection_status=inspection_status), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if searched_word is not None and searched_word != "":
            condition.add(Q(dataset__dataset_name__icontains=searched_word) , Q.AND)

        condition.add(Q(reviewer__member_id=member_id)|Q(reviewer__isnull=True), Q.AND)

        job_talk_source_qs = JobTalkSource.objects.filter(condition).select_related('dataset').order_by('inspection_status')
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(job_talk_source_qs, 12)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['jobTalksource_list'] = page_list
        context['inspection_status'] = inspection_status
        context['search_date'] = search_date
        context['paginator_range'] = paginator_range
        context['total_count'] = job_talk_source_qs.count()
        context['dataset_ids'] = dataset_ids
        context['searched_word'] = searched_word
        context['page'] = page
        context['search_date'] = search_date
        context['blank_count'] \
            = 12 - (job_talk_source_qs.count() - 12 * (page - 1)) if job_talk_source_qs.count() - 12 * (page - 1) < 12 else 0
        return context


class TalkSourceReview(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/talk_source_review.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkSourceReview, self).get_context_data(**kwargs)
        member_id = self.request.user.id
        source_id = self.kwargs.get('id')

        context['member_id'] = member_id
        context['source_detail'] = JobTalkSource.objects.get(id=source_id)
        return context


def JobSourceSave(request):
    if request.is_ajax():
        saveData = request.GET
        data = json.loads(saveData['data'])
        source_id = data['source_id']
        member_id = data['member_id']
        isTmp =  data['isTmp']
        try:
            role_code = User.objects.get(id=member_id, role_code=MemberRole.Reviewer)
        except Exception as e:
            return JsonResponse({'result': False, 'msg': '원문검수자로 등록된 회원이 아닙니다.'})
        try:
            reviewer = Reviewer.objects.get(member_id=member_id, valid_yn=UseType.Y)

            limit_yn = reviewer.limit_yn
            limit_count = reviewer.limit_count
            check_datetime = datetime.now()
            current_submit_count = JobTalkSource.objects \
                .filter(inspection_date__year=check_datetime.year,
                        inspection_date__month=check_datetime.month,
                        inspection_date__day=check_datetime.day,
                        inspection_status__in=[InspectionStatus.Complete, InspectionStatus.Reject],
                        reviewer=reviewer)
            if limit_yn == UseType.Y:
                return JsonResponse({'result': False, 'msg': '작업제한 상태입니다.'})

            if limit_count > 0 and (limit_count <= len(current_submit_count)):
                return JsonResponse({'result': False, 'msg': '일일작업량을 초과하였습니다.'})

            with transaction.atomic():
                jobtalkSrc = JobTalkSource.objects.get(id=source_id)

                if jobtalkSrc.reviewer is not None and int(jobtalkSrc.reviewer.member_id)!=int(member_id):
                    return JsonResponse({'result': False, 'msg': '다른 리뷰어가 작업한 목록입니다.', 'type': 'not'})
                if jobtalkSrc.reviewer is None:
                    condition = Q()
                    condition.add(Q(member_id=member_id), Q.AND)
                    condition.add(Q(dataset_id=jobtalkSrc.dataset_id), Q.AND)
                    try:
                        jobtalkSrc.reviewer = Reviewer.objects.get(condition)
                    except Exception as e:
                        if str(e) == 'Reviewer matching query does not exist.':
                            return JsonResponse({'result': False, 'msg' : '검수자로 등록되어 있지 않습니다.', 'type': 'not'})
                        else:
                            raise e
                if isTmp == 'True':

                    jobtalkSrc.de_identificated_talk = data['de_identificated_talk']
                    jobtalkSrc.de_identificated_status = data['de_identificated_status']
                    jobtalkSrc.speechbubble_count = data['speechbubble_count']
                    jobtalkSrc.turn_talk_count = data['turn_talk_count']
                    jobtalkSrc.talker_count = data['talker_count']
                    jobtalkSrc.domain = data['domain']
                    jobtalkSrc.category = data['category']
                    jobtalkSrc.inspection_status = InspectionStatus.Inspection
                    jobtalkSrc.mod_date = datetime.now()
                    jobtalkSrc.save()

                    JobReviewerHistory.objects.update_or_create(job_id=source_id, reviewer_id=jobtalkSrc.reviewer.id,
                                                                defaults={
                                                                    'job_source_type': JobSourceType.SourceInspection,
                                                                    'work_type': WorkType.Create,
                                                                    'work_text': '원문 검수 중간저장',
                                                                    'job_status': JobStatus.Writing,
                                                                    'inspection_status': InspectionStatus.Initial})
                    return JsonResponse({'result': True, 'msg': '임시 저장되었습니다.', 'type': 'tmp'})
                else:

                    jobtalkSrc.de_identificated_talk = data['de_identificated_talk']
                    jobtalkSrc.de_identificated_status = data['de_identificated_status']
                    jobtalkSrc.speechbubble_count = data['speechbubble_count']
                    jobtalkSrc.turn_talk_count = data['turn_talk_count']
                    jobtalkSrc.talker_count = data['talker_count']
                    jobtalkSrc.domain = data['domain']
                    jobtalkSrc.category = data['category']
                    jobtalkSrc.mod_date = datetime.now()
                    jobtalkSrc.inspection_date = datetime.now()
                    jobtalkSrc.inspection_status = InspectionStatus.Complete
                    jobtalkSrc.save()

                    JobReviewerHistory.objects.create(job_id=source_id, reviewer_id=jobtalkSrc.reviewer.id,
                                                      job_source_type=JobSourceType.SourceInspection,
                                                      work_type=WorkType.Update,
                                                      work_text='검수완료',
                                                      job_status=JobStatus.Complete,
                                                      inspection_status=InspectionStatus.Complete)

                    JobTalk.objects.create(job_status=JobStatus.Initial, inspection_status=InspectionStatus.Initial,
                                           dataset_id=jobtalkSrc.dataset_id, job_talk_source_id=source_id)
                    # 원문 검수 대화제공자 정산 / 원문 리뷰어 정산

                    return JsonResponse({'result': True, 'msg': '검수되었습니다.', 'type': 'save'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'msg': str(e)})
    else:
        return JsonResponse({'result': False, 'msg': 'is ajax only Method'})


def JobSourceImpossable(request):
    if request.is_ajax():
        msg = request.GET.get('msg')
        source_id = request.GET.get('source_id')
        member_id = request.GET.get('member_id')
        try:
            role_code = User.objects.get(id=member_id, role_code__in=[MemberRole.Reviewer, MemberRole.SummaryReviewer])
        except Exception as e:
            return JsonResponse({'result': False, 'error': '검수자로 등록된 회원이 아닙니다.'})
        try:
            with transaction.atomic():
                jobtalkSrc = JobTalkSource.objects.get(id=source_id)
                if jobtalkSrc.reviewer is not None and int(jobtalkSrc.reviewer.member_id) != int(member_id):
                    return JsonResponse({'result': False, 'msg': '다른 리뷰어가 작업한 목록입니다.', 'type': 'not'})
                if jobtalkSrc.reviewer is None:
                    condition = Q()
                    condition.add(Q(member_id=member_id), Q.AND)
                    condition.add(Q(dataset_id=jobtalkSrc.dataset_id), Q.AND)
                    try:
                        jobtalkSrc.reviewer = Reviewer.objects.get(condition)
                    except Exception as e:
                        if str(e) == 'Reviewer matching query does not exist.':
                            return JsonResponse({'result': False, 'msg' : '검수자로 등록되어 있지 않습니다.', 'type': 'not'})
                        else:
                            raise e

                jobtalkSrc.inspection_status = InspectionStatus.Reject
                jobtalkSrc.mod_date = datetime.now()
                jobtalkSrc.inspection_date = datetime.now()
                jobtalkSrc.reject_msg = msg

                jobtalkSrc.save()

                JobReviewerHistory.objects.create(job_id=source_id, reviewer_id=jobtalkSrc.reviewer.id,
                                                  job_source_type=JobSourceType.SourceInspection,
                                                  work_type=WorkType.Delete,
                                                  work_text=msg,
                                                  job_status=JobStatus.Exclude,
                                                  inspection_status=InspectionStatus.Reject)
                return JsonResponse({'result': True, 'msg': '반려되었습니다.', 'type': 'save'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


class TalkReviewerJobRecord(LoginRequiredMixin, FormView):
    template_name = 'job/talk/reviewer/record.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkReviewerJobRecord, self).get_context_data(**kwargs)
        return context

@csrf_exempt
def talk_reviewer_limit_modify(request):
    job_limit_count, job_limit_yn, reviewer_id, new_data, to_be_changed_items = None, None, None, None, None

    if request.method == "GET":
        reviewer_id = request.GET.get('reviewer_id', None)
        job_limit_count = request.GET.get('job_limit_count', None)
        job_limit_yn = request.GET.get('job_limit_yn', None)
        new_data = [job_limit_count, job_limit_yn]
    else:
        to_be_changed_items = json.loads(request.POST['to_be_changed_items'])

    if request.is_ajax():
        result = True
        error = ""
        try:
            with transaction.atomic():
                if not to_be_changed_items:
                    reviewer = Reviewer.objects.get(id=reviewer_id)
                    reviewer.limit_yn = job_limit_yn
                    reviewer.limit_count = job_limit_count
                    reviewer.save()
                else:
                    for item in to_be_changed_items:
                        reviewer = Reviewer.objects.get(id=item['reviewer_id'])
                        reviewer.limit_yn = item['job_limit_yn']
                        reviewer.limit_count = item['job_limit_count']
                        reviewer.save()
                return JsonResponse({'result': result, 'error': error, 'new_data': new_data})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def talk_reviewer_list_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % urllib.quote(
        '리뷰어 작업관리 목록.xls'.encode('utf-8'))
    try:
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('리뷰어 작업관리 목록')

        row_num = 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        ws.write_merge(0, 0, 2, 8, '리뷰어 정보', xlwt.easyxf('pattern: pattern solid, fore_color yellow'))
        ws.write_merge(0, 0, 9, 13, '검수 집계 (개 / %)', xlwt.easyxf('pattern: pattern solid, fore_color light_green'))
        columns = ['데이터세트명','리뷰유형', '이메일', '이름', '연락처', '등급', '가입경로',
                   '작업제한량(일일)(0:무제한)', '작업제한여부(Y:작업불가)',
                   '전체건수',
                   '승인', '', '반려(누적)', '',]

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        dataset_ids = request.GET.getlist('dataset_id', None)
        join_date = request.GET.get('join_date', None)
        modf_date = request.GET.get('modf_date', None)
        inspection_date = request.GET.get('inspection_date', None)
        limit_yn = request.GET.get('limit_yn', None)
        selected_join_source = request.GET.get('join_source', None)
        searched_word = request.GET.get('searched_word', None)
        selected_grade =request.GET.get('selected_grade', None)

        sort_criterion = request.GET.get('sort_criterion', 'id')
        upDown = request.GET.get('upDown', '-')

        condition = Q(
            reviewer__member__membergrade2member__valid_yn=UseType.Y)  # Q(reviewer__member__membergrade2member__valid_yn=UseType.Y)
        condition.add(Q(reviewer__member__secession_yn=UseType.N), Q.AND)
        # condition.add(Q(reviewer__member__membergrade2member__valid_yn=UseType.Y), Q.AND)

        condition2 = Q()
        condition2.add(Q(reviewer__reviewer_id=OuterRef('id')), Q.AND)
        condition2.add(Q(reviewer__reviewer__isnull=False), Q.AND)

        if isinstance(join_date, str) and join_date != "":
            is_selected = True
            start_join_date, end_join_date = return_start_end_date(join_date)
            if start_join_date == end_join_date:
                condition.add(Q(reviewer__member__join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(reviewer__member__join_date__range=[start_join_date, end_join_date]), Q.AND)

        if isinstance(modf_date, str) and modf_date != "":
            is_selected = True
            start_modf_date, end_modf_date = return_start_end_date(modf_date)
            if start_modf_date == end_modf_date:
                condition.add(Q(reviewer__member__modf_date__icontains=start_modf_date), Q.AND)
            else:
                condition.add(Q(reviewer__member__modf_date__range=[start_modf_date, end_modf_date]), Q.AND)

        if isinstance(inspection_date, str) and inspection_date != "":
            is_selected = True
            start_inspection_date, end_inspection_date = return_start_end_date(inspection_date)
            if start_inspection_date == end_inspection_date:
                condition2.add(Q(reg_date__icontains=start_inspection_date), Q.AND)
            else:
                condition2.add(Q(reg_date__range=[start_inspection_date, end_inspection_date]), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(reviewer__dataset__id__in=dataset_ids), Q.AND)

        if selected_join_source is not None and selected_join_source != 'all':
            is_selected = True
            condition.add(Q(reviewer__member__memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if limit_yn is not None and limit_yn != 'all':
            is_selected = True
            condition.add(Q(reviewer__limit_yn=limit_yn), Q.AND)

        if searched_word is not None and searched_word != '':
            is_searched = True
            condition.add(
                Q(reviewer__member__name__icontains=searched_word) | Q(member__email__icontains=searched_word),
                Q.AND)
        if selected_grade is not None and selected_grade != 'all':
            is_selected = True
            condition.add(Q(reviewer__member__membergrade2member__grade_code=selected_grade), Q.AND)

        sort_condition = ""

        if upDown == '-':
            sort_condition += '-'

        if sort_criterion == 'id':
            sort_condition += 'id'
        elif sort_criterion == 'dataset_name':
            sort_condition += "dataset__dataset_name"
        elif sort_criterion == 'total_count':
            sort_condition += "total_count"
        elif sort_criterion == 'limit_count':
            sort_condition += "limit_count"
        elif sort_criterion == 'email':
            sort_condition += "member__email"
        elif sort_criterion == 'name':
            sort_condition += "member__name"
        elif sort_criterion == 'tel_no':
            sort_condition += "member__tel_no"
        elif sort_criterion == 'member_grade':
            sort_condition += "member__membergrade2user__grade_code"
        elif sort_criterion == 'join_source':
            sort_condition += "member__memberaddition2member__member_join_source"
        elif sort_criterion == 'initial_count':
            sort_condition += "inspection_status_initial_count"
        elif sort_criterion == 'complete_count':
            sort_condition += "inspection_status_complete_count"
        elif sort_criterion == 'reject_count':
            sort_condition += "inspection_status_reject_count"
        elif sort_criterion == 'accumulated_reject_count':
            sort_condition += "accumulated_reject_count"

        total_qs = JobReviewerHistory.objects.values('job_source_type').annotate(total_count=Count('id')).order_by(
            'job_source_type').filter(job_source_type=OuterRef('job_source_type'),
                                      reviewer_id=OuterRef('reviewer_id')).values('total_count').filter(
            ~Q(inspection_status=InspectionStatus.Initial)) \
            .filter(condition)

        complete_qs = JobReviewerHistory.objects.values('job_source_type').annotate(
            complete_count=Count('id')).order_by('job_source_type').filter(
            inspection_status=InspectionStatus.Complete, job_source_type=OuterRef('job_source_type'),
            reviewer_id=OuterRef('reviewer_id')).values(
            'complete_count') \
            .filter(condition)
        reject_qs = JobReviewerHistory.objects.values('job_source_type').annotate(
            reject_count=Count('id')).order_by('job_source_type').filter(inspection_status=InspectionStatus.Reject,
                                                                         reviewer_id=OuterRef('reviewer_id'),
                                                                         job_source_type=OuterRef(
                                                                             'job_source_type')).values(
            'reject_count') \
            .filter(condition)

        rows = JobReviewerHistory.objects \
            .filter(condition) \
            .values(
            dataset_name=F('reviewer__dataset__dataset_name'), job_source_type_=F('job_source_type'),
            email=F('reviewer__member__email'),user_name=F('reviewer__member__name'),
            tel_no=F('reviewer__member__tel_no'), grade_code=F('reviewer__member__membergrade2member__grade_code'),member_join_source=F('reviewer__member__memberaddition2member__member_join_source'),
            limit_count=F('reviewer__limit_count'),limit_yn=F('reviewer__limit_yn')
        ) \
            .annotate(total_count=Subquery(total_qs)) \
            .annotate(inspection_status_complete_count=Subquery(complete_qs)) \
            .annotate(accumulated_reject_count=Subquery(reject_qs)) \
            .distinct()

        data_count = rows.count()
        plus = 0
        for row in rows:
            row_num += 1
            total = None
            for col_num, key in enumerate(row):
                output_data = row[key]
                if col_num == 1:
                    output_data = JobSourceType.get_value(output_data)
                if col_num == 5:
                    output_data = MemberGrade_Choice.get_value(output_data)
                if col_num == 6:
                    output_data = MemberJoinSource.get_value(output_data)
                if col_num == 9:
                    total = output_data
                    output_data = '0' if output_data is None else str(output_data)
                if col_num == 10 or col_num == 11:
                    count = 0
                    if total is not None and output_data is not None:
                        count = int(output_data)
                    ws.write(row_num, col_num + plus, count, font_style)
                    if count == 0:
                        percent = '0%'
                    else:
                        if total is None or count is None:
                            percent = '0%'
                        else:
                            percent = str(format(count / int(total) * 100, "2.1f")) + '%'
                    ws.write(row_num, col_num + plus + 1, percent, font_style)
                    plus += 1
                    continue
                if col_num in (1,2):
                    continue
                ws.write(row_num, col_num + plus, output_data, font_style)
            plus = 0

        wb.save(response)
    except Exception as e:
        traceback.print_exc()
        return response

    return response


class ReviewerManagementTableTrView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super(ReviewerManagementTableTrView, self).get_context_data(**kwargs)
        dataset_ids = self.kwargs.get('dataset_id', 'all')
        join_date = self.kwargs.get('join_date', None)
        modf_date = self.kwargs.get('modf_date', None)
        limit_yn = self.kwargs.get('limit_yn', 'all')
        selected_join_source = self.kwargs.get('join_source', 'all')
        inspection_date = self.kwargs.get('inspection_date', None)
        selected_grade = self.kwargs.get('grade', 'all')
        searched_word = self.kwargs.get('word', '')

        sort_criterion = self.kwargs.get('sort_criterion', 'id')
        upDown = self.kwargs.get('upDown', '-')
        page = self.kwargs.get('page')

        is_selected, is_searched = False, False

        condition = Q(reviewer__member__membergrade2member__valid_yn=UseType.Y)# Q(reviewer__member__membergrade2member__valid_yn=UseType.Y)
        condition.add(Q(reviewer__member__secession_yn=UseType.N), Q.AND)
        # condition.add(Q(reviewer__member__membergrade2member__valid_yn=UseType.Y), Q.AND)

        condition2 = Q()
        condition2.add(Q(reviewer__reviewer_id=OuterRef('id')), Q.AND)
        condition2.add(Q(reviewer__reviewer__isnull=False), Q.AND)

        if isinstance(join_date, str) and join_date != "":
            is_selected = True
            start_join_date, end_join_date = return_start_end_date(join_date)
            if start_join_date == end_join_date:
                condition.add(Q(reviewer__member__join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(reviewer__member__join_date__range=[start_join_date, end_join_date]), Q.AND)

        if isinstance(modf_date, str) and modf_date != "":
            is_selected = True
            start_modf_date, end_modf_date = return_start_end_date(modf_date)
            if start_modf_date == end_modf_date:
                condition.add(Q(reviewer__member__modf_date__icontains=start_modf_date), Q.AND)
            else:
                condition.add(Q(reviewer__member__modf_date__range=[start_modf_date, end_modf_date]), Q.AND)

        if isinstance(inspection_date, str) and inspection_date != "":
            is_selected = True
            start_inspection_date, end_inspection_date = return_start_end_date(inspection_date)
            if start_inspection_date == end_inspection_date:
                condition2.add(Q(reg_date__icontains=start_inspection_date), Q.AND)
            else:
                condition2.add(Q(reg_date__range=[start_inspection_date, end_inspection_date]), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(reviewer__dataset__id__in=dataset_ids), Q.AND)

        if selected_join_source is not None and selected_join_source != 'all':
            is_selected = True
            condition.add(Q(reviewer__member__memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if limit_yn is not None and limit_yn != 'all':
            is_selected = True
            condition.add(Q(reviewer__limit_yn=limit_yn), Q.AND)

        if searched_word is not None and searched_word != '':
            is_searched = True
            condition.add(Q(reviewer__member__name__icontains=searched_word) | Q(member__email__icontains=searched_word),
                          Q.AND)
        if selected_grade is not None and selected_grade != 'all':
            is_selected = True
            condition.add(Q(reviewer__member__membergrade2member__grade_code=selected_grade), Q.AND)

        # sorting 조건 만드는 곳
        sort_condition = ""

        if upDown == '-':
            sort_condition += '-'

        if sort_criterion == 'id':
            sort_condition += 'id'
        elif sort_criterion == 'dataset_name':
            sort_condition += "dataset__dataset_name"
        elif sort_criterion == 'total_count':
            sort_condition += "total_count"
        elif sort_criterion == 'limit_count':
            sort_condition += "limit_count"
        elif sort_criterion == 'email':
            sort_condition += "member__email"
        elif sort_criterion == 'name':
            sort_condition += "member__name"
        elif sort_criterion == 'tel_no':
            sort_condition += "member__tel_no"
        elif sort_criterion == 'member_grade':
            sort_condition += "member__membergrade2user__grade_code"
        elif sort_criterion == 'join_source':
            sort_condition += "member__memberaddition2member__member_join_source"
        elif sort_criterion == 'initial_count':
            sort_condition += "inspection_status_initial_count"
        elif sort_criterion == 'complete_count':
            sort_condition += "inspection_status_complete_count"
        elif sort_criterion == 'reject_count':
            sort_condition += "inspection_status_reject_count"
        elif sort_criterion == 'accumulated_reject_count':
            sort_condition += "accumulated_reject_count"

        total_qs = JobReviewerHistory.objects.values('job_source_type').annotate(total_count=Count('id')).order_by(
            'job_source_type').filter(job_source_type=OuterRef('job_source_type'), reviewer_id=OuterRef('reviewer_id')).values('total_count').filter(~Q(inspection_status=InspectionStatus.Initial))\
            .filter(condition)

        source_count_qs = JobReviewerHistory.objects.values('reviewer_id').annotate(source_count=Count('job_source_type', distinct=True))\
            .order_by('reviewer_id').filter(reviewer_id=OuterRef('reviewer_id')).values('source_count').filter(~Q(inspection_status=InspectionStatus.Initial))\
            .filter(condition)

        complete_qs = JobReviewerHistory.objects.values('job_source_type').annotate(
            complete_count=Count('id')).order_by('job_source_type').filter(
            inspection_status=InspectionStatus.Complete, job_source_type=OuterRef('job_source_type'), reviewer_id=OuterRef('reviewer_id')).values(
            'complete_count')\
            .filter(condition)
        reject_qs = JobReviewerHistory.objects.values('job_source_type').annotate(
            reject_count=Count('id')).order_by('job_source_type').filter(inspection_status=InspectionStatus.Reject, reviewer_id=OuterRef('reviewer_id'),
                                                                         job_source_type=OuterRef(
                                                                             'job_source_type')).values(
            'reject_count')\
            .filter(condition)

        qs = JobReviewerHistory.objects\
            .filter(condition) \
            .values(
            'reviewer_id', 'job_source_type', dataset_name=F('reviewer__dataset__dataset_name'),
            user_name=F('reviewer__member__name'), email=F('reviewer__member__email'),
            tel_no=F('reviewer__member__tel_no'), grade_code=F('reviewer__member__membergrade2member__grade_code'),
            member_join_source=F('reviewer__member__memberaddition2member__member_join_source'),
            limit_yn=F('reviewer__limit_yn'), limit_count=F('reviewer__limit_count'),
            member_id=F('reviewer__member_id')
        ) \
            .annotate(total_count=Subquery(total_qs)) \
            .annotate(inspection_status_complete_count=Subquery(complete_qs)) \
            .annotate(accumulated_reject_count=Subquery(reject_qs))\
            .annotate(source_count=Subquery(source_count_qs))\
            .distinct()
        total_count = qs.count()
        result = []
        for item in convert_dict_to_queryset('item', qs):
            result.append(item._replace(job_source_type=JobSourceType.__call__(item.job_source_type).label) \
                          ._replace(member_join_source=MemberJoinSource.get_value(item.member_join_source)))

        page = int(page)
        paginator = Paginator(result, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['items'] = page_list
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['total_count'] = qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['selected_grade'] = selected_grade
        context['dataset_ids'] = dataset_ids
        context['join_date'] = join_date
        context['modf_date'] = modf_date
        context['inspection_date'] = inspection_date
        context['selected_limit_yn'] = limit_yn
        context['selected_join_source'] = selected_join_source
        context['page'] = page
        context['total_count'] = total_count
        context['blank_count'] \
            = 15 - (qs.count() - 15 * (page - 1)) if qs.count() - 15 * (page - 1) < 15 else 0
        context['sort_criterion'] = sort_criterion
        context['upDown'] = upDown
        return context

@csrf_exempt
def get_talk_reviewer_management_tbody_html(request):
    if request.is_ajax():
        dataset_ids = request.POST.getlist('dataset_ids[]', None)
        join_source = request.POST.get('join_source', None)
        join_date = request.POST.get('join_date', None)
        inspection_date = request.POST.get('inspection_date', None)
        reviewer_info = request.POST.get('reviewer_info',None)
        limit_yn = request.POST.get('limit_yn', None)
        member_grade = request.POST.get('grade', 'all')
        page = request.POST.get('page', 1)

        if not dataset_ids:
            dataset_ids = ['all']
        context = ReviewerManagementTableTrView(
            kwargs={'dataset_id': dataset_ids, 'join_source': join_source, 'join_date': join_date, 'inspection_date': inspection_date, 'reviewer_info': reviewer_info, 'limit_yn': limit_yn,'grade':member_grade, 'page': page}).get_context_data()


        html = render_to_string('partials/reviewer_management_table_tr.html', context)
        pagenation_html = render_to_string('paginnation.html', context)

        # dataset_names = context['dataset_names']

        return JsonResponse(
            {'result': True, 'html': html, 'pagenation_html': pagenation_html, 'total_count': context['total_count']})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})



class ReviewerRecordTableTrView(LoginRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super(ReviewerRecordTableTrView, self).get_context_data(**kwargs)

        dataset_ids = self.kwargs.get('dataset_ids', None)
        searched_annotator_info_word = self.kwargs.get('annotator_info', '')
        searched_reviewer_info_word = self.kwargs.get('reviewer_info', '')
        selected_inspectionStatus = self.kwargs.get('inspectionStatus', None)
        job_date = self.kwargs.get('job_date', None)
        inspection_date = self.kwargs.get('inspection_date', None)
        searched_domain_word = self.kwargs.get('domain', '')
        searched_category_word = self.kwargs.get('category', '')
        searched_talk_word = self.kwargs.get('talk', '')
        searched_intent_word = self.kwargs.get('intent', '')
        selected_reviewer_grade = self.kwargs.get('reviewer_grade', None)
        page = self.kwargs.get('page')

        # 앞뒤 공백 제거
        if searched_annotator_info_word is not None:
            searched_annotator_info_word = searched_annotator_info_word.strip()
        if searched_reviewer_info_word is not None:
            searched_reviewer_info_word = searched_reviewer_info_word.strip()
        if searched_domain_word is not None:
            searched_domain_word = searched_domain_word.strip()
        if searched_category_word is not None:
            searched_category_word = searched_category_word.strip()
        if searched_talk_word is not None:
            searched_talk_word = searched_talk_word.strip()
        if searched_intent_word is not None:
            searched_intent_word = searched_intent_word.strip()

        condition = Q()
        user = self.kwargs.get('user')
        if not user.is_admin:
            condition.add(Q(job_talk__reviewer__member__id=user.id), Q.AND)
        condition2 = Q()
        condition.add(Q(job_talk__inspection_status__in=[InspectionStatus.Complete, InspectionStatus.Reject]), Q.AND)
        condition.add(Q(job_talk__reviewer__member__membergrade2member__valid_yn=UseType.Y), Q.AND)

        if isinstance(job_date, str) and job_date != "":
            start_job_date, end_job_date = return_start_end_date(job_date)
            if start_job_date == end_job_date:
                condition.add(Q(job_talk__job_date__icontains=start_job_date), Q.AND)
            else:
                condition.add(Q(job_talk__job_date__range=[start_job_date, end_job_date]), Q.AND)

        if isinstance(inspection_date, str) and inspection_date != "":
            start_inspection_date, end_inspection_date = return_start_end_date(inspection_date)
            if start_inspection_date == end_inspection_date:
                condition.add(Q(job_talk__inspection_date__icontains=start_inspection_date), Q.AND)
            else:
                condition.add(Q(job_talk__inspection_date__range=[start_inspection_date, end_inspection_date]), Q.AND)

        if searched_annotator_info_word is not None and searched_annotator_info_word != '':
            condition.add(Q(job_talk__annotator__member__name__icontains=searched_annotator_info_word) | Q(job_talk__annotator__member__tel_no__icontains=searched_annotator_info_word), Q.AND)

        if searched_reviewer_info_word is not None and searched_reviewer_info_word != '':
            condition.add(Q(job_talk__reviewer__member__name__icontains=searched_reviewer_info_word) | Q(job_talk__reviewer__member__tel_no__icontains=searched_reviewer_info_word), Q.AND)

        if searched_domain_word is not None and searched_domain_word != '':
            condition.add(Q(job_talk__job_talk_source__domain__icontains=searched_domain_word), Q.AND)

        if searched_category_word is not None and searched_category_word != '':
            condition.add(Q(job_talk__job_talk_source__category__icontains=searched_category_word), Q.AND)

        if searched_talk_word is not None and searched_talk_word != '':
            condition.add(Q(job_talk__job_talk_source__deidentificated_talk__icontains=searched_talk_word), Q.AND)

        if searched_intent_word is not None and searched_intent_word != '':
            condition.add(Q(intent__icontains=searched_intent_word), Q.AND)
            condition2.add(Q(intent__icontains=searched_intent_word), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            condition.add(Q(job_talk__dataset_id__in=dataset_ids), Q.AND)

        if selected_inspectionStatus is not None and selected_inspectionStatus != "all":
            if selected_inspectionStatus == InspectionStatus.Initial:
                condition.add(Q(job_talk__inspection_status=InspectionStatus.Initial) & Q(job_talk__reject_count=0), Q.AND)
            else:
                condition.add(Q(job_talk__inspection_status=selected_inspectionStatus), Q.AND)

        if selected_reviewer_grade != "all" and selected_reviewer_grade is not None:
            condition.add(Q(job_talk__reviewer__member__membergrade2member__grade_code=selected_reviewer_grade), Q.AND)

        sub_qs = JobTalkSummary.objects.filter()

        job_talk_qs = JobTalkSummary.objects.prefetch_related('job_talk')\
            .annotate(talk_count=Subquery(JobTalkSummary.objects.filter(job_talk_id=OuterRef('job_talk_id'))\
                                         .filter(condition2)
                                         .values('job_talk_id')\
                                         .annotate(Count('job_talk_id'))\
                                         .values('job_talk_id__count')))\
            .filter(condition)\
            .all().order_by('-job_talk__inspection_date', 'id')

        print(job_talk_qs.query)
        page = int(page)
        paginator = Paginator(job_talk_qs, 12)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        total_count = job_talk_qs.count()

        if 'all' not in dataset_ids:
            dataset_names = [Dataset.objects.get(id=id).dataset_name for id in dataset_ids]
        else:
            dataset_names = ['전체']

        context['items'] = page_list
        context['paginator_range'] = paginator_range
        context['total_count'] = total_count
        context['dataset_names'] = dataset_names
        context['page'] = page
        context['blank_count'] = 12 - (total_count - 12 * (page - 1)) if total_count - 12 * (page - 1) < 12 else 0
        return context

@csrf_exempt
def get_talk_reviewer_record_tbody_html(request):
    if request.is_ajax():
        dataset_ids = request.POST.getlist('dataset_ids[]', None)
        annotator_info = request.POST.get('annotator_info', None)
        reviewer_info = request.POST.get('reviewer_info', None)
        domain = request.POST.get('domain', None)
        category = request.POST.get('category', None)
        talk = request.POST.get('talk', None)
        intent = request.POST.get('intent', None)
        inspection_date = request.POST.get('inspection_date', None)
        inspectionStatus = request.POST.get('inspectionStatus', None)
        reviewer_grade = request.POST.get('reviewer_grade', None)
        job_date = request.POST.get('job_date', None)
        page = request.POST.get('page', 1)

        if not dataset_ids:
            dataset_ids = ['all']
        context = ReviewerRecordTableTrView(
            kwargs={'user': request.user, 'dataset_ids': dataset_ids, 'reviewer_info': reviewer_info, 'reviewer_grade': reviewer_grade, 'annotator_info': annotator_info, 'domain': domain, 'category': category, 'talk': talk, 'intent':intent ,'inspectionStatus': inspectionStatus,'inspection_date':inspection_date, 'job_date': job_date, 'page': page}).get_context_data()


        html = render_to_string('partials/reviewer_record_table_tr.html', context)
        pagenation_html = render_to_string('paginnation.html', context)

        dataset_names = context['dataset_names']

        return JsonResponse(
            {'result': True, 'html': html, 'pagenation_html': pagenation_html, 'total_count': context['total_count'], 'dataset_names': dataset_names})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})