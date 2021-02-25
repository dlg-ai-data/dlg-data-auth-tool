from django.db import models
from common.choices import BBSType, BBSContentsType, BBSStatusType, FileType, UseType


class File(models.Model):
    file_path = models.CharField(max_length=200, null=False, verbose_name='파일경로')
    file_name = models.CharField(max_length=100, null=False, verbose_name='파일명')
    org_file_name = models.CharField(max_length=100, null=False, verbose_name='원본 파일명')
    file_size = models.IntegerField(null=False, default=0, verbose_name='파일크기')
    file_type = models.CharField(choices=FileType.choices, max_length=4, null=False, verbose_name='파일유형')
    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')

    class Meta:
        db_table = 'file'
        verbose_name = '파일'
        ordering = ['id']

    def __str__(self):
        return self.org_file_name


class BBS(models.Model):
    member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='bbs2member')
    bbs_type = models.CharField(choices=BBSType.choices, max_length=4, null=False, verbose_name='게시판종류')
    content_type = models.CharField(choices=BBSContentsType.choices, max_length=4, null=True, verbose_name='작성분류')
    title = models.CharField(max_length=500, null=False, verbose_name='제목')
    contents = models.TextField(null=True, verbose_name='내용')
    bbs_status = models.CharField(choices=BBSStatusType.choices, max_length=4, default=BBSStatusType.Writing, verbose_name='작성상태')
    notice_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='공지여부')
    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
    modf_date = models.DateTimeField(auto_now=True, verbose_name='변경일자')
    upper = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, verbose_name='상위 게시판 일련번호', related_name='bbs2bbs')
    file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='첨부파일ID', related_name='bbs2file')

    dataset = models.ForeignKey('dataset.Dataset', null=True, on_delete=models.SET_NULL,  verbose_name='데이터셋ID', related_name='bbs2dataset')

    class Meta:
        db_table = 'bbs'
        verbose_name = '게시판'
        ordering = ['id']

    def __str__(self):
        return str(self.id)