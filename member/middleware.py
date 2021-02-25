from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from common.choices import MemberRole

from django.urls import reverse, resolve


class AllowSuperUserOnly(MiddlewareMixin):

  def process_request(self, request):
    # 회원 공통 사용 url prefix
    common_path = (
      '/logout/',
      '/media/',
      '/static/',
      '/common/',
    )

    # 관리자 페이지 접근 제한 특정 권한
    exclude_role = [
    ]

    # 특정권한 접근 가능 url prefix
    exclude_path = (
      '/textsummary/'
    )

    # url path가 매핑되어있는 app 정보, name space를 get
    url_resolve = resolve(request.path)

    # 회원이 로그인 되어있고 url이 app에 지정되어있고 공통사용 url이 아닐때
    if request.user.is_authenticated and url_resolve.app_name and not request.path.lower().startswith(common_path):
      if request.user.role_code in exclude_role:
        if not request.path.startswith(exclude_path):
          return redirect("/")
      else:
        if request.path.startswith(exclude_path):
          return redirect("/")

    return None
