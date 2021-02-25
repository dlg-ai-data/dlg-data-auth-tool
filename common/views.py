import os
import traceback
import urllib.request as urllib
from pathlib import PurePosixPath

from django.db import transaction
from django.http import HttpResponse, Http404, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from common.models import File
from vaiv import settings
from vaiv.view import LoginRequiredMixin, TemplateView
from member.models import User

class check_auth_valid(LoginRequiredMixin, TemplateView):
    template_name='no_valid.html'

    def get_context_data(self, **kwargs):
        context = super(check_auth_valid, self).get_context_data(**kwargs)
        prev_page=self.request.META.get('HTTP_REFERER')

        context['prev_page'] = prev_page
        return context

def file_IsExist(request):
    if request.is_ajax():
        file_id = request.GET.get('file_id')
        try:
            file = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return JsonResponse({'result': False, 'error': '해당 파일이 DB에 존재하지 않습니다. File Id: ' + str(file_id)})

        full_file_path = PurePosixPath(settings.MEDIA_ROOT, file.file_path, file.file_name)
        if os.path.exists(full_file_path):
            return JsonResponse({'result': True})
        else:
            return JsonResponse({'result': False, 'error': '해당 파일 경로는 존재하지 않습니다. 경로: ' + str(full_file_path)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})


def filedownload(request):
    id = request.GET.get('id')
    file = File.objects.get(id=id)
    fullfilepath = PurePosixPath(settings.MEDIA_ROOT, file.file_path, file.file_name)
    with open(fullfilepath, 'rb') as fh:
        response = HttpResponse(fh.read(), content_type='application/force-download')
        response['Content-Disposition'] = 'attachment; filename*=UTF-8\'\'%s' % urllib.quote(
            file.org_file_name.encode('utf-8'))
        return response

@csrf_exempt
def email_is_exist(request):
    if request.is_ajax():
        user_email = request.POST.get('user_email')
        try:
            with transaction.atomic():
                user = User.objects.get(email=user_email)
                if user:
                    return JsonResponse({'result': True, 'id': user.id})
                return JsonResponse({'result': False})
        except Exception as e:
            traceback.print_exc()
            return JsonResponse({'result': False, 'error': str(e)})
    else:
        return JsonResponse({'result': False, 'error': 'is ajax only Method'})

def pdf_file_view(request,id):
    try:
        file = JobFile.objects.get(id=int(id))
    except File.DoesNotExist:
        raise Http404
    fullfilepath = PurePosixPath(settings.MEDIA_ROOT, file.file_path, file.file_name)
    if os.path.exists(fullfilepath):
        with open(fullfilepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename*=UTF-8\'\'%s' % urllib.quote(
                file.org_file_name.encode('utf-8'))
            return response
        fh.closed
    else:
        raise Http404