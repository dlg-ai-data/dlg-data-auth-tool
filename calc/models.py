from django.db import models
from common.choices import BankCode, CalcStatus, CalcType, PayType, MemberGrade_Choice, JobSourceType

    
class Calc(models.Model):
    member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='calc2user')

    calc_month = models.IntegerField(null=False, verbose_name='정산월')
    pay_price = models.IntegerField(null=False, default=0, verbose_name='총지급금액')
    vat_price = models.IntegerField(null=False, default=0, verbose_name='부가세금액')
    tax_price = models.IntegerField(null=False, default=0, verbose_name='세금금액')

    pay_bank_code = models.CharField(choices=BankCode.choices, max_length=4, null=True, verbose_name='지급은행')
    pay_bank_no = models.CharField(null=True, max_length=50, verbose_name='지급계좌번호')

    calc_status = models.CharField(choices=CalcStatus.choices, max_length=4, default=CalcStatus.Initial, verbose_name='정산상태')
    calc_date = models.DateTimeField(auto_now_add=True, verbose_name='정산일자')

    pay_date = models.DateTimeField(null=True, verbose_name='지급일자')

    class Meta:
        db_table = 'calc'
        verbose_name = '정산'

    def __str__(self):
        return str(self.member_id)


class CalcDetail(models.Model):
    dataset = models.ForeignKey('dataset.Dataset', null=True, on_delete=models.SET_NULL, verbose_name='데이터셋ID', related_name='calcdetail2dataset')
    calc = models.ForeignKey('calc.Calc', null=False, on_delete=models.CASCADE, verbose_name='정산ID', related_name='calcdetail2calc')
    job_id = models.IntegerField(null=False, verbose_name='작업소스에따라 원문/요약')

    job_price = models.IntegerField(null=False, default=0, verbose_name='작업 금액')
    price = models.IntegerField(null=False, default=0, verbose_name='단가')
    grade_price = models.IntegerField(null=False, default=0, verbose_name='등급단가')
    grade_code = models.CharField(choices=MemberGrade_Choice.choices, max_length=4, null=True, verbose_name='등급')
    calc_type = models.CharField(choices=CalcType.choices, max_length=4, null=CalcType.VAT, verbose_name='정산유형')
    pay_type = models.CharField(choices=PayType.choices, max_length=4, default=PayType.Monthly, verbose_name='지급방식')
    job_source_type = models.CharField(choices=JobSourceType.choices, max_length=4, verbose_name='작업소스유형')
    class Meta:
        db_table = 'calc_detail'
        verbose_name = '정산 상세'

    def __str__(self):
        return str(self.calc_id)