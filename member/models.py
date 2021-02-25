import hashlib

from django.contrib.auth.models import (
    BaseUserManager, AbstractBaseUser, PermissionsMixin
)
from django.db import models
from django.utils.translation import ugettext_lazy as _
from common.choices import MemberGrade_Choice, MemberRole, BankCode, UseType, GenderType, AgeType, JobJoinType, MemberJobType, MemberJoinSource, AuthCertStatus


class UserManager(BaseUserManager):
    def create_user(self, email, password, name):
        user = self.model(
            name=name,
            email=self.normalize_email(email)
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, name):
        user = self.create_user(
            password=password,
            name=name,
            email=self.normalize_email(email)
        )

        user.is_superuser = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    email = models.EmailField(max_length=50, unique=True, null=False, verbose_name='이메일')
    name = models.CharField(max_length=20, null=False, verbose_name='이름')
    tel_no = models.CharField(max_length=20, null=True, verbose_name='연락처')
    zipcode = models.CharField(max_length=5, null=True, verbose_name='우편번호')
    addr = models.CharField(max_length=200, null=True, verbose_name='주소')
    addr_detail = models.CharField(max_length=200, null=True, verbose_name='상세주소')
    sms_rect_yn = models.CharField(max_length=1, default='N', verbose_name='SMS 수신여부')

    join_date = models.DateTimeField(auto_now_add=True, verbose_name='가입일자')
    secession_yn = models.CharField(max_length=1, default='N', verbose_name='탈퇴여부')
    modf_date = models.DateTimeField(auto_now=True, verbose_name='변경일자')

    is_active = models.BooleanField(default=False, verbose_name='활성화여부')
    is_admin = models.BooleanField(default=False, verbose_name='관리자여부')
    role_code = models.CharField(choices=MemberRole.choices, max_length=4, default=MemberRole.Annotrator, verbose_name='역할')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', ]

    class Meta:
        db_table = 'member'
        verbose_name = '회원'
        ordering = ['-join_date']

    def __str__(self):
        return self.email

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def set_password(self, raw_password):
        hashSHA = hashlib.sha256()
        hashSHA.update(raw_password.encode('utf-8'))
        hexSHA256 = hashSHA.hexdigest()
        self.password = hexSHA256

    def check_password(self, raw_password):
        try:
            user = User.objects.get(email=self.email)
            hashSHA = hashlib.sha256()
            hashSHA.update(raw_password.encode('utf-8'))
            hexSHA256 = hashSHA.hexdigest()

            # print(hexSHA256)
            # print(user.password)

            if user.password == hexSHA256:
                return True
            else:
                return False
        except User.DoesNotExist:
            return False

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All superusers are staff
        return self.is_superuser

    get_full_name.short_description = _('Full name')


class MemberGrade(models.Model):
    member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='membergrade2member')

    grade_code = models.CharField(choices=MemberGrade_Choice.choices, max_length=4, default=MemberGrade_Choice.Beginner, verbose_name='등급')
    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
    valid_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N)

    def get_member_grade_color(self):
        if self.grade_code == MemberGrade_Choice.Beginner:
            return 'label-success'
        elif self.grade_code == MemberGrade_Choice.Intermediate:
            return 'label-warning'
        elif self.grade_code == MemberGrade_Choice.Advanced:
            return 'label-primary'
        elif self.grade_code == MemberGrade_Choice.Provider:
            return 'label-danger'

    class Meta:
        db_table = 'member_grade'
        verbose_name = '회원등급'
        ordering = ['member_id']

    def __str__(self):
        return str(self.member_id)


class LoginHistory(models.Model):
    member = models.ForeignKey('member.User', null=False, on_delete=models.CASCADE, verbose_name='회원ID', related_name='loginhistory2member')
    login_date = models.DateTimeField(auto_now_add=False, verbose_name='로그인일자')
    user_agent = models.CharField(max_length=1000, null=False, verbose_name='로그인 기기정보')
    ip_addr = models.GenericIPAddressField(null=False)

    class Meta:
        db_table = 'login_history'
        verbose_name = '로그인이력'

    def __str__(self):
        return str(self.member_id)


class MemberAddition(models.Model):
    member = models.OneToOneField('member.User', primary_key=True, on_delete=models.CASCADE, verbose_name='회원ID', related_name='memberaddition2member')

    gender_code = models.CharField(choices=GenderType.choices, max_length=4, null=True, verbose_name='성별코드')
    age_code = models.CharField(choices=AgeType.choices, max_length=4, null=True, verbose_name='나이코드')
    job_join_type = models.CharField(choices=JobJoinType.choices, max_length=4, null=True, verbose_name='참여사유')
    work_time_type = models.CharField(max_length=50, null=True, verbose_name='작업시간')
    member_job_type = models.CharField(choices=MemberJobType.choices, max_length=4, null=True, verbose_name='직업')
    member_join_source = models.CharField(choices=MemberJoinSource.choices, max_length=4, null=True, verbose_name='가입경로')

    disabled_person_yn = models.CharField(choices=UseType.choices, max_length=1, null=True, default=UseType.N, verbose_name='장애인여부')

    rrn = models.CharField(max_length=100, null=True, verbose_name='주민등록번호(암호화)')
    bank_code = models.CharField(choices=BankCode.choices, max_length=4, null=True, verbose_name='은행코드')
    bank_no = models.CharField(max_length=50, null=True, verbose_name='계좌번호')
    reg_date = models.DateTimeField(auto_now_add=True, verbose_name='등록일자')
    adm_yn = models.CharField(choices=UseType.choices, max_length=1, default=UseType.N, verbose_name='승인여부')
    # dup_code = models.CharField(max_length=100, null=True, verbose_name='실명인증코드')

    contract_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='계약서 첨부파일ID', related_name='contract2file')
    bankbook_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='통장사본 첨부파일ID', related_name='bankbook2file')
    identification_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='신분서류 첨부파일ID', related_name='identification2file')
    disabled_person_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='장애증빙 첨부파일ID', related_name='disabled_person2file')
    resume_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='이력서 첨부파일ID', related_name='resume_file2file')
    agree_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='동의서 첨부파일ID', related_name='agree_file2file')
    family_certificate_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='가족관계 첨부파일ID', related_name='family_certificate_file2file')
    parents_agree_file = models.ForeignKey('common.File', on_delete=models.SET_NULL, null=True, verbose_name='부모동의서 첨부파일ID', related_name='parents_agree_file2file')
    
    certification_status = models.CharField(choices=AuthCertStatus.choices, max_length=4, null=True, verbose_name='실명인증상태')

    memo = models.CharField(max_length=500, null=True, verbose_name='메모')

    class Meta:
        db_table = 'member_addition'
        verbose_name = '회원부가정보'
        ordering = ['member_id']

