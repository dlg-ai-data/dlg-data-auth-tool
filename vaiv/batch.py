import http
import json
import os
import socket
from datetime import timedelta, datetime, date

from django.db import transaction, connection
from django.db.models import Sum, Count, Q, IntegerField, OuterRef, Subquery, Min
from django.db.models.functions import Coalesce

from calc.models import Calc, CalcDetail
from common.choices import InspectionStatus, JobStatus, PointStatus, CalcStatus, CalcType, \
    MemberGrade_Choice, UseType, JoinStatus, JoinType, PayType, WorkType
from common.models import SMSSendHistory
from dataset.models import Dataset, Reviewer, ProjectRequest, Annotator
from job.models import  JobReviewerHistory, JobAnnotratorHistory, JobTalk, JobTalkSummary
from vaiv import settings
from member.models import MemberAddition
'''
def monthly_caclc():
    calc_date = datetime(year=datetime.now().year, month=datetime.now().month, day=1)
    calc_date = calc_date + timedelta(seconds=-1)
    point_qs = Point.objects.filter(Q(reg_date__range=['2020-10-01', calc_date]), Q(point_status=PointStatus.Initial)
                                    , ~Q(grade_code__in=[MemberGrade_Choice.Tester]))

    point_value_qs = point_qs.values('member_id').annotate(
        sum_point_price=Sum('point_price')
    )

    with transaction.atomic():
        for idx, member_point in enumerate(point_value_qs):
            member_id = member_point['member_id']
            sum_point_price = member_point['sum_point_price']
            if sum_point_price >= 35000:
                tax_amount = 0
                vat_amount = 0

                point_pay_request = PointPayRequest.objects.create(member_id=member_id
                                                                   , sum_point_price=sum_point_price
                                                                   , pay_request_date=datetime.now()
                                                                   , pay_confirm_date=datetime.now())
                member_addition = MemberAddition.objects.get(member_id=member_id)
                calc = Calc.objects.create(member_id=member_id
                                           , point_pay_id=point_pay_request.id
                                           , pay_price=sum_point_price
                                           , pay_bank_code=member_addition.bank_code
                                           , pay_bank_no=member_addition.bank_no
                                           , calc_status=CalcStatus.Initial
                                           , calc_date=datetime.now())

                for jdx, point in enumerate(point_qs.filter(member_id=member_id)):
                    if point.project_type == 'AH06':
                        calc_type = CalcType.TAX
                        pay_type = PayType.Monthly
                    else:
                        calc_type = point.dataset.calc_type
                        pay_type = point.dataset.annotator_pay_type

                    if calc_type == CalcType.TAX:
                        tax_amount = tax_amount + point.point_price
                    elif calc_type == CalcType.VAT:
                        vat_amount = vat_amount + point.point_price

                    CalcDetail.objects.create(calc_id=calc.id
                                              , project_type=point.project_type
                                              , job_source_id=point.job_source_id
                                              , dataset_id=point.dataset_id
                                              , calc_type=calc_type
                                              , pay_type=pay_type
                                              , job_price=point.point_price
                                              , price=point.price
                                              , grade_price=point.grade_price
                                              , grade_code=point.grade_code)

                    point.point_pay_id = point_pay_request.id
                    point.point_status = PointStatus.Complete
                    point.save()

                if tax_amount > 0:
                    tax_amount = tax_amount * 0.033
                if vat_amount > 0:
                    vat_amount = vat_amount * 0.01

                calc.tax_price = tax_amount
                calc.vat_price = vat_amount
                calc.save()
'''

def monthly_calc():
    cursor = connection.cursor()
    with transaction.atomic():
        cursor.execute("call member_calc()")