import json
import traceback

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, FilteredRelation, OuterRef
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from datetime import date, datetime, timedelta
from common.choices import UseType, MemberGrade_Choice, JoinStatus
from common.templatetags.html_extras import return_start_end_date
from common.utils import get_page_range
from dataset.models import Dataset, DatasetGrade
from dataset.models import Annotator, Reviewer
from vaiv.view import LoginRequiredMixin
from member.models import MemberAddition, MemberGrade

class DatasetsView(LoginRequiredMixin, TemplateView):
    template_name = 'dataset/dataset_list.html'

    def get_context_data(self, **kwargs):
        context = super(DatasetsView, self).get_context_data(**kwargs)

        condition = Q()
        condition.add(Q(), Q.AND)

        selected_calc_type = self.request.GET.get('calc_type', None)
        selected_annotator_pay_type = self.request.GET.get('annotator_pay_type', None)
        selected_reviewer_pay_type = self.request.GET.get('reviewer_pay_type', None)
        searched_word = self.request.GET.get('word')

        is_selected, is_searched = False, False

        if selected_calc_type != "all" and selected_calc_type is not None:
            is_selected = True
            condition.add(Q(calc_type=selected_calc_type), Q.AND)

        if selected_annotator_pay_type != "all" and selected_annotator_pay_type is not None:
            is_selected = True
            condition.add(Q(annotator_pay_type=selected_annotator_pay_type), Q.AND)

        if selected_reviewer_pay_type != "all" and selected_reviewer_pay_type is not None:
            is_selected = True
            condition.add(Q(reviewer_pay_type=selected_reviewer_pay_type), Q.AND)

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(dataset_name__icontains=searched_word) | Q(request_orga__icontains=searched_word) | Q(
                price__icontains=searched_word), Q.AND)

        dataset_qs = Dataset.objects.filter(condition).order_by('-id')
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(dataset_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)
        context['all_datasets'] = page_list
        context['dataset_count'] = dataset_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['selected_calc_type'] = selected_calc_type
        context['selected_annotator_pay_type'] = selected_annotator_pay_type
        context['selected_reviewer_pay_type'] = selected_reviewer_pay_type
        context['page'] = page
        context['blank_count'] \
            = 15 - (dataset_qs.count() - 15 * (page - 1)) if dataset_qs.count() - 15 * (page - 1) < 15 else 0
        return context


