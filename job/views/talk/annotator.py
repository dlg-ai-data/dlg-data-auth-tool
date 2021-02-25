import json
import traceback
import urllib.request as urllib
from datetime import datetime

import xlwt
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Subquery, Count, OuterRef
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView
from django.template.loader import render_to_string

from common.choices import JobStatus, InspectionStatus, MemberJoinSource, MemberGrade_Choice, WorkType, MemberRole
from common.choices import UseType
from common.templatetags.html_extras import return_start_end_date
from common.utils import get_page_range
from dataset.models import Annotator, Reviewer, DatasetGrade, Dataset
from member.models import MemberGrade
from job.forms import TalkJobManagementForm
from job.models import JobTalk, JobAnnotratorHistory, JobTalkSummary, JobReviewerHistory
from vaiv.view import LoginRequiredMixin
from django.db.models import Q, Sum
from member.models import MemberAddition,User


class TalkAnnotatorJobManagement(LoginRequiredMixin, FormView):
    template_name = 'job/talk/annotator/management.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkAnnotatorJobManagement, self).get_context_data(**kwargs)
        dataset_ids = self.request.GET.getlist('dataset_id', None)
        join_date = self.request.GET.get('join_date', None)
        modf_date = self.request.GET.get('modf_date', None)
        job_date = self.request.GET.get('job_date', None)
        limit_yn = self.request.GET.get('limit_yn', None)
        selected_join_source = self.request.GET.get('join_source', None)
        searched_annotator_info_word = self.request.GET.get('word', '')
        selected_grade = self.request.GET.get('grade', None)

        sort_criterion = self.request.GET.get('sort_criterion', 'id')
        upDown = self.request.GET.get('upDown', '-')

        is_selected, is_searched = False, False

        condition = Q()
        condition.add(Q(member__secession_yn=UseType.N), Q.AND)

        condition2 = Q()
        condition2.add(Q(annotator_id=OuterRef('id')), Q.AND)
        condition2.add(Q(annotator__isnull=False), Q.AND)
        condition2.add(Q(job_status__in=[JobStatus.Complete, JobStatus.Exclude]), Q.AND)

        if isinstance(join_date, str) and join_date != "":
            is_selected = True
            start_join_date, end_join_date = return_start_end_date(join_date)
            if start_join_date == end_join_date:
                condition.add(Q(member__join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(member__join_date__range=[start_join_date, end_join_date]), Q.AND)

        if isinstance(modf_date, str) and modf_date != "":
            is_selected = True
            start_modf_date, end_modf_date = return_start_end_date(modf_date)
            if start_modf_date == end_modf_date:
                condition.add(Q(member__modf_date__icontains=start_modf_date), Q.AND)
            else:
                condition.add(Q(member__modf_date__range=[start_modf_date, end_modf_date]), Q.AND)

        if isinstance(job_date, str) and job_date != "":
            is_selected = True
            start_job_date, end_job_date = return_start_end_date(job_date)
            if start_job_date == end_job_date:
                condition2.add(Q(job_date__icontains=start_job_date), Q.AND)
            else:
                condition2.add(Q(job_date__range=[start_job_date, end_job_date]), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if selected_join_source is not None and selected_join_source != 'all':
            is_selected = True
            condition.add(Q(member__memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if limit_yn is not None and limit_yn != 'all':
            is_selected = True
            condition.add(Q(limit_yn=limit_yn), Q.AND)

        if searched_annotator_info_word is not None and searched_annotator_info_word != '':
            is_searched = True
            condition.add(Q(member__name__icontains=searched_annotator_info_word) | Q(
                member__email__icontains=searched_annotator_info_word) | Q(
                member__tel_no__icontains=searched_annotator_info_word), Q.AND)

        if selected_grade is not None and selected_grade != 'all':
            is_selected = True
            condition.add(Q(member__membergrade2member__grade_code=selected_grade), Q.AND)
            condition.add(Q(member__membergrade2member__valid_yn=UseType.Y), Q.AND)

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

        job_talk_qs = JobTalk.objects.filter(condition2)
        annotator_list = Annotator.objects \
            .extra(tables=['dataset', 'member']
                   , where=['dataset.id=annotator.dataset_id'
                , 'annotator.member_id=member.id']) \
            .filter(condition) \
            .annotate(total_count=Subquery(
            job_talk_qs
                .filter(((Q(job_status=JobStatus.Complete) & Q(inspection_status=InspectionStatus.Initial)) | (
                    Q(job_status=JobStatus.Exclude) & Q(inspection_status=InspectionStatus.Initial))) |
                        Q(job_status=JobStatus.Complete, inspection_status=InspectionStatus.Complete) |
                        Q(inspection_status=InspectionStatus.Reject) |
                        Q(job_status=JobStatus.Exclude, inspection_status=InspectionStatus.Impossible))
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(inspection_status_initial_count=Subquery(
            job_talk_qs.filter((Q(job_status=JobStatus.Complete) & Q(inspection_status=InspectionStatus.Initial)) | (
                    Q(job_status=JobStatus.Exclude) & Q(inspection_status=InspectionStatus.Initial)))
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(inspection_status_complete_count=Subquery(
            job_talk_qs.filter(job_status=JobStatus.Complete, inspection_status=InspectionStatus.Complete)
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(inspection_status_reject_count=Subquery(
            job_talk_qs.filter(Q(inspection_status=InspectionStatus.Reject))
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(accumulated_reject_count=Subquery(
            job_talk_qs.values('annotator_id').annotate(sum=(Sum('reject_count'))).values('sum')
        )).order_by(sort_condition)

        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(annotator_list, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['annotator_list'] = page_list
        context['searched_annotator_info_word'] = searched_annotator_info_word
        context['paginator_range'] = paginator_range
        context['total_count'] = annotator_list.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['dataset_ids'] = dataset_ids
        context['join_date'] = join_date
        context['modf_date'] = modf_date
        context['job_date'] = job_date
        context['selected_grade'] = selected_grade
        context['selected_limit_yn'] = limit_yn
        context['selected_join_source'] = selected_join_source
        context['page'] = page
        context['blank_count'] \
            = 15 - (annotator_list.count() - 15 * (page - 1)) if annotator_list.count() - 15 * (page - 1) < 15 else 0
        context['sort_criterion'] = sort_criterion
        context['upDown'] = upDown
        return context


class TalkAnnotatorJob(LoginRequiredMixin, FormView):
    template_name = 'job/talk/annotator/talk_annotate.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkAnnotatorJob, self).get_context_data(**kwargs)

        source_id = self.kwargs.get('id')

        jobtalk = JobTalk.objects.filter(id=source_id)
        if jobtalk[0]!=None and jobtalk[0].inspection_status==InspectionStatus.Reject:
            context['reject_msg'] = jobtalk[0].reject_msg
            if context['reject_msg']=='':
                context['reject_msg'] = "사유 없음"
            context['inspection_status'] = jobtalk[0].inspection_status
        else :
            context['reject_msg'] = ""
            context['inspection_status'] = InspectionStatus.Initial
        condition = Q()
        condition.add(Q(job_talk_id=source_id), Q.AND)

        jobtalksummary = JobTalkSummary.objects.filter(condition)

        condition = Q()
        condition.add(Q(id=source_id), Q.AND)

        jobtalk = JobTalk.objects.filter(condition)
        context['selected_deidentification_status'] = jobtalk[0].job_talk_source.de_identificated_status
        context['source_detail'] = jobtalk[0].job_talk_source.de_identificated_talk
        context['talker_count'] = jobtalk[0].job_talk_source.talker_count
        context['turn_talk_count'] = jobtalk[0].job_talk_source.turn_talk_count
        context['speechbubble_count'] = jobtalk[0].job_talk_source.speechbubble_count

        if len(jobtalksummary) == 0:
            context['table_count'] = jobtalk[0].job_talk_source.speechbubble_count
        else:
            context['jobtalksummary'] = jobtalksummary
            context['table_count'] = 0
        context['job_status'] = jobtalk[0].job_status
        context['source_id'] = self.kwargs.get('id')
        context['member_id'] =  self.request.user.id
        return context


def JobTalkSave(request):
    if request.is_ajax():
        tasks = request.GET.getlist('list[]')
        source_id = request.GET.get('source_id')
        member_id = request.GET.get('member_id')
        isTmp = request.GET.get('isTmp')

        try:
            role_code = User.objects.get(id=member_id, role_code=MemberRole.Annotrator)
        except Exception as e:
            return JsonResponse({'result': False, 'error': '어노테이터로 등록된 회원이 아닙니다.'})

        try:
            with transaction.atomic():
                jobtalk = JobTalk.objects.get(id=source_id)

                if jobtalk.annotator is not None and int(jobtalk.annotator.member_id) != int(member_id):
                    return JsonResponse({'result': False, 'msg': '다른 어노테이터가 작업한 목록입니다.', 'type': 'not'})
                if jobtalk.annotator is None:
                    condition = Q()
                    condition.add(Q(member_id=member_id), Q.AND)
                    condition.add(Q(dataset_id=jobtalk.dataset_id), Q.AND)
                    jobtalk.annotator = Annotator.objects.get(condition)
                jobtalk.mod_date = datetime.now()
                jts_del = JobTalkSummary.objects.filter(job_talk=source_id)
                jts_del.delete()
                for i in range(0, len(tasks)):
                    json_val = json.loads(tasks[i])
                    jobtalksummary = JobTalkSummary()
                    jobtalksummary.job_talk_id = source_id
                    jobtalksummary.talker = json_val['talker']
                    jobtalksummary.talk_summary = json_val['summary']
                    jobtalksummary.seq = i + 1
                    jobtalksummary.qa_type = json_val['qatype']
                    jobtalksummary.intent = json_val['intent']
                    jobtalksummary.save()
                if isTmp == 'True':
                    jobtalk.job_date = datetime.now()
                    jobtalk.job_status = JobStatus.Writing
                    jobtalk.save()

                    JobAnnotratorHistory.objects.update_or_create(job_id=source_id, annotator_id=jobtalk.annotator.id, job_status=JobStatus.Writing,
                                                                defaults={
                                                                    'work_type': WorkType.Update,
                                                                    'work_text': '대화 요약 중간저장',
                                                                    'job_status': JobStatus.Writing,
                                                                    'inspection_status': InspectionStatus.Initial})
                    return JsonResponse({'result': True, 'msg': '임시 저장되었습니다.', 'type': 'tmp'})
                else:
                    jobtalk.job_date = datetime.now()
                    jobtalk.job_status = JobStatus.Complete
                    jobtalk.inspection_status = InspectionStatus.Initial
                    jobtalk.save()

                    JobAnnotratorHistory.objects.create(job_id=source_id, annotator_id=jobtalk.annotator.id,
                                                      work_type=WorkType.Update,
                                                      work_text='작업완료',
                                                      job_status=JobStatus.Complete,
                                                      inspection_status=InspectionStatus.Complete)
                    return JsonResponse({'result': True, 'msg': '제출되었습니다.', 'type': 'save'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def JobAssignment(request):
    if request.is_ajax():
        member_id = request.user.id
        print(member_id)
        index = -1
        condition = Q()
        condition.add(Q(member_id=member_id), Q.AND)
        condition.add(Q(valid_yn=UseType.Y), Q.AND)
        annotator = Annotator.objects.filter(condition)
        if len(annotator) == 0:
            return JsonResponse({'result': True, 'msg': '어노테이터로 등록되지 않은 회원입니다.', 'index': index})

        condition = Q()
        for i in annotator:
            condition.add(Q(annotator=i.id) & Q(dataset=i.dataset), Q.OR)

        condition.add(Q(job_status='AK03') | Q(inspection_status='AL02'), Q.AND)
        isjobDate = JobTalk.objects.filter(condition).order_by('inspection_status')[:1]
        if len(isjobDate) != 0:
            return JsonResponse({'result': True, 'msg': '작업이 완료 되지 않았거나 반려된 건이 존재합니다. 해당 작업으로 이동됩니다.', 'index': isjobDate[0].id})

        check_datetime = datetime.now()
        current_submit_count = JobTalk.objects \
            .filter(job_date__year=check_datetime.year,
                    job_date__month=check_datetime.month,
                    job_date__day=check_datetime.day,
                    job_status__in=[JobStatus.Complete, JobStatus.Exclude],
                    annotator=annotator[0])
        if annotator[0].limit_yn == UseType.Y:
            return JsonResponse({'result': True, 'msg': '작업제한 상태입니다.', 'index': index})

        if annotator[0].limit_count > 0 and (annotator[0].limit_count <= len(current_submit_count)):
            return JsonResponse({'result': True, 'msg': '일일작업량을 초과하였습니다.', 'index': index})

        condition = Q()
        condition.add(Q(annotator__isnull=True), Q.AND)
        condition.add(Q(job_status='AK01'), Q.AND)
        dataset=[]
        for i in annotator:
            dataset.append(i.dataset_id)

        condition.add(Q(dataset__in=dataset), Q.AND)
        jobtalkdata = JobTalk.objects.filter(condition).order_by('id')[:1]

        if len(jobtalkdata) == 0:
            return JsonResponse({'result': True, 'msg': '배정받을 작업이 존재하지 않습니다.', 'index': index})
        index = jobtalkdata[0].id
        annotator_id = -1
        for i in annotator:
            if i.dataset == jobtalkdata[0].dataset:
                annotator_id = i.id
                break
        if annotator_id == -1:
            return JsonResponse({'result': True, 'msg': '어노테이터가 잘못 지정되었습니다. 다시 확인해주세요', 'index': -1})

        try:
            with transaction.atomic():
                jobtalk = JobTalk.objects.get(id=index)
                jobtalk.annotator_id = annotator_id
                jobtalk.job_status = 'AK03'

                JobAnnotratorHistory.objects.create(job_id=jobtalk.id
                                                    , annotator_id=annotator_id
                                                    , work_type=WorkType.Create
                                                    , work_text='신규작업배정'
                                                    , job_status=JobStatus.Initial
                                                    , inspection_status=InspectionStatus.Initial)
                jobtalk.save()
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': '배정에 실패했습니다.'})
        return JsonResponse({'result': True, 'msg': '배정되었습니다.', 'index': index})
    else:
        return JsonResponse({'result': False, 'error': '오류가 발생했습니다.(전송오류)'})


class TalkAnnotatorJobList(LoginRequiredMixin, FormView):
    template_name = 'job/talk/annotator/talk_annotate_list.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkAnnotatorJobList, self).get_context_data(**kwargs)

        dataset_ids = self.request.GET.getlist('dataset_ids', None)
        print(dataset_ids)
        search_date = self.request.GET.get('search_date')
        inspection_status = self.request.GET.get('inspection_status','all')
        job_status = self.request.GET.get('job_status','all')
        member_id = self.request.user.id
        searched_word = self.request.GET.get('word')
        condition = Q()
        condition.add(Q(annotator__member_id=member_id), Q.AND)
        if inspection_status  is not None and inspection_status != "all":
            condition.add(Q(inspection_status=inspection_status), Q.AND)
        if isinstance(search_date, str) and search_date != "":
            start_join_date, end_join_date = return_start_end_date(search_date)
            if start_join_date == end_join_date:
                condition.add(Q(job_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(job_date__range=[start_join_date, end_join_date]), Q.AND)

        if job_status  is not None and job_status != "all":
            condition.add(Q(job_status=job_status), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        job_talk_qs = JobTalk.objects.filter(condition) \
            .extra(tables=['dataset'], select={'dataset_name': 'dataset.dataset_name'}
                   , where=['job_talk.dataset_id=dataset.id']) \
            .select_related('job_talk_source') \
            .order_by('job_date')
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(job_talk_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['inspection_status'] = inspection_status
        context['job_status'] = job_status
        context['search_date'] = search_date
        context['jobtalk_list'] = page_list
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['total_count'] = job_talk_qs.count()
        context['dataset_ids'] = dataset_ids
        context['page'] = page
        context['blank_count'] \
            = 15 - (job_talk_qs.count() - 15 * (page - 1)) if job_talk_qs.count() - 15 * (page - 1) < 15 else 0
        return context


class TalkAnnotatorJobRecord(LoginRequiredMixin, FormView):
    template_name = 'job/talk/annotator/record.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkAnnotatorJobRecord, self).get_context_data(**kwargs)
        return context

class AnnotatorRecordTableTrView(LoginRequiredMixin, TemplateView):

    def get_context_data(self, **kwargs):
        context = super(AnnotatorRecordTableTrView, self).get_context_data(**kwargs)

        dataset_ids = self.kwargs.get('dataset_ids', None)
        searched_annotator_info_word = self.kwargs.get('annotator_info', '')
        selected_jobStatus = self.kwargs.get('jobStatus', None)
        job_date = self.kwargs.get('job_date', None)
        selected_inspectionStatus = self.kwargs.get('inspectionStatus', None)
        searched_domain_word = self.kwargs.get('domain', '')
        searched_category_word = self.kwargs.get('category', '')
        searched_talk_word = self.kwargs.get('talk', '')
        searched_intent_word = self.kwargs.get('intent', '')
        selected_annotator_grade = self.kwargs.get('annotator_grade', None)
        page = self.kwargs.get('page')

        # 앞뒤 공백 제거
        if searched_annotator_info_word is not None:
            searched_annotator_info_word = searched_annotator_info_word.strip()
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
            condition.add(Q(job_talk__annotator__member__id=user.id), Q.AND)
        condition2 = Q()
        condition.add(Q(job_talk__job_status__in=[JobStatus.Complete, JobStatus.Exclude]), Q.AND)
        condition.add(Q(job_talk__annotator__member__membergrade2member__valid_yn=UseType.Y), Q.AND)

        if isinstance(job_date, str) and job_date != "":
            start_job_date, end_job_date = return_start_end_date(job_date)
            if start_job_date == end_job_date:
                condition.add(Q(job_talk__job_date__icontains=start_job_date), Q.AND)
            else:
                condition.add(Q(job_talk__job_date__range=[start_job_date, end_job_date]), Q.AND)

        if searched_annotator_info_word is not None and searched_annotator_info_word != '':
            condition.add(Q(job_talk__annotator__member__name__icontains=searched_annotator_info_word) | Q(annotator__member__tel_no__icontains=searched_annotator_info_word), Q.AND)

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

        if selected_jobStatus is not None and selected_jobStatus != "all":
            if selected_jobStatus == 'AL02_his':
                condition.add(Q(job_talk__inspection_status=InspectionStatus.Initial) & Q(job_talk__reject_count__gte=1), Q.AND)
            else:
                condition.add(Q(job_talk__job_status=selected_jobStatus), Q.AND)

        if selected_annotator_grade != "all" and selected_annotator_grade is not None:
            condition.add(Q(job_talk__annotator__member__membergrade2member__grade_code=selected_annotator_grade), Q.AND)

        sub_qs = JobTalkSummary.objects.filter()

        job_talk_qs = JobTalkSummary.objects.prefetch_related('job_talk')\
            .annotate(talk_count=Subquery(JobTalkSummary.objects.filter(job_talk_id=OuterRef('job_talk_id'))\
                                         .filter(condition2)
                                         .values('job_talk_id')\
                                         .annotate(Count('job_talk_id'))\
                                         .values('job_talk_id__count')))\
            .filter(condition)\
            .all().order_by('-job_talk__job_date', 'id')

        print(job_talk_qs.query)
        page = int(page)
        paginator = Paginator(job_talk_qs, 15)
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
        context['blank_count'] = 4 - (total_count - 15 * (page - 1)) if total_count - 15 * (page - 1) < 15 else 0
        return context

@csrf_exempt
def get_talk_annotator_record_tbody_html(request):
    if request.is_ajax():
        dataset_ids = request.POST.getlist('dataset_ids[]', None)
        annotator_info = request.POST.get('annotator_info', None)
        domain = request.POST.get('domain', None)
        category = request.POST.get('category', None)
        talk = request.POST.get('talk', None)
        intent = request.POST.get('intent', None)
        jobStatus = request.POST.get('jobStatus', None)
        inspectionStatus = request.POST.get('inspectionStatus', None)
        annotator_grade = request.POST.get('annotator_grade', None)
        job_date = request.POST.get('job_date', None)
        page = request.POST.get('page', 1)

        if not dataset_ids:
            dataset_ids = ['all']
        context = AnnotatorRecordTableTrView(
            kwargs={'user': request.user,'dataset_ids': dataset_ids, 'jobStatus': jobStatus, 'annotator_grade': annotator_grade, 'annotator_info': annotator_info, 'domain': domain, 'category': category, 'talk': talk, 'intent':intent ,'inspectionStatus': inspectionStatus, 'job_date': job_date, 'page': page}).get_context_data()


        html = render_to_string('partials/annotator_record_table_tr.html', context)
        pagenation_html = render_to_string('paginnation.html', context)

        dataset_names = context['dataset_names']

        return JsonResponse(
            {'result': True, 'html': html, 'pagenation_html': pagenation_html, 'total_count': context['total_count'], 'dataset_names': dataset_names})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

@csrf_exempt
def talk_annotator_limit_modify(request):
    job_limit_count, job_limit_yn, annotator_id, new_data, to_be_changed_items = None, None, None, None, None

    if request.method == "GET":
        annotator_id = request.GET.get('annotator_id', None)
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
                    annotator = Annotator.objects.get(id=annotator_id)
                    annotator.limit_yn = job_limit_yn
                    annotator.limit_count = job_limit_count
                    annotator.save()
                else:
                    for item in to_be_changed_items:
                        annotator = Annotator.objects.get(id=item['annotator_id'])
                        annotator.limit_yn = item['job_limit_yn']
                        annotator.limit_count = item['job_limit_count']
                        annotator.save()
                return JsonResponse({'result': result, 'error': error, 'new_data': new_data})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def talk_annotator_list_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % urllib.quote(
        '어노테이터 작업관리 목록.xls'.encode('utf-8'))
    try:
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('어노테이터 작업관리 목록')

        row_num = 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        ws.write_merge(0, 0, 1, 5, '어노테이터 정보', xlwt.easyxf('pattern: pattern solid, fore_color yellow'))
        ws.write_merge(0, 0, 6, 14, '검수 집계 (개 / %)', xlwt.easyxf('pattern: pattern solid, fore_color light_green'))
        columns = ['데이터세트명', '이메일', '이름', '연락처', '등급', '가입경로',
                   '전체건수',
                   '초기', '', '승인', '', '반려', '', '반려(누적)', '',
                   '작업제한량(일일)(0:무제한)', '작업제한여부(Y:작업불가)']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        dataset_ids = request.GET.getlist('dataset_id', None)
        join_date = request.GET.get('join_date', None)
        modf_date = request.GET.get('modf_date', None)
        job_date = request.GET.get('job_date', None)
        limit_yn = request.GET.get('limit_yn', None)
        selected_join_source = request.GET.get('join_source', None)
        searched_word = request.GET.get('searched_word')

        sort_criterion = request.GET.get('sort_criterion', 'id')
        upDown = request.GET.get('upDown', '-')

        condition = Q()
        condition.add(Q(member__secession_yn=UseType.N), Q.AND)
        condition.add(Q(valid_yn=UseType.Y), Q.AND)
        condition.add(Q(member__membergrade2member__valid_yn=UseType.Y), Q.AND)

        condition2 = Q()
        condition2.add(Q(annotator_id=OuterRef('id')), Q.AND)
        condition2.add(Q(annotator__isnull=False), Q.AND)
        condition2.add(Q(job_status__in=[JobStatus.Complete, JobStatus.Exclude]), Q.AND)

        if isinstance(join_date, str) and join_date != "":
            start_join_date, end_join_date = return_start_end_date(join_date)
            if start_join_date == end_join_date:
                condition.add(Q(member__join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(member__join_date__range=[start_join_date, end_join_date]), Q.AND)

        if isinstance(modf_date, str) and modf_date != "":
            start_modf_date, end_modf_date = return_start_end_date(modf_date)
            if start_modf_date == end_modf_date:
                condition.add(Q(member__modf_date__icontains=start_modf_date), Q.AND)
            else:
                condition.add(Q(member__modf_date__range=[start_modf_date, end_modf_date]), Q.AND)

        if isinstance(job_date, str) and job_date != "":
            start_job_date, end_job_date = return_start_end_date(job_date)
            if start_job_date == end_job_date:
                condition2.add(Q(job_date__icontains=start_job_date), Q.AND)
            else:
                condition2.add(Q(job_date__range=[start_job_date, end_job_date]), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if selected_join_source is not None and selected_join_source != 'all':
            condition.add(Q(member__memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if limit_yn is not None and limit_yn != 'all':
            condition.add(Q(limit_yn=limit_yn), Q.AND)

        if searched_word is not None and searched_word != '':
            condition.add(Q(member__name__icontains=searched_word) | Q(member__email__icontains=searched_word), Q.AND)

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
        elif sort_criterion == 'join_source':
            sort_condition += "member__memberaddition2member__member_join_source"
        elif sort_criterion == 'initial_count':
            sort_condition += "inspection_status_initial_count"
        elif sort_criterion == 'complete_count':
            sort_condition += "inspection_status_complete_count"
        elif sort_criterion == 'reject_count':
            sort_condition += "inspection_status_reject_count"
        elif sort_criterion == 'impossible_count':
            sort_condition += "inspection_status_impossible_count"
        elif sort_criterion == 'accumulated_reject_count':
            sort_condition += "accumulated_reject_count"

        job_talk_qs = JobTalk.objects.filter(condition2)
        rows = Annotator.objects \
            .extra(tables=['dataset', 'member']
                   , where=['dataset.id=annotator.dataset_id'
                , 'annotator.member_id=member.id']) \
            .filter(condition) \
            .annotate(total_count=Subquery(
            job_talk_qs
                .filter(((Q(job_status=JobStatus.Complete) & Q(inspection_status=InspectionStatus.Initial)) | (
                    Q(job_status=JobStatus.Exclude) & Q(inspection_status=InspectionStatus.Initial))) |
                        Q(job_status=JobStatus.Complete, inspection_status=InspectionStatus.Complete) |
                        Q(inspection_status=InspectionStatus.Reject) |
                        Q(job_status=JobStatus.Exclude, inspection_status=InspectionStatus.Impossible))
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(inspection_status_initial_count=Subquery(
            job_talk_qs.filter((Q(job_status=JobStatus.Complete) & Q(inspection_status=InspectionStatus.Initial)) | (
                    Q(job_status=JobStatus.Exclude) & Q(inspection_status=InspectionStatus.Initial)))
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(inspection_status_complete_count=Subquery(
            job_talk_qs.filter(job_status=JobStatus.Complete, inspection_status=InspectionStatus.Complete)
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(inspection_status_reject_count=Subquery(
            job_talk_qs.filter(Q(inspection_status=InspectionStatus.Reject))
                .values('annotator_id')
                .annotate(Count('annotator_id'))
                .values('annotator_id__count')
        )) \
            .annotate(accumulated_reject_count=Subquery(
            job_talk_qs.values('annotator_id').annotate(sum=(Sum('reject_count'))).values('sum')))\
        .values_list('dataset__dataset_name', 'member__email', 'member__name', 'member__tel_no', 'member__membergrade2member__grade_code',
                     'member__memberaddition2member__member_join_source',
                     'total_count',
                     'inspection_status_initial_count', 'inspection_status_complete_count',
                     'inspection_status_reject_count', 'accumulated_reject_count',
                     'limit_count', 'limit_yn').order_by(sort_condition)
        print(rows.query)
        data_count = rows.count()
        plus = 0
        for row in rows:
            row_num += 1
            total = None
            for col_num in range(len(row)):
                output_data = row[col_num]
                if col_num == 4:
                    output_data = MemberGrade_Choice.get_value(output_data)
                if col_num == 5:
                    output_data = MemberJoinSource.get_value(output_data)
                if col_num == 6:
                    total = output_data
                    output_data = '0' if output_data is None else str(output_data)
                if col_num == 7 or col_num == 8 or col_num == 9 or col_num == 10:
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
                ws.write(row_num, col_num + plus, output_data, font_style)
            plus = 0

        wb.save(response)
    except Exception as e:
        traceback.print_exc()
        return response

    return response


@csrf_exempt
def talk_annotator_collection(request):
    if request.is_ajax():
        result = True
        error = ""
        try:
            with transaction.atomic():
                annotator_id = request.GET.get('annotator_id', None)
                inspection_status_reject_count = int(request.GET.get('inspection_status_reject_count', '0'))
                job_qs = JobTalk.objects.filter(annotator_id=annotator_id, inspection_status=InspectionStatus.Reject,
                                                job_status=JobStatus.Complete)
                reject_count = job_qs.count()
                if reject_count == inspection_status_reject_count:
                    for job in job_qs:
                        job.job_status = JobStatus.Complete
                        job.job_date = None
                        job.inspection_status = InspectionStatus.Impossible
                        job.inspection_date = None
                        job.reviewer = None
                        job.annotator = None
                        job.save()

                        JobTalkSummary.objects.filter(id=job.talk_summary_id).update(
                            json=None
                        )

                        JobAnnotratorHistory.objects.create(job_source_id=job.id
                                                            , annotator_id=annotator_id
                                                            , work_type=WorkType.Reset
                                                            , work_text='{}-관리자에 의한 초기화 처리'.format(request.user.email)
                                                            , job_status=JobStatus.Initial
                                                            , inspection_status=InspectionStatus.Initial)

                    return JsonResponse({'result': result, 'error': error})
                else:
                    return JsonResponse({'result': False, 'error': '삭제건이 일치하지 않습니다.'})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def talk_annotator_inspection(request):
    if request.is_ajax():
        result = True
        error = ""
        try:
            with transaction.atomic():
                annotator_id = request.GET.get('annotator_id', None)
                dataset_id = request.GET.get('dataset_id', None)
                annotator_qs = Annotator.objects.get(id=annotator_id , dataset_id=dataset_id, valid_yn=UseType.Y)
                job_qs = JobTalk.objects.filter(annotator_id=annotator_id, inspection_status=InspectionStatus.Initial, dataset_id=dataset_id,
                                                job_status=JobStatus.Complete)
                try:
                    reviewer_qs = Reviewer.objects.get(member_id=request.user.id, dataset_id=annotator_qs.dataset_id, valid_yn=UseType.Y)
                except Reviewer.DoesNotExist:
                    reviewer_qs = Reviewer.objects.create(member_id=request.user.id, dataset_id=annotator_qs.dataset_id, valid_yn=UseType.Y,
                                                          limit_count=0, limit_yn=UseType.N)

                for job in job_qs:
                    job.inspection_status = InspectionStatus.Complete
                    job.inspection_date = datetime.now()
                    job.reviewer_id = reviewer_qs.id
                    job.save()

                    JobReviewerHistory.objects.create(job_source_id=job.id
                                                      , reviewer_id=reviewer_qs.id
                                                      , work_type=WorkType.Update
                                                      , work_text='{}-관리자에 의한 검수 승인 처리'.format(request.user.email)
                                                      , job_status=JobStatus.Complete
                                                      , inspection_status=InspectionStatus.Complete)
                    member_grade_qs = MemberGrade.objects.get(member_id=annotator_qs.member_id
                                                                      , valid_yn=UseType.Y)
                    datasetgrade_qs = DatasetGrade.objects.get(dataset_id=annotator_qs.dataset_id,
                                                               grade_code=member_grade_qs.grade_code,
                                                               job_use_yn=UseType.Y)

                return JsonResponse({'result': result, 'error': error})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})
