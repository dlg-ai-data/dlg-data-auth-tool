import datetime
import traceback
import urllib.request as urllib
import re

import xlwt
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, CharField, DateTimeField, OuterRef, Subquery, F, Sum
from django.db.models.functions import TruncSecond, Cast
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from calc.models import Calc, CalcDetail
from common.templatetags.html_extras import get_job_price, get_member_grade, parse_rrn
from common.utils import get_page_range
from vaiv.view import LoginRequiredMixin
from common.choices import UseType, MemberGrade_Choice, BankCode, CalcStatus, CalcType, PayType, PointStatus
from datetime import datetime


class CalcCurrentStateBoardView(LoginRequiredMixin, TemplateView):
    template_name = 'calc/current_state_board.html'

    def get_context_data(self, **kwargs):
        context = super(CalcCurrentStateBoardView, self).get_context_data(**kwargs)

        condition = Q()
        if not self.request.user.is_admin:
            condition.add(Q(member__id=self.request.user.id), Q.AND)
        condition.add(Q(member__secession_yn=UseType.N), Q.AND)

        selected_calc_status = self.request.GET.get('calc_status', None)
        set_calc_date_month = self.request.GET.get('calc_date_month', None)
        selected_bankyn = self.request.GET.get('bankyn', None)
        searched_word = self.request.GET.get('word')
        selected_grade = self.request.GET.get('grade', None)

        # START: set_calc_date_month 파싱 -> date 형식으로 가공
        temp_date = ""
        if isinstance(set_calc_date_month, str) and set_calc_date_month != "":
            temp_date = re.split('년 |월', set_calc_date_month)
            temp_date = temp_date[0] + '-' + temp_date[1]
        # END  : set_calc_date_month 파싱 -> date 형식으로 가공

        is_selected, is_searched = False, False

        if selected_calc_status != "all" and selected_calc_status is not None:
            is_selected = True
            condition.add(Q(calc_status=selected_calc_status), Q.AND)
        if selected_grade is not None and selected_grade != 'all':
            is_selected = True
            condition.add(Q(member__membergrade2member__grade_code=selected_grade), Q.AND)
            condition.add(Q(member__membergrade2member__valid_yn='Y'), Q.AND)

        if selected_bankyn is not None and selected_bankyn != 'all':
            is_selected = True
            if selected_bankyn == UseType.N:
                condition.add(Q(member__memberaddition2member__bank_code=None) | Q(member__memberaddition2member__bank_no=None), Q.AND)
            else:
                condition.add(~(Q(member__memberaddition2member__bank_code=None) | Q(member__memberaddition2member__bank_no=None)), Q.AND)

        if isinstance(temp_date, str) and temp_date != "":
            is_selected = True
            condition.add(Q(calc_date__icontains=temp_date), Q.AND)

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(member__email__icontains=searched_word) | Q(member__name__icontains=searched_word), Q.AND)

        calc_detail_qs = CalcDetail.objects.filter(calc_id=OuterRef('id'))
        calc_qs = Calc.objects.filter(condition) \
            .annotate(price=Subquery(calc_detail_qs.values('calc_id').annotate(Sum('price')).values('price__sum')))

        calc_status_initial_count = calc_qs.filter(calc_status=CalcStatus.Initial).count()
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(calc_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['all_items'] = page_list
        context['record_count'] = calc_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['selected_calc_status'] = selected_calc_status
        context['selected_bankyn'] = selected_bankyn
        context['set_calc_date_month'] = set_calc_date_month
        context['selected_grade'] = selected_grade
        context['page'] = page
        context['blank_count'] \
            = 15 - (calc_qs.count() - 15 * (page - 1)) if calc_qs.count() - 15 * (page - 1) < 15 else 0
        context['calc_status_initial_count'] = calc_status_initial_count
        return context


def current_state_board_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % urllib.quote(
        '정산현황.xls'.encode('utf-8'))
    try:
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('정산현황')

        ws.col(0).width = 30 * 255  # 이메일
        ws.col(2).width = 20 * 255  # 주민등록번호
        ws.col(4).width = 15 * 255  # 은행명
        ws.col(5).width = 20 * 255  # 계좌번호
        ws.col(7).width = 22 * 255  # 정산일자
        ws.col(8).width = 22 * 255  # 지급일자
        ws.col(9).width = 22 * 255  # 등급
        ws.col(10).width = 22 * 255  # 지급금액

        row_num = 1

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['이메일', '이름','정산월', '은행명', '계좌번호', '정산상태', '정산일자', '지급일자', '등급', '지급금액']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        calc_status = request.GET.get('calc_status', None)
        calc_date_month = request.GET.get('calc_date_month', None)
        searched_word = request.GET.get('searched_word', None)
        selected_grade = request.GET.get('member_grade', None)

        condition = Q()
        condition.add(Q(member__secession_yn=UseType.N), Q.AND)

        if calc_status != "all" and calc_status is not None:
            condition.add(Q(calc_status=calc_status), Q.AND)

        if selected_grade != 'all' and selected_grade is not None:
            condition.add(Q(member__membergrade2member__grade_code=selected_grade), Q.AND)
            condition.add(Q(member__membergrade2member__valid_yn=UseType.Y), Q.AND)

        if isinstance(calc_date_month, str) and calc_date_month != "":
            temp_date = re.split('년 |월', calc_date_month)
            temp_date = temp_date[0] + temp_date[1]
            condition.add(Q(calc_month=temp_date), Q.AND)

        if searched_word is not None and searched_word != "":
            condition.add(Q(member__email__icontains=searched_word) | Q(member__name__icontains=searched_word), Q.AND)

        calc_detail_qs = CalcDetail.objects.filter(calc_id=OuterRef('id'))
        calc_qs = Calc.objects.filter(condition) \
            .annotate(price=Subquery(
            calc_detail_qs.values('calc_id').annotate(Sum('price')).values('price__sum')
        )).annotate(format_calc_date=Cast(TruncSecond('calc_date', DateTimeField()), CharField()),
                    format_pay_date=Cast(TruncSecond('pay_date', DateTimeField()), CharField()))

        rows = calc_qs.values_list('member__email', 'member__name', 'calc_month', 'pay_bank_code', 'pay_bank_no',
                                   'calc_status', 'format_calc_date', 'format_pay_date')
        data_count = rows.count()
        rows = list(rows)
        for i in range(len(rows)):
            rows[i] += (get_member_grade(calc_qs[i].member.id), get_job_price(calc_qs[i].id))
        for row in rows:
            row_num += 1
            for col_num in range(len(row)):
                output_data = row[col_num]
                if row[col_num] is None:
                    continue
                if col_num ==3:  # 지급계좌
                    bank_data = BankCode.get_value(row[3])
                    ws.write(row_num, 4, bank_data, font_style)
                    continue
                if col_num == 5:  # 정산상태
                    calc_status = CalcStatus.get_value(output_data)
                    if calc_status == '진행중':
                        ws.write(row_num, col_num, calc_status, xlwt.easyxf('font: color red, bold True;'))
                    else:
                        ws.write(row_num, col_num, calc_status, xlwt.easyxf('font: color blue, bold True;'))
                    continue
                if col_num == 7 and output_data is None:
                    ws.write(row_num, col_num, '미지급', xlwt.easyxf('font: color red, bold True;'))
                    continue
                if col_num == 8:
                    grade = MemberGrade_Choice.get_value(output_data)
                    ws.write(row_num, col_num, grade, font_style)
                    continue
                ws.write(row_num, col_num, output_data, font_style)
        wb.save(response)

    except Exception as e:
        traceback.print_exc()
        return response

    return response


@csrf_exempt
def confirm_calc_pay(request):
    if request.is_ajax():
        pay_date = request.POST.get('pay_date')

        # START: pay_date 파싱 -> 저장 형식 지정
        if isinstance(pay_date, str) and pay_date != "":
            temp_date = re.split('년 |월 |일', pay_date)
            temp_date = temp_date[0] + '-' + temp_date[1] + '-' + temp_date[2] + ' 00:00:00'
            pay_date = datetime.strptime(temp_date, '%Y-%m-%d %H:%M:%S')
        # END  : pay_date 파싱 -> 저장 형식 지정

        try:
            with transaction.atomic():
                calc_qs = Calc.objects.filter(calc_status=CalcStatus.Initial)
                for calc in calc_qs:
                    calc.pay_date = pay_date
                    calc.calc_status = CalcStatus.Complete
                    calc.save()

            return JsonResponse({'result': True, 'error': 'OK'})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


class CalcEventView(LoginRequiredMixin, TemplateView):
    template_name = 'calc/event.html'

    def get_context_data(self, **kwargs):
        context = super(CalcEventView, self).get_context_data(**kwargs)

        condition = Q()

        selected_point_status = self.request.GET.get('point_status', None)
        searched_word = self.request.GET.get('word')

        is_selected, is_searched = False, False

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(event_description__icontains=searched_word) | Q(member__name__icontains=searched_word) | Q(
                member__email__icontains=searched_word), Q.AND)

        point_qs = Point.objects.filter(member_id=OuterRef('member_id'), job_source_id=OuterRef('id'))
        job_event_qs = JobEvent.objects.filter(condition).select_related('member') \
            .annotate(point_status=Subquery(
            point_qs.all().values('point_status')
        )) \
            .order_by('-id')

        if selected_point_status is not None and selected_point_status != 'all':
            is_selected = True
            job_event_qs = job_event_qs.filter(point_status=selected_point_status)

        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(job_event_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['all_items'] = page_list
        context['total_count'] = job_event_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['page'] = page
        context['blank_count'] \
            = 15 - (job_event_qs.count() - 15 * (page - 1)) if job_event_qs.count() - 15 * (page - 1) < 15 else 0
        context['PointStatus'] = PointStatus
        context['selected_point_status'] = selected_point_status
        return context