class DatasetRequestView(LoginRequiredMixin, TemplateView):
    template_name = 'dataset/dataset_request_list.html'

    def get_context_data(self, **kwargs):
        context = super(DatasetRequestView, self).get_context_data(**kwargs)

        selected_request_status = self.request.GET.get('request_status', None)
        selected_request_type = self.request.GET.get('request_type', None)
        dataset_ids = self.request.GET.getlist('dataset_ids', None)
        join_source = self.request.GET.get('join_source', None)
        join_date = self.request.GET.get('join_date', None)
        modf_date = self.request.GET.get('modf_date', None)
        searched_word = self.request.GET.get('word')

        sort_criterion = self.request.GET.get('sort_criterion', 'id')
        upDown = self.request.GET.get('upDown', '-')

        is_selected, is_searched = False, False

        condition = Q()
        condition.add(Q(member__secession_yn=UseType.N), Q.AND)

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

        if selected_request_status != "all" and selected_request_status is not None:
            is_selected = True
            condition.add(Q(request_status=selected_request_status), Q.AND)

        if selected_request_type != "all" and selected_request_type is not None:
            is_selected = True
            condition.add(Q(request_type=selected_request_type), Q.AND)

        if dataset_ids and 'all' not in dataset_ids:
            is_selected = True
            condition.add(Q(dataset__id__in=dataset_ids), Q.AND)

        if join_source is not None and join_source != 'all':
            is_selected = True
            condition.add(Q(member__memberaddition2member__member_join_source=join_source), Q.AND)

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(member__name__icontains=searched_word) | Q(member__email__icontains=searched_word) | Q(
                dataset__dataset_name__icontains=searched_word), Q.AND)

        # sorting 조건 만드는 곳
        sort_condition = ""

        if upDown == '-':
            sort_condition += '-'

        if sort_criterion == 'id':
            sort_condition += 'id'
        elif sort_criterion == 'email':
            sort_condition += "member__email"
        elif sort_criterion == 'name':
            sort_condition += "member__name"
        elif sort_criterion == 'join_source':
            sort_condition += "member__memberaddition2member__member_join_source"
        elif sort_criterion == 'member_grade':
            sort_condition += "member__membergrade2user__grade_code"
        elif sort_criterion == 'dataset_name':
            sort_condition += "dataset__dataset_name"
        elif sort_criterion == 'request_type':
            sort_condition += "request_type"
        elif sort_criterion == 'request_status':
            sort_condition += "request_status"
        elif sort_criterion == 'request_date':
            sort_condition += "request_date"
        #
        # request_qs = ProjectRequest.objects \
        #     .extra(tables=['dataset', 'member', 'member_grade']
        #            , where=['dataset.id=project_request.dataset_id'
        #         , 'project_request.member_id=member.id'
        #         , 'member.id=member_grade.member_id']) \
        #     .filter(condition).order_by(sort_condition)
        #
        # page = int(self.request.GET.get('page', 1))
        # paginator = Paginator(request_qs, 15)
        # page_list = paginator.get_page(page)
        # paginator_range = get_page_range(paginator, page)
        #
        # # 일괄 승인 또는 반려를 하는 데 있어서 조건에 맞는 레코드의 아이디 모아줌.
        # current_page_acceptable_request_obj_list = []
        # for item in page_list:
        #     if item.request_status == "AV01" and item.member.memberaddition2member.age_code is not None:
        #         request_obj = {
        #             "id": item.id,  # request_id
        #             "member_id": item.member.id,
        #             "request_type": item.request_type,
        #             "dataset_id": item.dataset.id,
        #         }
        #         current_page_acceptable_request_obj_list.append(request_obj)
        #
        # context['all_requests'] = page_list
        # context['request_count'] = request_qs.count()
        # context['isSelected'] = is_selected
        # context['isSearched'] = is_searched
        # context['searched_word'] = searched_word
        # context['paginator_range'] = paginator_range
        #
        # context['selected_request_status'] = selected_request_status
        # context['selected_request_type'] = selected_request_type
        # context['dataset_ids'] = dataset_ids
        # context['selected_join_source'] = join_source
        # context['join_date'] = join_date
        # context['modf_date'] = modf_date
        # context['page'] = page
        # context['blank_count'] \
        #     = 15 - (request_qs.count() - 15 * (page - 1)) if request_qs.count() - 15 * (page - 1) < 15 else 0
        # context['current_page_acceptable_request_obj_list'] = current_page_acceptable_request_obj_list
        # context['sort_criterion'] = sort_criterion
        # context['upDown'] = upDown
        return context


class DatasetOverallSettingView(LoginRequiredMixin, TemplateView):
    template_name = 'dataset/dataset_overall_setting.html'

    def get_context_data(self, **kwargs):

        dataset_id = self.kwargs.get('id')

        context = super(DatasetOverallSettingView, self).get_context_data(**kwargs)

        # 해당 데이터세트의 전체 정보를 받아온다.
        context['dataset_detail'] = Dataset.objects.get(id=dataset_id)

        # 해당 데이터세트와 연관된 등급 정보를 가져온다.
        context['dataset_grade'] = DatasetGrade.objects.filter(dataset_id=dataset_id)
        return context


