import datetime
import json
import traceback
import urllib.request as urllib
import pandas as pd
import xlwt
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Case, When, CharField, IntegerField, DateTimeField
from django.db.models.functions import TruncSecond, Cast
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, TemplateView
from django.shortcuts import redirect
from datetime import date, timedelta

from common.templatetags.html_extras import parse_rrn
from common.utils import get_page_range
from dataset.models import Annotator, Reviewer, Provider,Dataset
from vaiv.view import LoginRequiredMixin
from member.form import LoginForm
from member.models import User, MemberGrade
from common.choices import UseType, GenderType, MemberRole, AgeType, \
    MemberJoinSource, MemberGrade_Choice, InspectionStatus, JoinStatus
from common.models import File
from common.utils import handler_file_write
from member.models import MemberAddition
from common.AESCipher import AESCipher
from datetime import datetime
import uuid
import http.client


class LoginView(FormView):
    template_name = 'login.html'
    form_class = LoginForm
    success_url = '/'

    def form_valid(self, form):

        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')

        if not (email and password):
            msg = '아이디 및 패스워드가 입력되지 않았습니다.'
        else:
            user = authenticate(email=email, password=password)
            if user is not None:
                if user.is_admin or user.role_code == MemberRole.Annotrator or user.role_code == MemberRole.SummaryReviewer or user.role_code == MemberRole.Reviewer or user.role_code == MemberRole.Provider:
                    login(request=self.request, user=user)
                    return redirect(reverse_lazy('main'))
                else:
                    msg = '권한이 없습니다.'
            else:
                msg = '회원정보가 일치하지 않습니다.'
        context = {'form': form, 'msg': msg}
        return render(self.request, self.template_name, context)


class MemberRegister(LoginRequiredMixin, TemplateView):
    template_name = 'member/member_register.html'

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_admin:
            return redirect(reverse("common:check_auth_valid"))
        return super().get(self, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MemberRegister, self).get_context_data(**kwargs)

        return context


