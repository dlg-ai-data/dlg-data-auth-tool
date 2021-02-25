import json
import traceback
import urllib.request as urllib
from datetime import datetime

import xlwt
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Subquery, Count, OuterRef, F, Value, QuerySet, Prefetch
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView

from common.choices import JobStatus, InspectionStatus, MemberJoinSource, MemberGrade_Choice, WorkType, \
    DeIdentificationStatus, MemberRole
from common.choices import UseType
from common.templatetags.html_extras import return_start_end_date
from common.utils import get_page_range, convert_dict_to_queryset
from dataset.models import Provider
from member.models import MemberGrade, User
from job.forms import TalkJobManagementForm
from job.models import JobTalk, JobTalkSource
from vaiv.view import LoginRequiredMixin
from django.db.models import Q, Sum
from member.models import MemberAddition

from collections import namedtuple

class TalkProviderManagement(LoginRequiredMixin, FormView):
    template_name = 'job/talk/provider/management.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkProviderManagement, self).get_context_data(**kwargs)
        dataset_ids = self.request.GET.getlist('dataset_id', None)
        join_date = self.request.GET.get('join_date', None)
        modf_date = self.request.GET.get('modf_date', None)
        job_date = self.request.GET.get('job_date', None)
        limit_yn = self.request.GET.get('limit_yn', None)
        selected_join_source = self.request.GET.get('join_source', None)
        searched_provider_info_word = self.request.GET.get('word', '')

        sort_criterion = self.request.GET.get('sort_criterion', 'id')
        upDown = self.request.GET.get('upDown', '-')

        is_selected, is_searched = False, False

        condition = Q(provider__member__membergrade2member__grade_code=MemberGrade_Choice.Provider)
        condition.add(Q(provider__member__secession_yn=UseType.N), Q.AND)

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

        if searched_provider_info_word is not None and searched_provider_info_word != '':
            condition.add(Q(provider__member__name__icontains=searched_provider_info_word) |
                          Q(provider__member__email__icontains=searched_provider_info_word) |
                          Q(provider__member__tel_no__icontains=searched_provider_info_word),Q.AND)

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

        job_talk_qs = JobTalkSource.objects\
            .select_related('dataset')\
            .select_related('provider') \
            .prefetch_related('provider__member__membergrade2member')\
            .filter( condition) \
            .values('dataset__dataset_name', 'provider__member__name', 'provider__member__tel_no', 'provider__member__email', 'provider_id', 'provider__limit_count') \
            .annotate(dataset_name=F('dataset__dataset_name'),
                  provider_name=F('provider__member__name'),
                  tel_no=F('provider__member__tel_no'),
                  email=F('provider__member__email'),
                  limit_count=F('provider__limit_count')) \
            .distinct()

        sub_qs=JobTalkSource.objects

        provider_list = job_talk_qs.annotate(total_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(provider_id=OuterRef('provider_id'), dataset_id=OuterRef('dataset_id'))
        ))\
            .annotate(inspection_status_initial_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(provider_id=OuterRef('provider_id'), dataset_id=OuterRef('dataset_id')).filter(Q(inspection_status=InspectionStatus.Initial) | Q(inspection_status__isnull=True))
        ))\
            .annotate(inspection_status_complete_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(provider_id=OuterRef('provider_id'), dataset_id=OuterRef('dataset_id')).filter(Q(inspection_status=InspectionStatus.Complete))
        ))\
            .annotate(inspection_status_reject_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(provider_id=OuterRef('provider_id'), dataset_id=OuterRef('dataset_id')).filter(Q(inspection_status=InspectionStatus.Reject))
        ))

        rtn_queryset = convert_dict_to_queryset('provider', provider_list)

        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(rtn_queryset, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['provider_list'] = page_list
        # context['searched_annotator_info_word'] = searched_annotator_info_word
        context['paginator_range'] = paginator_range
        context['total_count'] = len(rtn_queryset)
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['dataset_ids'] = dataset_ids
        context['join_date'] = join_date
        context['modf_date'] = modf_date
        context['job_date'] = job_date
        context['searched_word'] = searched_provider_info_word
        context['page'] = page
        context['blank_count'] \
            = 15 - (provider_list.count() - 15 * (page - 1)) if provider_list.count() - 15 * (page - 1) < 15 else 0
        context['sort_criterion'] = sort_criterion
        context['upDown'] = upDown
        return context

class TalkProviderRecord(LoginRequiredMixin, FormView):
    template_name = 'job/talk/provider/record.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkProviderRecord, self).get_context_data(**kwargs)

        searched_provider_info_word = self.request.GET.get('provider_info', '')
        dataset_ids = self.request.GET.getlist('dataset_ids', None)
        selected_inspectionStatus = self.request.GET.get('inspectionStatus', None)
        reg_date = self.request.GET.get('reg_date', None)
        searched_provider_domain_info_word = self.request.GET.get('domain', '')
        searched_provider_category_info_word = self.request.GET.get('category', '')
        searched_provider_talk_info_word = self.request.GET.get('talk', '')

        is_selected, is_searched = False, False

        condition = Q()
        if not self.request.user.is_admin:
            condition.add(Q(provider__member_id=self.request.user.id), Q.AND)

        if isinstance(reg_date, str) and reg_date != "":
            is_selected = True
            start_job_date, end_job_date = return_start_end_date(reg_date)
            if start_job_date == end_job_date:
                condition.add(Q(reg_date__icontains=start_job_date), Q.AND)
            else:
                condition.add(Q(reg_date__range=[start_job_date, end_job_date]), Q.AND)

        if searched_provider_info_word is not None and searched_provider_info_word != '':
            is_searched = True
            condition.add(Q(provider__member__name__icontains=searched_provider_info_word) | Q(
                provider__member__tel_no__icontains=searched_provider_info_word), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if selected_inspectionStatus is not None and selected_inspectionStatus != "all":
            is_selected = True
            condition.add(Q(inspection_status=selected_inspectionStatus), Q.AND)

        if searched_provider_domain_info_word != "" :
            is_searched = True
            condition.add(Q(domain__contains=searched_provider_domain_info_word), Q.AND)
        if searched_provider_category_info_word != "" :
            is_searched = True
            condition.add(Q(category__contains=searched_provider_category_info_word), Q.AND)
        if searched_provider_talk_info_word != "":
            is_searched = True
            condition.add(Q(de_identificated_talk__contains=searched_provider_talk_info_word), Q.AND)

        job_talk_qs = JobTalkSource.objects\
            .prefetch_related('dataset').filter(condition).order_by('inspection_status','id', '-reg_date')
        print(job_talk_qs.query)
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(job_talk_qs, 5)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['jobtalksource_list'] = page_list
        context['paginator_range'] = paginator_range
        context['total_count'] = job_talk_qs.count()
        context['dataset_ids'] = dataset_ids
        context['selected_inspectionStatus'] = selected_inspectionStatus
        context['searched_provider_info_word'] = searched_provider_info_word
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_domain_word'] = searched_provider_domain_info_word
        context['searched_category_word'] = searched_provider_category_info_word
        context['searched_talk_word'] = searched_provider_talk_info_word
        context['page'] = page
        context['job_date'] = reg_date
        context['blank_count'] \
            = 5 - (job_talk_qs.count() - 5 * (page - 1)) if job_talk_qs.count() - 5 * (page - 1) < 5 else 0
        return context

@csrf_exempt
def talk_provider_limit_modify(request):
    job_limit_count, job_limit_yn, provider_id, new_data, to_be_changed_items = None, None, None, None, None

    if request.method == "GET":
        provider_id = request.GET.get('provider_id', None)
        job_limit_count = request.GET.get('job_limit_count', None)
        new_data = [job_limit_count]
    else:
        to_be_changed_items = json.loads(request.POST['to_be_changed_items'])

    if request.is_ajax():
        result = True
        error = ""
        try:
            with transaction.atomic():
                if not to_be_changed_items:
                    provider = Provider.objects.get(id=provider_id)
                    provider.limit_count = job_limit_count
                    provider.save()
                else:
                    for item in to_be_changed_items:
                        provider = Provider.objects.get(id=item['provider_id'])
                        provider.limit_count = item['job_limit_count']
                        provider.save()
                return JsonResponse({'result': result, 'error': error, 'new_data': new_data})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

def talk_provider_list_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % urllib.quote(
        '대화조각제공자 작업관리 목록.xls'.encode('utf-8'))
    try:
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('대화조각제공자 작업관리 목록')

        row_num = 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True
        ws.write_merge(0, 0, 0, 4, '대화제공자 정보', xlwt.easyxf('pattern: pattern solid, fore_color yellow'))
        ws.write_merge(0, 0, 5, 12, '검수 집계 (개 / %)', xlwt.easyxf('pattern: pattern solid, fore_color light_green'))
        columns = ['데이터세트명', '이메일', '이름', '연락처', '등급',
                   '전체건수', '검수완료(승인+반려)',
                   '초기', '', '승인', '', '반려', '',
                   '작업제한량(일일)(0:무제한)']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        dataset_ids = request.GET.getlist('dataset_id', None)
        join_date = request.GET.get('join_date', None)
        modf_date = request.GET.get('modf_date', None)
        searched_word = request.GET.get('searched_word')

        sort_criterion = request.GET.get('sort_criterion', 'id')
        upDown = request.GET.get('upDown', '-')

        condition = Q(provider__member__membergrade2member__grade_code=MemberGrade_Choice.Provider)
        condition.add(Q(provider__member__secession_yn=UseType.N), Q.AND)

        if isinstance(join_date, str) and join_date != "":
            is_selected = True
            start_join_date, end_join_date = return_start_end_date(join_date)
            if start_join_date == end_join_date:
                condition.add(Q(provider__member__join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(provider__member__join_date__range=[start_join_date, end_join_date]), Q.AND)

        if isinstance(modf_date, str) and modf_date != "":
            is_selected = True
            start_modf_date, end_modf_date = return_start_end_date(modf_date)
            if start_modf_date == end_modf_date:
                condition.add(Q(provider__member__modf_date__icontains=start_modf_date), Q.AND)
            else:
                condition.add(Q(provider__member__modf_date__range=[start_modf_date, end_modf_date]), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if searched_word is not None and searched_word != '':
            condition.add(Q(provider__member__name__icontains=searched_word) | Q(provider__member__email__icontains=searched_word),
                          Q.AND)

        # sorting 조건 만드는 곳
        sort_condition = ""

        if upDown == '-':
            sort_condition += '-'
        if sort_criterion == 'id':
            sort_condition += 'provider__member_id'
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

        job_talk_qs = JobTalkSource.objects \
            .select_related('dataset') \
            .prefetch_related('provider') \
            .prefetch_related('provider__member__membergrade2member') \
            .filter(condition) \
            .values('dataset__dataset_name', 'provider__member__name', 'provider__member__tel_no',
                    'provider__member__email', 'provider_id', 'provider__limit_count', 'provider__member__membergrade2member__grade_code')\
            .distinct()

        sub_qs = JobTalkSource.objects

        provider_list = job_talk_qs.annotate(total_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(
                provider_id=OuterRef('provider_id'))
        )) \
            .annotate(provider_complete_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(
                provider_id=OuterRef('provider_id')).filter(
                Q(inspection_status=InspectionStatus.Complete) | Q(inspection_status__isnull=InspectionStatus.Reject))
        )) \
            .annotate(inspection_status_initial_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(
                provider_id=OuterRef('provider_id')).filter(
                Q(inspection_status=InspectionStatus.Initial) | Q(inspection_status__isnull=True))
        )) \
            .annotate(inspection_status_complete_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(
                provider_id=OuterRef('provider_id')).filter(Q(inspection_status=InspectionStatus.Complete))
        )) \
            .annotate(inspection_status_reject_count=Subquery(
            sub_qs.values('provider_id').annotate(Count('provider_id')).values('provider_id__count').filter(
                provider_id=OuterRef('provider_id')).filter(Q(inspection_status=InspectionStatus.Reject))
        ))\
        .values_list('dataset__dataset_name', 'provider__member__email', 'provider__member__name', 'provider__member__tel_no', 'provider__member__membergrade2member__grade_code',
                     'total_count', 'provider_complete_count',
                     'inspection_status_initial_count', 'inspection_status_complete_count',
                     'inspection_status_reject_count',
                     'provider__limit_count').order_by(sort_condition)
        print(provider_list.query)
        data_count = provider_list.count()
        plus = 0
        for row in provider_list:
            row_num += 1
            total = None
            for col_num in range(len(row)):
                output_data = row[col_num]
                if col_num == 4:
                    output_data = MemberGrade_Choice.get_value(output_data)
                if col_num == 5 or col_num == 6:
                    if col_num == 5:
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