@csrf_exempt
def modify_dataset(request):
    if request.is_ajax():

        result = True

        id = request.POST.get('id', None)
        dataset_name = request.POST.get('dataset_name', None)
        request_orga = request.POST.get('request_orga', None)
        job_start_end_date = request.POST.get('job_start_end_date', None)
        price = request.POST.get('price', None)
        calc_type = request.POST.get('calc_type', None)
        annotator_pay_type = request.POST.get('annotator_pay_type', None)
        reviewer_pay_type = request.POST.get('reviewer_pay_type', None)
        grade_id = request.POST.getlist('grade_id')
        grade_code = request.POST.getlist('grade_code')
        job_use_yn = request.POST.getlist('job_use_yn')
        grade_price = request.POST.getlist('grade_price')

        terms = request.POST.get('terms', None)
        progress_value = request.POST.get('progress_value', 0)

        progress_value = '0' if progress_value == '' else progress_value

        # START: 금액 예외 처리 구간
        price = '0' if price == '' else price
        if isinstance(price, str) and price != "":
            price = price.replace(",", "")

        for i in range(len(grade_price)):
            grade_price[i] = '0' if grade_price[i] == '' else grade_price[i]
            if isinstance(grade_price[i], str) and grade_price[i] != "":
                grade_price[i] = grade_price[i].replace(',', '')
        # END  : 금액 예외 처리 구간

        start_job_start_end_date, end_job_start_end_date = None, None

        if isinstance(job_start_end_date, str) and job_start_end_date != "":
            temp = job_start_end_date.split(" ")
            start_job_start_end_date = temp[0]
            end_job_start_end_date = temp[2]

        try:
            with transaction.atomic():
                dataset = Dataset.objects.get(id=id)
                dataset.dataset_name = dataset_name
                dataset.request_orga = request_orga
                dataset.job_start_date = start_job_start_end_date
                dataset.job_end_date = end_job_start_end_date
                dataset.price = price
                dataset.calc_type = calc_type
                dataset.annotator_pay_type = annotator_pay_type
                dataset.reviewer_pay_type = reviewer_pay_type
                dataset.terms = terms
                dataset.progress_value = progress_value
                dataset.save()

                test_job_yn = UseType.N

                for idx, grade in enumerate(grade_id):
                    dataset_grade = DatasetGrade.objects.get(id=grade)
                    if grade_code[idx] != dataset_grade.grade_code:
                        raise Exception('데이터세트 등급에 문제가 발생함')

                    dataset_grade.job_use_yn = job_use_yn[idx]
                    dataset_grade.grade_price = grade_price[idx]
                    dataset_grade.save()

                return JsonResponse({'result': result})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def register_dataset(request):
    if request.is_ajax():
        result = True
        dataset_name = request.POST.get('dataset_name', None)
        try:
            with transaction.atomic():

                new_dataset = Dataset.objects.create(dataset_name=dataset_name)
                for key, val in MemberGrade_Choice.choices:
                    DatasetGrade.objects.create(grade_code=key, job_use_yn=UseType.N, grade_price=0,
                                                dataset_id=new_dataset.id)

                return JsonResponse({'result': result, 'id': new_dataset.id})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def approve_dataset(request):
    if request.is_ajax():
        request_id, member_id, dataset_id, request_type, current_page_acceptable_request_obj_list = None, None, None, None, None
        if request.method == "GET":
            request_id = request.GET.get("id")
            member_id = request.GET.get("member_id")
            dataset_id = request.GET.get("dataset_id")
            request_type = request.GET.get("request_type")
        else:
            current_page_acceptable_request_obj_list = json.loads(
                request.POST['current_page_acceptable_request_obj_list'])
        result = True
        error = ""
        try:
            with transaction.atomic():

                if not current_page_acceptable_request_obj_list:

                    # 개별 승인
                    datasetRequest = ProjectRequest.objects.get(id=request_id)
                    datasetRequest.request_status = JoinStatus.Complete
                    datasetRequest.approval_member_id = request.user.id
                    datasetRequest.save()

                    member_addition = MemberAddition.objects.get(member_id=member_id)
                    if member_addition.adm_yn == UseType.N:
                        member_addition.adm_yn = UseType.Y
                        member_addition.save()

                    if request_type == "AU01":
                        if Annotator.objects.filter(dataset_id=dataset_id, member_id=member_id).count() >= 1:
                            result = False
                            error = "이미 승인 처리된 데이터세트입니다. 화면을 새로고침합니다."
                        else:
                            limit_count = 2

                            Annotator.objects.create(limit_count=limit_count, dataset_id=dataset_id, member_id=member_id)
                    elif request_type == "AU02":
                        if Reviewer.objects.filter(dataset_id=dataset_id, member_id=member_id).count() >= 1:
                            result = False
                            error = "이미 승인 처리된 데이터세트입니다. 화면을 새로고침합니다."
                        else:
                            Reviewer.objects.create(limit_count=0, dataset_id=dataset_id, member_id=member_id)
                else:
                    # 일괄 승인
                    for item in current_page_acceptable_request_obj_list:

                        datasetRequest = ProjectRequest.objects.get(id=item['id'])
                        datasetRequest.request_status = JoinStatus.Complete
                        datasetRequest.approval_member_id = request.user.id
                        datasetRequest.save()

                        member_addition = MemberAddition.objects.get(member_id=item['member_id'])
                        if member_addition.adm_yn == UseType.N:
                            member_addition.adm_yn = UseType.Y
                            member_addition.save()

                        if item['request_type'] == "AU01":
                            limit_count = 2

                            if Annotator.objects.filter(dataset_id=item['dataset_id'],
                                                        member_id=item['member_id']).count() < 1:
                                Annotator.objects.create(limit_count=limit_count, dataset_id=item['dataset_id'],
                                                         member_id=item['member_id'])
                        elif item['request_type'] == "AU02":
                            if Reviewer.objects.filter(dataset_id=item['dataset_id'],
                                                       member_id=item['member_id']).count() < 1:
                                Reviewer.objects.create(limit_count=0, dataset_id=item['dataset_id'],
                                                        member_id=item['member_id'])

                return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})

    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def reject_dataset(request):
    if request.is_ajax():
        id, current_page_acceptable_request_obj_list = None, None
        if request.method == "GET":
            id = request.GET.get("id")
        else:
            current_page_acceptable_request_obj_list = json.loads(
                request.POST['current_page_acceptable_request_obj_list'])
        result = True
        error = ""
        try:
            with transaction.atomic():
                if not current_page_acceptable_request_obj_list:
                    # 개별 반려
                    datasetRequest = ProjectRequest.objects.get(id=id)
                    datasetRequest.request_status = ProjectJoinStatus.Reject
                    datasetRequest.approval_member_id = request.user.id
                    datasetRequest.save()

                else:
                    # 일괄 반려
                    for item in current_page_acceptable_request_obj_list:
                        datasetRequest = ProjectRequest.objects.get(id=item['id'])
                        datasetRequest.request_status = ProjectJoinStatus.Reject
                        datasetRequest.approval_member_id = request.user.id
                        datasetRequest.save()

                return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})

    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def modify_dataset_label(request):
    if request.is_ajax():
        if request.method == 'POST':
            new_labels_data = json.loads(request.body)

        dataset_id = new_labels_data["dataset_id"]
        result = True
        try:
            with transaction.atomic():

                use_yn_check_label_id_list = new_labels_data["use_yn_check_label_id_list"]
                models = DatasetLabel.objects.filter(dataset_id=dataset_id)
                for model in models:
                    if model.id not in use_yn_check_label_id_list:
                        model.use_yn = UseType.N
                    else:
                        model.use_yn = UseType.Y
                    model.save()

                color_change_label_id_and_color_list = new_labels_data["color_change_label_id_and_color_list"]
                for item in color_change_label_id_and_color_list:
                    label = DatasetLabel.objects.get(id=item["label_id"])
                    label.color = item["color"]
                    label.save()

                for key, value in new_labels_data.items():
                    if key != "dataset_id" and key != "use_yn_check_label_id_list" and key != "color_change_label_id_and_color_list":
                        for item in value:
                            if item["label"] == "":
                                return JsonResponse({'result': False, 'error': "레이블 이름은 공백일 수 없습니다."})
                            models = DatasetLabel.objects.filter(dataset_id=dataset_id, label_type=key)
                            for model in models:
                                if model.label == item["label"]:
                                    return JsonResponse({'result': False, 'error': "레이블 이름이 중복됩니다. 수정하세요."})
                            DatasetLabel.objects.create(dataset_id=dataset_id, label=item["label"], color=item["color"],
                                                        use_yn=item["use_yn"], label_type=key)

                return JsonResponse({'result': result})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


