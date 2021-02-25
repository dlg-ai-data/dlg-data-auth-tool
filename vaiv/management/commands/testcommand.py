from django.core.management import BaseCommand
from django.db.models import Count

from calc.models import Calc, CalcDetail
from dataset.models import Annotator, Reviewer, Provider
from member.models import MemberGrade
from job.models import JobTalkSource
from common.choices import InspectionStatus
class Command(BaseCommand):
    def handle(self, *args, **options):
        #1. Provider 정산
        #2. Annotator 정산
        #3. Reviewer 정산
        #정산기준 : 마지막 정산일~25일
        #등급변경된거 산정해야함
        self.calc_provider()

    def calc_provider(self):
        #제출내역 / 승인완료 / 데이터세트
        provider=JobTalkSource.objects.filter(inspection_status=InspectionStatus.Complete, reg_date__year=2021, reg_date__month__lt= 1).values('dataset_id', 'provider_id', 'reg_date__year', 'reg_date__month').annotate(job_count=Count('id'))\
        .values('dataset_id', 'provider_id', 'reg_date__year', 'reg_date__month', 'job_count')


        print(provider)
        pass

    def calc_annotator(self):
        pass

    def calc_reviewer(self):
        pass