class TalkProvider(LoginRequiredMixin, FormView):
    template_name = 'job/talk/provider/talk_provider.html'
    form_class = TalkJobManagementForm

    def get_context_data(self, **kwargs):
        context = super(TalkProvider, self).get_context_data(**kwargs)
        member_id = self.request.user.id
        source_id = self.kwargs.get('id')
        context['member_id'] = member_id
        return context



@csrf_exempt
def ProviderSourceSave(request):
    if request.is_ajax():

        src = request.POST.get('src')
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        dataset_id = request.POST.get('dataset_id')

        try:
            with transaction.atomic():
                isUser = User.objects.filter(email=email)

                if len(isUser) == 0:
                    new_user = User()
                    new_user.tel_no = phone
                    new_user.name = name
                    new_user.email = email
                    new_user.save()
                    user_id = User.objects.latest('id')
                else:
                    user_id = isUser[0].id
                try:
                    role_code = User.objects.get(id=user_id, role_code=MemberRole.Provider)
                except Exception as e:
                    return JsonResponse({'result': False, 'error': '대화제공자로 등록된 회원이 아닙니다.'})
                # print(user_id)
                condition = Q()
                condition.add(Q(member=user_id), Q.AND)
                condition.add(Q(dataset_id=dataset_id), Q.AND)
                condition.add(Q(valid_yn=UseType.Y), Q.AND)

                try:
                    provider = Provider.objects.get(condition)
                    provider_id=provider.id
                    # print(provider.limit_yn )

                    limit_count = provider.limit_count
                    check_datetime=datetime.now()
                    current_submit_count = JobTalkSource.objects\
                        .filter(reg_date__year=check_datetime.year, 
                                reg_date__month=check_datetime.month, 
                                reg_date__day=check_datetime.day,
                                provider_id=provider_id,
                                dataset_id=dataset_id)
                    
                    if provider.limit_yn is not None and provider.limit_yn == 'Y':
                        return JsonResponse({'result': False, 'msg': '작업 제한 상태 입니다.'})
                    elif limit_count > 0 and (limit_count <= len(current_submit_count)):
                        return JsonResponse({'result': False, 'msg': '일일작업량을 초과하였습니다.'})
                    else:
                        provider.valid_yn = 'Y'
                        provider.limit_yn = 'N'
                        provider.save()
                except Exception as e:
                    print(e)
                    new_provider = Provider()
                    new_provider.dataset_id = dataset_id
                    new_provider.limit_count = 0
                    new_provider.member = user_id
                    new_provider.valid_yn = 'Y'
                    new_provider.limit_yn = 'N'
                    new_provider.save()
                    provider_id = new_provider.objects.latest('id')

                jobtalksource = JobTalkSource()
                jobtalksource.de_identificated_talk = None
                jobtalksource.de_identificated_status = DeIdentificationStatus.Initial
                jobtalksource.inspection_status = InspectionStatus.Initial
                jobtalksource.provider_id = provider_id
                jobtalksource.talk = src
                jobtalksource.dataset_id = dataset_id
                jobtalksource.save()

                return JsonResponse({'result': True, 'msg': '성공적으로 제출되었습니다.'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    return JsonResponse({'result': False, 'error': '발송 실패'})

