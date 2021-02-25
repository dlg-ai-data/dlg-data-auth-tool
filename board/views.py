import traceback

from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView

from common.utils import get_page_range
from vaiv.view import LoginRequiredMixin
from member.models import User
from common.choices import FileType, UseType, BBSType, BBSStatusType
from common.models import BBS
from common.models import File
from common.utils import handler_file_write

class NoticeView(LoginRequiredMixin, TemplateView):
    template_name = 'board/notice_board.html'

    def get_context_data(self, **kwargs):
        context = super(NoticeView, self).get_context_data(**kwargs)

        condition = Q(bbs_type=BBSType.Notice)

        selected_status = self.request.GET.get('status', None)
        selected_notice_yn = self.request.GET.get('notice_yn', None)
        searched_word = self.request.GET.get('word')

        is_selected, is_searched = False, False

        if selected_status != "all" and selected_status is not None:
            is_selected = True
            condition.add(Q(bbs_status=selected_status), Q.AND)

        if selected_notice_yn != "all" and selected_notice_yn is not None:
            is_selected = True
            condition.add(Q(notice_yn=selected_notice_yn), Q.AND)

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(title__icontains=searched_word) | Q(member__name__icontains=searched_word), Q.AND)

        bbs_qs = BBS.objects.select_related('member').filter(condition).order_by('-reg_date')
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(bbs_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['all_notices'] = page_list
        context['notice_count'] = bbs_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['selected_status'] = selected_status
        context['selected_notice_yn'] = selected_notice_yn
        context['page'] = page
        context['blank_count'] \
            = 15 - (bbs_qs.count() - 15 * (page - 1)) if bbs_qs.count() - 15 * (page - 1) < 15 else 0
        return context

@csrf_exempt
def notice_register(request):
    if request.is_ajax():

        member_id = request.user.id
        title = request.POST.get('title')
        attachment = request.FILES.get('attachment')
        contents = request.POST.get('contents')
        bbs_status = request.POST.get('bbs_status')
        result = True

        try:
            with transaction.atomic():

                bbs_type = BBSType.Notice
                content_type, upper_id, file_id = None, None, None
                notice_yn = UseType.N

                # 첨부 파일 객체 생성
                if attachment:
                    write_path, file_name, org_file_name, file_size = handler_file_write(attachment)
                    file_id = File.objects.create(file_path=write_path,
                                                  file_name=file_name,
                                                  org_file_name=org_file_name,
                                                  file_size=file_size,
                                                  file_type=FileType.BBSFile).id

                BBS.objects.create(bbs_type=bbs_type, content_type=content_type, bbs_status=bbs_status, title=title,
                                   contents=contents, notice_yn=notice_yn, file_id=file_id, upper_id=upper_id,
                                   member_id=member_id)

                return JsonResponse({'result': result, 'id': member_id})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

@csrf_exempt
def notice_modify(request):
    if request.is_ajax():

        notice_id = request.POST.get('notice_id')
        title = request.POST.get('title')
        attachment = request.FILES.get('attachment')
        contents = request.POST.get('contents')
        bbs_status = request.POST.get('bbs_status')
        already_saved_file_id = request.POST.get('already_saved_file_id')
        result = True

        if already_saved_file_id == 'None' or already_saved_file_id == "":
            already_saved_file_id = None

        try:
            with transaction.atomic():

                file_id = None;
                # 첨부 파일 객체 생성
                if attachment:
                    write_path, file_name, org_file_name, file_size = handler_file_write(attachment)
                    file_id = File.objects.create(file_path=write_path,
                                                  file_name=file_name,
                                                  org_file_name=org_file_name,
                                                  file_size=file_size,
                                                  file_type=FileType.BBSFile).id

                notice = BBS.objects.get(id=notice_id)
                notice.title = title
                notice.contents = contents
                if attachment:
                    notice.file_id = file_id
                else:
                    if already_saved_file_id:
                        if File.objects.get(id=already_saved_file_id) == '':
                            notice.file_id = None

                notice.bbs_status = bbs_status

                if bbs_status == 'AE01':
                    notice.notice_yn = UseType.N;

                # 마이너스 버튼을 눌렀다면 DB에 파일정보를 None으로 변경
                if already_saved_file_id is None and attachment is None:
                    notice.file_id = None

                notice.save()

                return JsonResponse({'result': result, 'id': notice_id})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

@csrf_exempt
def notice_delete(request):
    if request.is_ajax():

        id = request.GET.get("id")
        result = True
        error = ""
        try:
            with transaction.atomic():
                notice = BBS.objects.get(id=id)
                notice.delete()

                return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

@csrf_exempt
def reference_delete(request):
    if request.is_ajax():

        id = request.GET.get("id")
        result = True
        error = ""
        try:
            with transaction.atomic():
                reference = BBS.objects.get(id=id)
                reference.delete()

                return JsonResponse({'result': result, 'error': error})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

def notice_change_status(request):
    if request.is_ajax():

        id = request.GET.get("id")
        selectedStatus = request.GET.get("noticeyn")
        result = True
        error = ""
        try:
            with transaction.atomic():
                notice = BBS.objects.get(id=id)
                notice.notice_yn = selectedStatus
                notice.save()

                return JsonResponse({'result': result, 'error': error, 'new_status': selectedStatus})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

class ReferenceView(LoginRequiredMixin, TemplateView):
    template_name = 'board/reference_board.html'

    def get_context_data(self, **kwargs):
        context = super(ReferenceView, self).get_context_data(**kwargs)

        condition = Q(bbs_type=BBSType.Reference)

        if not self.request.user.is_admin:
            condition.add(Q(bbs_status=BBSStatusType.Complete), Q.AND)

        selected_status = self.request.GET.get('status', None)
        searched_word = self.request.GET.get('word')

        is_selected, is_searched = False, False

        if selected_status != "all" and selected_status is not None:
            is_selected = True
            condition.add(Q(bbs_status=selected_status), Q.AND)

        if searched_word is not None and searched_word != "":
            is_searched = True
            condition.add(Q(title__icontains=searched_word) | Q(member__name__icontains=searched_word), Q.AND)

        bbs_qs = BBS.objects.select_related('member').filter(condition).order_by('-reg_date')
        page = int(self.request.GET.get('page', 1))
        paginator = Paginator(bbs_qs, 15)
        page_list = paginator.get_page(page)
        paginator_range = get_page_range(paginator, page)

        context['all_references'] = page_list
        context['reference_count'] = bbs_qs.count()
        context['isSelected'] = is_selected
        context['isSearched'] = is_searched
        context['searched_word'] = searched_word
        context['paginator_range'] = paginator_range
        context['selected_status'] = selected_status
        context['page'] = page
        context['blank_count'] \
            = 15 - (bbs_qs.count() - 15 * (page - 1)) if bbs_qs.count() - 15 * (page - 1) < 15 else 0
        return context

@csrf_exempt
def reference_register(request):
    if request.is_ajax():

        member_id = request.user.id
        title = request.POST.get('title')
        attachment = request.FILES.get('attachment')
        contents = request.POST.get('contents')
        bbs_status = request.POST.get('bbs_status')
        result = True

        try:
            with transaction.atomic():

                bbs_type = BBSType.Reference
                content_type, upper_id, file_id = None, None, None

                # 첨부 파일 객체 생성
                if attachment:
                    write_path, file_name, org_file_name, file_size = handler_file_write(attachment)
                    file_id = File.objects.create(file_path=write_path,
                                                  file_name=file_name,
                                                  org_file_name=org_file_name,
                                                  file_size=file_size,
                                                  file_type=FileType.BBSFile).id

                BBS.objects.create(bbs_type=bbs_type, content_type=content_type, bbs_status=bbs_status, title=title,
                                   contents=contents, file_id=file_id, upper_id=upper_id,
                                   member_id=member_id)

                return JsonResponse({'result': result, 'id': member_id})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

@csrf_exempt
def reference_modify(request):
    if request.is_ajax():

        reference_id = request.POST.get('reference_id')
        title = request.POST.get('title')
        attachment = request.FILES.get('attachment')
        contents = request.POST.get('contents')
        bbs_status = request.POST.get('bbs_status')
        already_saved_file_id = request.POST.get('already_saved_file_id')
        result = True

        if already_saved_file_id == 'None' or already_saved_file_id == "":
            already_saved_file_id = None

        try:
            with transaction.atomic():

                file_id = None;
                # 첨부 파일 객체 생성
                if attachment:
                    write_path, file_name, org_file_name, file_size = handler_file_write(attachment)
                    file_id = File.objects.create(file_path=write_path,
                                                  file_name=file_name,
                                                  org_file_name=org_file_name,
                                                  file_size=file_size,
                                                  file_type=FileType.BBSFile).id

                reference = BBS.objects.get(id=reference_id)
                reference.title = title
                reference.contents = contents
                if attachment:
                    reference.file_id = file_id
                else:
                    if already_saved_file_id:
                        if File.objects.get(id=already_saved_file_id) == '':
                            reference.file_id = None

                reference.bbs_status = bbs_status

                # 마이너스 버튼을 눌렀다면 DB에 파일정보를 None으로 변경
                if already_saved_file_id is None and attachment is None:
                    reference.file_id = None

                reference.save()

                return JsonResponse({'result': result, 'id': reference_id})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})
