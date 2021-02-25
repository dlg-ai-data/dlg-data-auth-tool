from django.core.management import BaseCommand
from django.db import connection, transaction

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 마지막 정산일 부터 현재까지 작업완료건 insert
        # 반려 및 재작업은 포함되지않음
        cursor = connection.cursor()
        with transaction.atomic():
            cursor.execute("call member_calc()")