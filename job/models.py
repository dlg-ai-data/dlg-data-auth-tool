from django.db import models

# Create your models here.
from common.choices import JobStatus, InspectionStatus, DeIdentificationStatus, WorkType, QAType, JobSourceType

class JobTalk(models.Model):
    dataset = models.ForeignKey('dataset.Dataset', null=False, on_delete=models.CASCADE, verbose_name='데이터셋ID', related_name='jobtalk2dataset')
    annotator = models.ForeignKey('dataset.Annotator', null=True, on_delete=models.CASCADE, verbose_name='어노테이터ID', related_name='jobtalk2annotator')
    reviewer = models.ForeignKey('dataset.Reviewer', null=True, on_delete=models.CASCADE, verbose_name='리뷰어ID', related_name='jobtalk2reviewer')
    job_talk_source = models.ForeignKey('job.JobTalkSource', null=True, on_delete=models.CASCADE, verbose_name='대화조각원문ID', related_name='jobtalk2jobtalksource')

    job_status = models.CharField(choices=JobStatus.choices, max_length=4, default=JobStatus.Initial, verbose_name='작업상태')
    inspection_status = models.CharField(choices=InspectionStatus.choices, max_length=4, default=InspectionStatus.Initial, verbose_name='검수상태')

    job_date = models.DateTimeField(null=True, verbose_name='작업일자')
    inspection_date = models.DateTimeField(null=True, verbose_name='검수일자')
    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
    mod_date = models.DateTimeField(auto_now=True, verbose_name='최종수정일자')

    reject_msg = models.CharField(max_length=200, null=True, verbose_name='반려메시지')
    reject_count = models.IntegerField(default=0, verbose_name='반려 누적 건수')

    json = models.TextField(null=True, verbose_name='json')

    class Meta:
        db_table = 'job_talk'
        verbose_name = '작업_한국어 대화 조각'

    def __str__(self):
        return str(self.id)

class JobTalkSummary(models.Model):
    job_talk = models.ForeignKey('job.JobTalk', null=False, on_delete=models.CASCADE, verbose_name='작업소스ID', related_name='jobtalksummary2jobtalk')

    seq = models.IntegerField(null=False, verbose_name='문장번호')
    talk_summary = models.TextField(null=False, verbose_name='대화조각')
    talker = models.CharField(null=True, max_length=50, verbose_name='화자')
    qa_type = models.CharField(null=False, choices=QAType.choices,  max_length=4,verbose_name='질문/답변 유형')
    intent_type = models.CharField(max_length=50, verbose_name='질문/답변 의도 유형')
    intent = models.CharField(max_length=50, verbose_name='의도')
    entity = models.CharField(max_length=100, verbose_name='개체')
    thesaurus = models.CharField(max_length=100, verbose_name='용어사전')

    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
    json = models.TextField(null=True, verbose_name='json')

    class Meta:
        db_table = 'job_talk_summary'
        verbose_name = '작업_한국어 대화 조각 요약'

    def __str__(self):
        return str(self.id)

class JobTalkSource(models.Model):
    dataset = models.ForeignKey('dataset.Dataset', null=False, on_delete=models.CASCADE, verbose_name='데이터세트ID', related_name='jobtalksource2dataset')
    provider = models.ForeignKey('dataset.Provider', null=False, on_delete=models.CASCADE, verbose_name='대화제공자ID', related_name='jobtalksource2provider')
    reviewer = models.ForeignKey('dataset.Reviewer', null=True, on_delete=models.CASCADE, verbose_name='리뷰어', related_name='jobtalksource2reviewer')

    talk = models.TextField(null=False, verbose_name='대화조각 원문')
    de_identificated_talk = models.TextField(null=True, verbose_name='비식별화 대화조각')
    de_identificated_status = models.CharField(choices=DeIdentificationStatus.choices, max_length=4, default=DeIdentificationStatus.Initial, verbose_name='비식별화 처리상태')

    domain = models.CharField(null=True, max_length=100, verbose_name='도메인(주제)')
    category = models.CharField(null=True, max_length=100, verbose_name='카테고리')
    talker_count = models.IntegerField(null=True, verbose_name='화자 수')
    turn_talk_count = models.IntegerField(null=True, verbose_name='말차례 수')
    speechbubble_count = models.IntegerField(null=True, verbose_name='말풍선 수')
    empty_speechbubble_count = models.IntegerField(null=True, verbose_name='의미없는 말풍선 수')

    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
    mod_date = models.DateTimeField(auto_now=True, null=True, verbose_name='최종수정일자')
    json = models.TextField(null=True, verbose_name='json')

    inspection_date = models.DateTimeField(null=True, verbose_name='검수일자')
    inspection_status = models.CharField(null=True, choices=InspectionStatus.choices, max_length=4, default=InspectionStatus.Initial, verbose_name='검수상태')
    reject_msg = models.CharField(null=True, max_length=200, verbose_name='반려사유')

    class Meta:
        db_table = 'job_talk_source'
        verbose_name = '작업_대화조각원문'

    def __str__(self):
        return str(self.id)

class JobAnnotratorHistory(models.Model):
    job = models.ForeignKey('job.JobTalk', null=False, on_delete=models.CASCADE, verbose_name='작업일련번호', related_name='jobannotatorhistory2jobtalk')
    annotator = models.ForeignKey('dataset.Annotator', null=False, on_delete=models.CASCADE, verbose_name='어노테이터ID', related_name='jobannotatorhistory2annotrator')
    work_type = models.CharField(choices=WorkType.choices, max_length=4, default=WorkType.Create, verbose_name='작업유형')
    work_text = models.CharField(max_length=4000, null=True, verbose_name='작업내용')

    reg_date = models.DateTimeField(auto_now_add=True, null=True, verbose_name='등록일자')

    job_status = models.CharField(choices=JobStatus.choices, max_length=4, null=True, verbose_name='작업상태')
    inspection_status = models.CharField(choices=InspectionStatus.choices, max_length=4, null=True, verbose_name='검수상태')



    class Meta:
        db_table = 'job_annotator_history'
        verbose_name = '어노테이터 작업이력'

    def __str__(self):
        return str(self.id)
    
    
class JobReviewerHistory(models.Model):
    reviewer = models.ForeignKey('dataset.Reviewer', null=False, on_delete=models.CASCADE, verbose_name='리뷰어ID', related_name='jobreviewerhistory2reviewer')

    job_id = models.IntegerField(null=False, verbose_name='작업일련번호')
    job_source_type = models.CharField(choices=JobSourceType.choices, max_length=4, verbose_name='작업소스유형')
    work_type = models.CharField(choices=WorkType.choices, max_length=4, default=WorkType.Create, verbose_name='작업유형')
    work_text = models.CharField(max_length=4000, null=True, verbose_name='작업내용')

    reg_date = models.DateTimeField(auto_now_add=True, null=True, verbose_name='등록일자')

    job_status = models.CharField(choices=JobStatus.choices, max_length=4, null=True, verbose_name='작업상태')
    inspection_status = models.CharField(choices=InspectionStatus.choices, max_length=4, null=True, verbose_name='검수상태')

    class Meta:
        db_table = 'job_reviewer_history'
        verbose_name = '리뷰어 작업이력'

    def __str__(self):
        return str(self.id)