class MemberList(LoginRequiredMixin, TemplateView):
    template_name = 'member/member_list.html'

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_admin:
            return redirect(reverse("common:check_auth_valid"))
        return super().get(self, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MemberList, self).get_context_data(**kwargs)

        condition = Q()
        condition.add(Q(secession_yn=UseType.N), Q.AND)

        searched_word = self.request.GET.get('word')
        selected_admyn = self.request.GET.get('admyn', None)
        selected_sms_rect_yn = self.request.GET.get('sms_rect_yn', None)
        selected_join_source = self.request.GET.get('join_source', None)
        set_up_join_date = self.request.GET.get('join_date', None)

        start_join_date, end_join_date = None, None

        if isinstance(set_up_join_date, str) and set_up_join_date != "":
            temp = set_up_join_date.split(" ")
            start_join_date = temp[0].split("-")
            end_join_date = temp[2].split("-")

            start_join_date = date(int(start_join_date[0]), int(start_join_date[1]), int(start_join_date[2]))
            end_join_date = date(int(end_join_date[0]), int(end_join_date[1]), int(end_join_date[2])) + timedelta(
                days=1)

        is_selected, is_searched = False, False

        if selected_admyn != "all" and selected_admyn is not None:
            is_selected = True
            condition.add(Q(memberaddition2member__adm_yn=selected_admyn), Q.AND)

        if selected_sms_rect_yn != "all" and selected_sms_rect_yn is not None:
            is_selected = True
            condition.add(Q(sms_rect_yn=selected_sms_rect_yn), Q.AND)

        if selected_join_source is not None and selected_join_source != 'all':
            is_selected = True
            if selected_join_source == 'no-data':
                condition.add(Q(memberaddition2member__member_join_source=None), Q.AND)
            else:
                condition.add(Q(memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if isinstance(set_up_join_date, str) and set_up_join_date != "":
            is_selected = True
            if start_join_date == end_join_date:
                condition.add(Q(join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(join_date__range=[start_join_date, end_join_date]), Q.AND)

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(email__icontains=searched_word) | Q(name__icontains=searched_word) | Q(
                memberaddition2member__memo__icontains=searched_word), Q.AND)

        user_qs = User.objects.filter(condition).order_by('-join_date').distinct()

        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(user_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['all_users'] = page_list
        context['user_count'] = user_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['selected_admyn'] = selected_admyn
        context['selected_sms_rect_yn'] = selected_sms_rect_yn
        context['selected_join_source'] = selected_join_source
        context['join_date'] = set_up_join_date
        context['page'] = page
        context['blank_count'] \
            = 15 - (user_qs.count() - 15 * (page - 1)) if user_qs.count() - 15 * (page - 1) < 15 else 0
        return context


class MemberModify(LoginRequiredMixin, TemplateView):
    template_name = 'member/member_modify.html'

    def get(self, request, *args, **kwargs):
        if not  self.request.user.is_admin:
            if str(self.request.user.id) != self.kwargs.get('id'):
                return redirect(reverse("common:check_auth_valid"))

        return super().get(self, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MemberModify, self).get_context_data(**kwargs)
        context['modf_user'] = User.objects.get(id=self.kwargs.get('id'))
        role_code = context['modf_user'].role_code
        if  role_code == 'MR01':
            context['dataset_ids'] = list(Annotator.objects.filter(member=self.kwargs.get('id'), valid_yn=UseType.Y).values_list('dataset_id', flat=True))
        elif role_code == 'MR04':
            context['dataset_ids'] = list(Provider.objects.filter(member=self.kwargs.get('id'), valid_yn=UseType.Y).values_list('dataset_id', flat=True))
        else:
            context['dataset_ids'] = list(Reviewer.objects.filter(member=self.kwargs.get('id'), valid_yn=UseType.Y).values_list('dataset_id', flat=True))
        return context


class GradeListView(LoginRequiredMixin, TemplateView):
    template_name = 'member/member_grade_list.html'

    def get(self, request, *args, **kwargs):
        if not self.request.user.is_admin:
            return redirect(reverse("common:check_auth_valid"))
        return super().get(self, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GradeListView, self).get_context_data(**kwargs)

        condition = Q()
        condition.add(Q(member__secession_yn=UseType.N), Q.AND)
        condition.add(Q(valid_yn=UseType.Y), Q.AND)

        selected_grade = self.request.GET.get('grade', None)
        selected_join_source = self.request.GET.get('join_source', None)
        searched_word = self.request.GET.get('word')

        is_selected, is_searched = False, False

        if selected_grade != "all" and selected_grade is not None:
            is_selected = True
            condition.add(Q(grade_code=selected_grade), Q.AND)

        if selected_join_source is not None and selected_join_source != 'all':
            is_selected = True
            condition.add(Q(member__memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if searched_word is not None:
            is_searched = True
            condition.add(Q(member__email__icontains=searched_word) | Q(member__name__icontains=searched_word), Q.AND)

        grade_qs = MemberGrade.objects.select_related('member').filter(condition).order_by('member__reg_date')

        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(grade_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['all_grades'] = page_list
        context['user_count'] = grade_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['selected_grade'] = selected_grade
        context['selected_join_source'] = selected_join_source
        context['member_role'] = MemberRole.choices
        context['member_grade'] = MemberGrade_Choice.choices
        context['page'] = page
        context['blank_count'] \
            = 15 - (grade_qs.count() - 15 * (page - 1)) if grade_qs.count() - 15 * (page - 1) < 15 else 0
        return context


def join_member(request):
    if request.is_ajax():
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        cpassword = request.POST.get('cpassword')

        result = True
        error = None

        if password != cpassword:
            result = False
            error = '비밀번호 불일치'
        elif User.objects.filter(email=email).count() > 0:
            result = False
            error = '이미 가입된 아이디입니다.'
        else:
            with transaction.atomic():
                user = User.objects.create(email=email, name=name)
                user.set_password(password)
                user.save()

                MemberAddition.objects.create(member=user, adm_yn=UseType.Y)
                MemberGrade.objects.create(member=user, valid_yn=UseType.Y)

                return JsonResponse({'result': result, 'id': user.id})

        return JsonResponse({'result': result, 'error': error})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def member_register(request):
    if request.is_ajax():

        # 저장할 form 데이터

        # - 회원 기본정보
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        name = request.POST.get('name')
        tel_no1 = request.POST.get('tel_no1')
        tel_no2 = request.POST.get('tel_no2')
        tel_no3 = request.POST.get('tel_no3')
        zipcode = request.POST.get('zipcode')
        addr = request.POST.get('addr')
        addr_detail = request.POST.get('addr_detail')
        sms_rect_yn = request.POST.get('sms_rect_yn')
        role_code = request.POST.get('role_code')
        is_active = True

        # 데이터세트
        dataset_list = request.POST.getlist('dataset_ids')

        # - 회원 부가정보
        rrn1 = request.POST.get('resident-registration-number1')
        rrn2 = request.POST.get('resident-registration-number2')
        bank_code = request.POST.get('bank_code')
        bank_no = request.POST.get('bank_no')
        job_join_type = request.POST.get('job_join_type')
        work_time_type = ','.join(request.POST.getlist('work_time_type'))
        member_job_type = request.POST.get('member_job_type')
        member_join_source = request.POST.get('member_join_source')
        disabled_person_yn = request.POST.get('disabled_person_yn')
        contract_file = request.FILES.get('file1')
        bankbook_file = request.FILES.get('file2')
        identification_file = request.FILES.get('file3')
        disabled_person_file = request.FILES.get('file4')
        resume_file = request.FILES.get('file5')
        agree_file = request.FILES.get('file6')
        file_type_list = request.POST.getlist('file_type')

        memo = request.POST.get('memo')

        if role_code == MemberRole.Provider:
            member_grade=MemberGrade_Choice.Provider
        else:
            member_grade=MemberGrade_Choice.Beginner

        # 입력을 넣지 않은 필드 처리 '' -> None
        tel_no1 = None if tel_no1 == '' else tel_no1
        tel_no2 = None if tel_no2 == '' else tel_no2
        tel_no3 = None if tel_no3 == '' else tel_no3
        zipcode = None if zipcode == '' else zipcode
        addr = None if addr == '' else addr
        addr_detail = None if addr_detail == '' else addr_detail
        rrn1 = None if rrn1 == '' else rrn1
        rrn2 = None if rrn2 == '' else rrn2
        bank_no = None if bank_no == '' else bank_no

        rrn, tel_no, gender_code, age_code = None, None, None, None
        result = True

        try:
            # 예외 처리
            if password1 != password2:
                result = False
                error = '비밀번호 불일치'
            elif User.objects.filter(email=email).count() > 0:
                result = False
                error = '이미 가입된 아이디입니다.'
            else:
                # 예외 통과하면 회원 등록
                with transaction.atomic():

                    # START : 넘어온 데이터 처리
                    # - checkbox : sms 수신 여부, 장애 여부, 관리자 승인 여부
                    if sms_rect_yn:
                        sms_rect_yn = UseType.Y
                    else:
                        sms_rect_yn = UseType.N
                    if disabled_person_yn:
                        disabled_person_yn = UseType.Y
                    else:
                        disabled_person_yn = UseType.N

                    # 관리자 승인
                    adm_yn = UseType.Y

                    # is_admin = 1

                    # - 주민등록번호 & 성별 & 나이
                    if rrn1 and rrn2:
                        rrn = AESCipher().encrypt_str(rrn1 + rrn2)
                        age = 0
                        if rrn2[0] == '1' or rrn2[0] == '3':
                            gender_code = GenderType.Man
                        elif rrn2[0] == '2' or rrn2[0] == '4':
                            gender_code = GenderType.Woman

                        if rrn2[0] == '1' or rrn2[0] == '2':
                            age = datetime.today().year - int('19' + rrn1[0:2]) + 1
                        elif rrn2[0] == '3' or rrn2[0] == '4':
                            age = datetime.today().year - int('20' + rrn1[0:2]) + 1

                        if 10 <= age < 20:
                            age_code = AgeType.Teenager
                        elif 20 <= age < 30:
                            age_code = AgeType.Twenty
                        elif 30 <= age < 40:
                            age_code = AgeType.Thirty
                        elif 40 <= age < 50:
                            age_code = AgeType.Forty
                        elif 50 <= age < 60:
                            age_code = AgeType.FifTy
                        elif 60 <= age < 70:
                            age_code = AgeType.Sixty

                    if tel_no1 and tel_no2 and tel_no3:
                        tel_no = tel_no1 + '-' + tel_no2 + '-' + tel_no3
                    # END   : 넘어온 데이터 처리

                    # START : 사용자 기본 정보 저장
                    user = User.objects.create(email=email, name=name, tel_no=tel_no, zipcode=zipcode, is_active = is_active,
                                               addr=addr, addr_detail=addr_detail, sms_rect_yn=sms_rect_yn, role_code=role_code)
                    user.set_password(password1)
                    user.save()
                    # END   : 사용자 기본 정보 저장

                    # START : 첨부 파일 리스트 처리
                    file_list = [contract_file, bankbook_file, identification_file, disabled_person_file, resume_file,
                                 agree_file]
                    for idx, file in enumerate(file_list):
                        if file:
                            write_path, file_name, org_file_name, file_size = handler_file_write(file)

                            # 첨부 파일 객체 생성
                            file_object = File.objects.create(file_path=write_path,
                                                              file_name=file_name,
                                                              org_file_name=org_file_name,
                                                              file_size=file_size,
                                                              file_type=file_type_list[idx])

                            if idx == 0:
                                contract_file = file_object
                            elif idx == 1:
                                bankbook_file = file_object
                            elif idx == 2:
                                identification_file = file_object
                            elif idx == 3:
                                disabled_person_file = file_object
                            elif idx == 4:
                                resume_file = file_object
                            elif idx == 5:
                                agree_file = file_object

                    # END   : 첨부 파일 리스트 처리

                    # START : 사용자 부가 정보 저장
                    MemberAddition.objects.create(member=user, rrn=rrn, gender_code=gender_code, age_code=age_code,
                                                  bank_code=bank_code, bank_no=bank_no,
                                                  job_join_type=job_join_type,
                                                  work_time_type=work_time_type,
                                                  member_job_type=member_job_type,
                                                  member_join_source=member_join_source,
                                                  disabled_person_yn=disabled_person_yn, adm_yn=adm_yn,
                                                  bankbook_file=bankbook_file,
                                                  contract_file=contract_file,
                                                  identification_file=identification_file,
                                                  disabled_person_file=disabled_person_file,
                                                  resume_file=resume_file,
                                                  agree_file=agree_file,
                                                  memo=memo
                                                  )

                    MemberGrade.objects.create(member=user, valid_yn=UseType.Y, grade_code=member_grade)
                    # END   : 사용자 부가 정보 저장

                    # START 역할 별 인서트
                    if role_code == 'MR01':
                        role = Annotator
                    elif role_code == 'MR02' or role_code == 'MR03':
                        role = Reviewer
                    else:
                        role = Provider
                    for datasetid in dataset_list:
                        updated, created = role.objects.update_or_create(member=user, dataset_id=datasetid,
                                                                         defaults={'valid_yn':UseType.Y, 'limit_count':0})
                        if not updated and not created :
                            raise
                    # END
                    return JsonResponse({'result': result, 'id': user.id})
            return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def member_modify(request):
    if request.is_ajax():

        # 수정할 form 데이터

        # - 회원 기본정보
        id = request.POST.get('id')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        name = request.POST.get('name')
        tel_no1 = request.POST.get('tel_no1')
        tel_no2 = request.POST.get('tel_no2')
        tel_no3 = request.POST.get('tel_no3')
        zipcode = request.POST.get('zipcode')
        addr = request.POST.get('addr')
        addr_detail = request.POST.get('addr_detail')
        sms_rect_yn = request.POST.get('sms_rect_yn')
        role_code = request.POST.get('role_code')

        # - 회원 부가정보
        rrn1 = request.POST.get('resident-registration-number1')
        rrn2 = request.POST.get('resident-registration-number2')
        bank_code = request.POST.get('bank_code')
        bank_no = request.POST.get('bank_no')
        job_join_type = request.POST.get('job_join_type')
        work_time_type = ','.join(request.POST.getlist('work_time_type'))
        member_job_type = request.POST.get('member_job_type')
        member_join_source = request.POST.get('member_join_source')
        disabled_person_yn = request.POST.get('disabled_person_yn')
        contract_file = request.FILES.get('file1')
        bankbook_file = request.FILES.get('file2')
        identification_file = request.FILES.get('file3')
        disabled_person_file = request.FILES.get('file4')
        resume_file = request.FILES.get('file5')
        agree_file = request.FILES.get('file6')
        prev_contract_file_id = request.POST.get('already_saved_contract_file_id')
        prev_bankbook_file_id = request.POST.get('already_saved_bankbook_file_id')
        prev_identification_file_id = request.POST.get('already_saved_identification_file_id')
        prev_disabled_person_file_id = request.POST.get('already_saved_disabled_person_file_id')
        prev_resume_file_id = request.POST.get('already_saved_resume_file_id')
        prev_agree_file_id = request.POST.get('already_saved_agree_file_id')
        file_type_list = request.POST.getlist('file_type')
        gender_code = request.POST.get('gender_code')
        age_code = request.POST.get('age_code')

        memo = request.POST.get('memo')

        role_check = User.objects.get(id=id)
        if role_check.role_code != 'MR04' and role_code == 'MR04':
            return JsonResponse({'result': False, 'error': '작업자는 대화제공자로 변경할 수 없습니다.'})

        # 데이터세트
        dataset_list = request.POST.getlist('dataset_ids')

        # 입력을 넣지 않은 필드 처리 '' -> None
        password1 = None if password1 == '' else password1
        password2 = None if password2 == '' else password2
        tel_no1 = None if tel_no1 == '' else tel_no1
        tel_no2 = None if tel_no2 == '' else tel_no2
        tel_no3 = None if tel_no3 == '' else tel_no3
        zipcode = None if zipcode == '' else zipcode
        addr = None if addr == '' else addr
        addr_detail = None if addr_detail == '' else addr_detail
        rrn1 = None if rrn1 == '' else rrn1
        rrn2 = None if rrn2 == '' else rrn2
        bank_no = None if bank_no == '' else bank_no
        prev_contract_file_id = None if prev_contract_file_id == '' else prev_contract_file_id
        prev_bankbook_file_id = None if prev_bankbook_file_id == '' else prev_bankbook_file_id
        prev_identification_file_id = None if prev_identification_file_id == '' else prev_identification_file_id
        prev_disabled_person_file_id = None if prev_disabled_person_file_id == '' else prev_disabled_person_file_id
        prev_resume_file_id = None if prev_resume_file_id == '' else prev_resume_file_id
        prev_agree_file_id = None if prev_agree_file_id == '' else prev_agree_file_id

        tel_no, rrn = None, None
        result = True

        try:
            # 예외 처리
            if not (password1 is None and password2 is None):
                if password1 != password2:
                    result = False
                    error = '비밀번호 불일치'
                    return JsonResponse({'result': result, 'error': error})

            # 예외 통과하면 회원 정보 수정
            with transaction.atomic():
                # START : 넘어온 데이터 처리
                # - checkbox : sms 수신 여부, 장애 여부, 관리자 승인 여부
                if sms_rect_yn:
                    sms_rect_yn = UseType.Y
                else:
                    sms_rect_yn = UseType.N
                if disabled_person_yn:
                    disabled_person_yn = UseType.Y
                else:
                    disabled_person_yn = UseType.N

                # - 주민등록번호 & 성별 & 나이
                if rrn1 and rrn2:
                    rrn = AESCipher().encrypt_str(rrn1 + rrn2)
                    age = 0
                    if rrn2[0] == '1' or rrn2[0] == '3':
                        gender_code = GenderType.Man
                    elif rrn2[0] == '2' or rrn2[0] == '4':
                        gender_code = GenderType.Woman

                    if rrn2[0] == '1' or rrn2[0] == '2':
                        age = datetime.today().year - int('19' + rrn1[0:2]) + 1
                    elif rrn2[0] == '3' or rrn2[0] == '4':
                        age = datetime.today().year - int('20' + rrn1[0:2]) + 1

                    if 10 <= age < 20:
                        age_code = AgeType.Teenager
                    elif 20 <= age < 30:
                        age_code = AgeType.Twenty
                    elif 30 <= age < 40:
                        age_code = AgeType.Thirty
                    elif 40 <= age < 50:
                        age_code = AgeType.Forty
                    elif 50 <= age < 60:
                        age_code = AgeType.FifTy
                    elif 60 <= age < 70:
                        age_code = AgeType.Sixty

                if tel_no1 and tel_no2 and tel_no3:
                    tel_no = tel_no1 + '-' + tel_no2 + '-' + tel_no3
                # END   : 넘어온 데이터 처리

                # START : 사용자 기본 정보 수정
                user = User.objects.get(id=id)
                user.name = name
                if password1:
                    user.set_password(password1)
                user.tel_no = tel_no
                user.zipcode = zipcode
                user.addr = addr
                user.addr_detail = addr_detail
                user.sms_rect_yn = sms_rect_yn
                user.modf_date = datetime.now()
                user.role_code = role_code

                user.save()
                # END   : 사용자 기본 정보 수정

                # START : 첨부 파일 리스트 처리
                file_list = [contract_file, bankbook_file, identification_file, disabled_person_file, resume_file,
                             agree_file]
                for idx, file in enumerate(file_list):
                    if file:
                        write_path, file_name, org_file_name, file_size = handler_file_write(file)

                        # 첨부 파일 객체 생성

                        file_object = File.objects.create(file_path=write_path,
                                                          file_name=file_name,
                                                          org_file_name=org_file_name,
                                                          file_size=file_size,
                                                          file_type=file_type_list[idx])

                        if idx == 0:
                            contract_file = file_object
                        elif idx == 1:
                            bankbook_file = file_object
                        elif idx == 2:
                            identification_file = file_object
                        elif idx == 3:
                            disabled_person_file = file_object
                        elif idx == 4:
                            resume_file = file_object
                        elif idx == 5:
                            agree_file = file_object

                # raise Exception
                # END   : 첨부 파일 리스트 처리

                # START : 사용자 부가 정보 저장
                additional_info = MemberAddition.objects.get(member_id=id)
                additional_info.rrn = rrn
                additional_info.bank_code = bank_code
                additional_info.bank_no = bank_no
                additional_info.gender_code = gender_code
                additional_info.age_code = age_code
                additional_info.job_join_type = job_join_type
                additional_info.work_time_type = work_time_type
                additional_info.member_job_type = member_job_type
                additional_info.member_join_source = member_join_source
                additional_info.disabled_person_yn = disabled_person_yn

                if contract_file:
                    additional_info.contract_file = contract_file
                else:
                    if prev_contract_file_id and File.objects.get(id=prev_contract_file_id) == '':
                        additional_info.contract_file = None

                if bankbook_file:
                    additional_info.bankbook_file = bankbook_file
                else:
                    if prev_bankbook_file_id and File.objects.get(id=prev_bankbook_file_id) == '':
                        additional_info.bankbook_file = None

                if identification_file:
                    additional_info.identification_file = identification_file
                else:
                    if prev_identification_file_id and File.objects.get(id=prev_identification_file_id) == '':
                        additional_info.identification_file = None

                if disabled_person_file:
                    additional_info.disabled_person_file = disabled_person_file
                else:
                    if prev_disabled_person_file_id and File.objects.get(id=prev_disabled_person_file_id) == '':
                        additional_info.disabled_person_file = None

                if resume_file:
                    additional_info.resume_file = resume_file
                else:
                    if prev_resume_file_id and File.objects.get(id=prev_resume_file_id) == '':
                        additional_info.resume_file = None

                if agree_file:
                    additional_info.agree_file = agree_file
                else:
                    if prev_agree_file_id and File.objects.get(id=prev_agree_file_id) == '':
                        additional_info.agree_file = None

                # 마이너스 버튼을 눌렀다면 DB에 파일정보를 None으로 변경
                if prev_contract_file_id is None and contract_file is None:
                    additional_info.contract_file = None

                if prev_bankbook_file_id is None and bankbook_file is None:
                    additional_info.bankbook_file = None

                if prev_identification_file_id is None and identification_file is None:
                    additional_info.identification_file = None

                if prev_disabled_person_file_id is None and disabled_person_file is None:
                    additional_info.disabled_person_file = None

                if prev_resume_file_id is None and resume_file is None:
                    additional_info.resume_file = None

                if prev_agree_file_id is None and agree_file is None:
                    additional_info.agree_file = None

                # raise Exception
                additional_info.memo = memo
                additional_info.save()

                # END   : 사용자 부가 정보 저장

                # 사용자 역할 별 데이터처리
                if role_code == 'MR01':
                    role = Annotator
                elif role_code == 'MR02' or role_code == 'MR03':
                    role = Reviewer
                else:
                    role = Provider

                role_qs = role.objects.filter(member=user)
                role_qs.update(valid_yn=UseType.N)

                for datasetid in dataset_list:
                    try:
                        limit_count=role.objects.get(member=user, dataset=datasetid).limit_count
                    except Exception as e:
                        if str(e) == 'Reviewer matching query does not exist.':
                            limit_count=0

                    updated, created = role.objects.update_or_create(member=user, dataset=Dataset.objects.get(id=datasetid),
                                                                     defaults={'valid_yn': UseType.Y, 'limit_count':limit_count})
                    if not updated and not created:
                        raise
                # END

                return JsonResponse({'result': result, 'id': user.id})

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def member_delete(request):
    if request.is_ajax():
        id = request.GET.get("id")
        result = False
        error = ""
        try:
            with transaction.atomic():

                annotator_qs = Annotator.objects.filter(member_id=id,
                                                        member__point2user__point_status=PointStatus.Complete)
                bbox_reviewr_qs = Reviewer.objects.filter(member_id=id,
                                                          jobbox2reviewer__inspection_status=InspectionStatus.Complete)
                seg_reviewr_qs = Reviewer.objects.filter(member_id=id,
                                                         jobsegmentation2reviewer__inspection_status=InspectionStatus.Complete)
                tqa_reviewr_qs = Reviewer.objects.filter(member_id=id,
                                                         jobtextqa2reviewer__inspection_status=InspectionStatus.Complete)
                vqa_reviewr_qs = Reviewer.objects.filter(member_id=id,
                                                         jobvisualqa2reviewer__inspection_status=InspectionStatus.Complete)
                img_reviewr_qs = Reviewer.objects.filter(member_id=id,
                                                         jobimage2reviewer__inspection_status=InspectionStatus.Complete)
                if annotator_qs.count() > 0:
                    error = "해당 계정은 어노테이터이며 포인트가 존재하기 때문에 제거가 불가능합니다."
                elif bbox_reviewr_qs.count() > 0:
                    error = "해당 계정은 bbox 리뷰어이며 검수를 완료한 작업이 존재하기 때문에 제거가 불가능합니다."
                elif seg_reviewr_qs.count() > 0:
                    error = "해당 계정은 segmentation 리뷰어이며 검수를 완료한 작업이 존재하기 때문에 제거가 불가능합니다."
                elif tqa_reviewr_qs.count() > 0:
                    error = "해당 계정은 textQA 리뷰어이며 검수를 완료한 작업이 존재하기 때문에 제거가 불가능합니다."
                elif vqa_reviewr_qs.count() > 0:
                    error = "해당 계정은 visualQA 리뷰어이며 검수를 완료한 작업이 존재하기 때문에 제거가 불가능합니다."
                elif img_reviewr_qs.count() > 0:
                    error = "해당 계정은 image 리뷰어이며 검수를 완료한 작업이 존재하기 때문에 제거가 불가능합니다."
                else:
                    result = True
                    user = User.objects.get(id=id)
                    user.secession_yn = UseType.Y
                    user.email = uuid.uuid1()
                    user.tel_no = None
                    user.is_active = False
                    user.save()
                return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})

    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def member_approve(request):
    if request.is_ajax():
        id = request.GET.get("id")
        result = True
        error = ""
        try:
            with transaction.atomic():
                additional_info = MemberAddition.objects.get(member_id=id)
                additional_info.adm_yn = UseType.Y
                additional_info.save()
                return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})

    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


@csrf_exempt
def member_grade_update(request):
    if request.is_ajax():
        id, selectedGrade, selectedRole, new_data, to_be_changed_items = None, None, None, None, None
        project_grade = []
        project_grade_value = []

        if request.method == "GET":
            id = request.GET.get("id")
            selectedGrade = request.GET.get("grade")
            selectedRole = request.GET.get('role')
            new_data = [selectedGrade]

            new_data.append(selectedRole)
        else:
            to_be_changed_items = json.loads(request.POST['to_be_changed_items'])

        result = True
        error = ""

        try:
            with transaction.atomic():
                origin_role = User.objects.get(id=id).role_code
                if not to_be_changed_items:
                    #역할이 변경되는 경우 데이터셋과 limitcount 보전
                    dataset_list = list(Reviewer.objects.filter(member=id, valid_yn=UseType.Y)\
                                    .union(
                                        Annotator.objects.filter(member=id, valid_yn=UseType.Y)).values_list('dataset_id', flat=True))
                    role = Reviewer
                    if origin_role != selectedRole:
                        if origin_role == 'MR01':
                            role = Reviewer
                            Annotator.objects.filter(member=id).update(valid_yn=UseType.N)
                        else:
                            if(selectedRole == 'MR01'):
                                role = Annotator
                                Reviewer.objects.filter(member=id).update(valid_yn=UseType.N)

                        for dataset_id in dataset_list:
                            updated, created = role.objects.update_or_create(member_id=id, dataset_id=dataset_id,
                                                                             defaults={'limit_count':0, 'valid_yn':UseType.Y})

                            if not updated and not created:
                                raise

                    # 원래 레코드는 유효 여부 N으로 바꿈
                    grade_info = MemberGrade.objects.filter(valid_yn=UseType.Y).get(member_id=id)
                    grade_info.valid_yn = UseType.N
                    grade_info.save()

                    # 등급을 바꾼 사용자에 대한 등급 레코드를 새롭게 생성하여 추가.
                    MemberGrade.objects.create(member_id=id, valid_yn=UseType.Y, grade_code=selectedGrade)

                    user = User.objects.get(id=id)
                    user.role_code = selectedRole
                    user.save()
                else:
                    for item in to_be_changed_items:
                        grade_info = MemberGrade.objects.filter(valid_yn=UseType.Y).get(member_id=item['member_id'])
                        grade_info.valid_yn = UseType.N
                        grade_info.save()

                        MemberGrade.objects.create(member_id=item['member_id'], valid_yn=UseType.Y,
                                                   grade_code=item['grade_code'])

                        user = User.objects.get(id=item['member_id'])
                        user.role_code = item['role_code']
                        user.save()

                return JsonResponse({'result': result, 'error': error, 'new_data': new_data})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})

    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def member_list_excel(request):
    response = HttpResponse(content_type='application/ms-excel')
    try:
        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('회원목록')

        ws.col(0).width = 30 * 255  # 이메일
        ws.col(1).width = 15 * 255  # 이름
        ws.col(2).width = 15 * 255  # 연락처
        ws.col(3).width = 45 * 255  # 주소
        ws.col(4).width = 25 * 255  # 상세주소
        ws.col(5).width = 15 * 255  # 주민등록번호
        ws.col(9).width = 20 * 255  # 가입경로
        ws.col(10).width = 20 * 255  # 가입일자
        ws.col(11).width = 20 * 255  # 변경일자

        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['이메일', '이름', '연락처', '주소', '상세주소', '주민등록번호', '부가정보입력', '은행정보입력', '이력서등록', '가입경로', '가입일자', '변경일자',
                   '추가정보승인', '회원메모']

        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        font_style = xlwt.XFStyle()

        condition = Q()
        condition.add(Q(secession_yn=UseType.N), Q.AND)

        selected_admyn = request.GET.get('admyn', None)
        selected_join_source = request.GET.get('join_source', None)
        set_up_join_date = request.GET.get('join_date', None)
        searched_word = request.GET.get('searched_word', None)
        title = ""

        title += '회원목록.xls'
        response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % urllib.quote(title.encode('utf-8'))

        start_join_date, end_join_date = None, None

        if isinstance(set_up_join_date, str) and set_up_join_date != "":
            temp = set_up_join_date.split(" ")
            start_join_date = temp[0].split("-")
            end_join_date = temp[2].split("-")

            start_join_date = date(int(start_join_date[0]), int(start_join_date[1]), int(start_join_date[2]))
            end_join_date = date(int(end_join_date[0]), int(end_join_date[1]), int(end_join_date[2])) + timedelta(days=1)

        if selected_join_source is not None and selected_join_source != 'all':
            if selected_join_source == 'no-data':
                condition.add(Q(memberaddition2member__member_join_source=None), Q.AND)
            else:
                condition.add(Q(memberaddition2member__member_join_source=selected_join_source), Q.AND)

        if isinstance(set_up_join_date, str) and set_up_join_date != "":
            if start_join_date == end_join_date:
                condition.add(Q(join_date__icontains=start_join_date), Q.AND)
            else:
                condition.add(Q(join_date__range=[start_join_date, end_join_date]), Q.AND)

        if searched_word is not None and searched_word != '':
            condition.add(Q(name__icontains=searched_word) | Q(email__icontains=searched_word), Q.AND)

        user_rows = User.objects.filter(condition).annotate(
            addition_info=Case(
                When(
                    memberaddition2member__age_code__isnull=False,
                    then=1
                ), default=0, output_field=IntegerField()
            ),
            bank_info=Case(
                When(
                    memberaddition2member__bank_no__isnull=False,
                    then=1
                ), default=0, output_field=IntegerField()
            ),
            resume_info=Case(
                When(
                    memberaddition2member__resume_file__isnull=False,
                    then=1
                ), default=0, output_field=IntegerField()
            ), format_join_date=Cast(
                TruncSecond('join_date', DateTimeField()), CharField()
            ), format_modf_date=Cast(
                TruncSecond('modf_date', DateTimeField()), CharField()
            )
        ).values_list('email', 'name', 'tel_no', 'addr', 'addr_detail', 'memberaddition2member__rrn', 'addition_info',
                      'bank_info', 'resume_info',
                      'memberaddition2member__member_join_source', 'format_join_date',
                      'format_modf_date', 'memberaddition2member__adm_yn',
                      'memberaddition2member__memo').distinct()
        data_count = user_rows.count()
        for row in user_rows:
            row_num += 1
            for col_num in range(len(row)):
                output_data = row[col_num]
                if col_num == 5:
                    if output_data is not None:
                        rear = parse_rrn(output_data, 'rear')
                        rrn = parse_rrn(output_data, 'head') + '-' + rear[:1] + '******'
                    else:
                        rrn = ''
                    ws.write(row_num, col_num, rrn, font_style)
                    continue
                if col_num == 6 or col_num == 7:
                    output_data = '미입력' if output_data == 0 else '입력완료'
                if col_num == 8:
                    output_data = '미첨부' if output_data == 0 else '첨부완료'
                if col_num == 9:
                    output_data = MemberJoinSource.get_value(output_data)

                ws.write(row_num, col_num, output_data, font_style)

        wb.save(response)
    except Exception as e:
        traceback.print_exc()
        return response

    return response


def jsonBody(title, msg, numbers):
    number = []
    for num in numbers:
        number.append({
            "recipientNo": num,  # 필수
            # "countryCode":"82",
            # "internationalRecipientNo":"821000000000",
            "templateParameter": {
            }
            #  "recipientGroupingKey":"recipientGroupingKey"
        })

    jsonBody = {
        # "templateId":"TemplateId",
        "title": title,  # 필수
        "body": msg,  # 필수
        "sendNo": "0423656589",  # 필수
        # "senderGroupingKey":"SenderGroupingKey",
        "recipientList": number,
        "userId": ""
        #  "statsId":"statsId"
    }
    return json.dumps(jsonBody)

def get_member_qs(role=None):
    # 역할 미입력: 전체 사용자 쿼리셋 return
    if role is None:
        all_member_qs = User.objects.filter(secession_yn=UseType.N)
        return all_member_qs

    # 역할 입력: 해당 역할에 속한 사용자 쿼리셋 return
    else:
        if role == 'MR01':
            annotator_members_qs = Annotator.objects.filter(member__secession_yn=UseType.N)
            return annotator_members_qs
        elif role == 'MR02':
            reviewer_members_qs = Reviewer.objects.filter(member__secession_yn=UseType.N)
            return reviewer_members_qs
