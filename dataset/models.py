from django.db import models

from common.choices import PayType, UseType, MemberGrade_Choice, CalcType, JobSourceType

class Dataset(models.Model):
  dataset_name = models.CharField(max_length=100, null=False, verbose_name='데이터세트명')
  request_orga = models.CharField(max_length=100, null=False, verbose_name='요청기관(기업)')
  job_start_date = models.DateField(null=True, verbose_name='작업시작일자')
  job_end_date = models.DateField(null=True, verbose_name='작업종료일자')
  reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
  provider_pay_type = models.CharField(choices=PayType.choices, max_length=4, default=PayType.Monthly, verbose_name='대화제공자 지급방식')
  annotator_pay_type = models.CharField(choices=PayType.choices, max_length=4, default=PayType.Monthly, verbose_name='어노테이터 지급방식')
  reviewer_pay_type = models.CharField(choices=PayType.choices, max_length=4, default=PayType.Monthly, verbose_name='리뷰어 지급방식')
  price = models.IntegerField(default=0, verbose_name='단가')
  modf_date = models.DateTimeField(auto_now=True, verbose_name='변경일자')

  terms = models.TextField(null=True, verbose_name='약관')
  dataset_desc = models.CharField(null=True, max_length=200, verbose_name='설명')
  progress_value = models.IntegerField(default=0, verbose_name='진행율')

  class Meta:
    db_table = 'dataset'
    verbose_name = '데이터세트'

  def __str__(self):
    return self.dataset_name

class DatasetGrade(models.Model):
  dataset = models.ForeignKey('dataset.Dataset', null=False, on_delete=models.CASCADE, verbose_name='데이터셋ID', related_name='datasetgrade2dataset')
  grade_code = models.CharField(choices=MemberGrade_Choice.choices, max_length=4, default=MemberGrade_Choice.Beginner, verbose_name='등급')
  job_use_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='작업가능여부')
  grade_price = models.IntegerField(default=0, verbose_name='등급단가')

  class Meta:
    db_table = 'dataset_grade'
    verbose_name = '데이터세트 등급'
    ordering = ['dataset_id']

  def __str__(self):
    return '{}-{}'.format(self.dataset_id, self.id)

class Annotator(models.Model):
  member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='annotrator2user')
  dataset = models.ForeignKey('dataset.Dataset', null=False, on_delete=models.CASCADE, verbose_name='데이터셋ID', related_name='annotator2dataset')
  limit_count = models.IntegerField(null=False, verbose_name='제한량')
  modf_date = models.DateTimeField(auto_now=True, verbose_name='변경일자')

  limit_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='제한여부')
  valid_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='유효여부')

  class Meta:
    db_table = 'annotator'
    verbose_name = '어노테이터'
    ordering = ['member_id', 'dataset_id']

  def __str__(self):
    return '{}-{}'.format(self.member_id, self.dataset_id)


class Reviewer(models.Model):
  member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='reviewer2user')
  dataset = models.ForeignKey('dataset.Dataset', null=False, on_delete=models.CASCADE, verbose_name='데이터셋ID', related_name='reviewer2dataset')
  limit_count = models.IntegerField(null=False, verbose_name='제한량')
  modf_date = models.DateTimeField(auto_now=True, verbose_name='변경일자')
  limit_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='제한여부')
  valid_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='유효여부')
  class Meta:
    db_table = 'reviewer'
    verbose_name = '리뷰어'
    ordering = ['member_id', 'dataset_id']

  def __str__(self):
    return '{}-{}'.format(self.member_id, self.dataset_id)

class Provider(models.Model):
  member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='provider2user')
  dataset = models.ForeignKey('dataset.Dataset', null=False, on_delete=models.CASCADE, verbose_name='데이터셋ID', related_name='provider2dataset')
  limit_count = models.IntegerField(null=False, verbose_name='제한량', default=0)
  modf_date = models.DateTimeField(auto_now=True, verbose_name='변경일자')

  limit_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='제한여부')
  valid_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.Y, verbose_name='유효여부')

  class Meta:
    db_table = 'provider'
    verbose_name = '대화제공자'
    ordering = ['member_id', 'dataset_id']

  def __str__(self):
    return '{}-{}'.format(self.member_id, self.dataset_id)