class DatasetSetView(LoginRequiredMixin, TemplateView):
    template_name = 'partials/dataset_info_set.html'

    def get_context_data(self, **kwargs):
        context = super(DatasetSetView, self).get_context_data(**kwargs)
        context['dataset_detail'] = Dataset.objects.get(id=self.kwargs.get('id'))
        context['dataset_grade'] = DatasetGrade.objects.filter(dataset_id=self.kwargs.get('id'))
        return context


class DatasetDisplayView(LoginRequiredMixin, TemplateView):
    template_name = 'partials/dataset_info_display.html'

    def get_context_data(self, **kwargs):
        context = super(DatasetDisplayView, self).get_context_data(**kwargs)
        context['dataset_detail'] = Dataset.objects.get(id=self.kwargs.get('id'))
        context['dataset_grade'] = DatasetGrade.objects.filter(dataset_id=self.kwargs.get('id'))
        return context


@csrf_exempt
def dataset_info_set_html_return(request):
    if request.is_ajax():
        dataset_id = request.POST.get('dataset_id')
        context = DatasetSetView(kwargs={'id': dataset_id}).get_context_data()
        html = render_to_string('partials/dataset_info_set.html', context)

        return HttpResponse(html)
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def dataset_info_display_html_return(request):
    if request.is_ajax():
        dataset_id = request.POST.get('dataset_id')
        context = DatasetDisplayView(kwargs={'id': dataset_id}).get_context_data()
        html = render_to_string('partials/dataset_info_display.html', context)

        return HttpResponse(html)
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})
