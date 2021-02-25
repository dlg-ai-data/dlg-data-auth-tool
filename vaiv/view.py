from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.views.generic import TemplateView

from common.choices import UseType, JobStatus, InspectionStatus, BBSType, MemberRole
from job.models import JobTalk, JobTalkSource
from member.models import User
from common.models import BBS
from django.db.models.functions import TruncDay
from django.db.models import Q
from datetime import timedelta, datetime, date


class LoginRequiredMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(LoginRequiredMixin, cls).as_view(**initkwargs)
        return login_required(view)


class MainView(LoginRequiredMixin, TemplateView):
    template_name = 'main.html'

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)

        bbs_qs = BBS.objects.filter(bbs_type=BBSType.Notice, notice_yn=UseType.Y).all().order_by('-reg_date')[:5]

        annotator = []
        annotator_reject = []
        source_reviewer=[]
        reviewer=[]
        provider=[]
        provider_reject=[]
        days = []

        member_id = self.request.user.id
        role_code = self.request.user.role_code
        is_admin = self.request.user.is_admin

        annotator_condition = Q()
        source_reviewer_condition = Q()
        reviewer_condition = Q()
        provider_condition = Q()

        if not is_admin:
            if role_code == MemberRole.Annotrator:
                annotator_condition.add(Q(annotator__member_id=member_id), Q.AND)
                reviewer_condition.add(Q(annotator__member_id=member_id), Q.AND)
            elif role_code == MemberRole.Provider:
                provider_condition.add(Q(provider__member_id=member_id), Q.AND)
                source_reviewer_condition.add(Q(provider__member_id=member_id), Q.AND)
            else:
                reviewer_condition.add(Q(reviewer__member_id=member_id), Q.AND)
                source_reviewer_condition.add(Q(reviewer__member_id=member_id), Q.AND)

        checkdatetime = datetime.now() + timedelta(days=-5)
        checkdatetime = date(checkdatetime.year, checkdatetime.month, checkdatetime.day)

        for idx in range(5):
            date_condition = '{}-{}'.format(checkdatetime.month, str(checkdatetime.day + 1).zfill(2))
            checkdatetime = checkdatetime - timedelta(days=-1)

            days.append(date_condition)
            annotator_qs = JobTalk.objects.filter(job_status=JobStatus.Complete
                                                            , job_date__year=checkdatetime.year
                                                            , job_date__month=checkdatetime.month
                                                            , job_date__day=checkdatetime.day)\
            .extra({'job_date_char': "CAST(DATE_FORMAT(job_date, '%%m-%%d') AS char)"}) \
            .values('job_date_char') \
            .filter(annotator_condition)\
            .annotate(job_date_count=Count('id')) \
            .order_by('job_date_char')
            annotator.append(
                [data['job_date_count'] for data in annotator_qs][0] if annotator_qs.count() > 0 else 0)

            source_reviewer_qs = JobTalkSource.objects.filter(inspection_status=InspectionStatus.Complete
                                                      , inspection_date__year=checkdatetime.year
                                                      , inspection_date__month=checkdatetime.month
                                                      , inspection_date__day=checkdatetime.day) \
            .extra({'inspection_date_char': "CAST(DATE_FORMAT(inspection_date, '%%m-%%d') AS char)"}) \
            .values('inspection_date_char') \
            .annotate(inspection_date_count=Count('id')) \
            .filter(source_reviewer_condition) \
            .order_by('inspection_date_char')

            source_reviewer.append(
                [data['inspection_date_count'] for data in source_reviewer_qs][0] if source_reviewer_qs.count() > 0 else 0)

            reviewer_qs = JobTalk.objects.filter(inspection_status=InspectionStatus.Complete
                                                           , inspection_date__year=checkdatetime.year
                                                           , inspection_date__month=checkdatetime.month
                                                           , inspection_date__day=checkdatetime.day) \
            .extra({'inspection_date_char': "CAST(DATE_FORMAT(inspection_date, '%%m-%%d') AS char)"}) \
            .values('inspection_date_char') \
            .annotate(inspection_date_count=Count('id')) \
            .filter(reviewer_condition) \
            .order_by('inspection_date_char')

            reviewer.append(
                [data['inspection_date_count'] for data in reviewer_qs][0] if reviewer_qs.count() > 0 else 0)

            reviewer_qs = JobTalk.objects.filter(inspection_status=InspectionStatus.Reject
                                                 , inspection_date__year=checkdatetime.year
                                                 , inspection_date__month=checkdatetime.month
                                                 , inspection_date__day=checkdatetime.day) \
            .extra({'inspection_date_char': "CAST(DATE_FORMAT(inspection_date, '%%m-%%d') AS char)"}) \
            .values('inspection_date_char') \
            .annotate(inspection_date_count=Count('id')) \
            .filter(reviewer_condition) \
            .order_by('inspection_date_char')
            annotator_reject.append(
                [data['inspection_date_count'] for data in reviewer_qs][0] if reviewer_qs.count() > 0 else 0)

            provider_qs = JobTalkSource.objects.filter(reg_date__year=checkdatetime.year
                                                 , reg_date__month=checkdatetime.month
                                                 , reg_date__day=checkdatetime.day) \
            .filter(provider_condition) \
            .extra({'reg_date_char': "CAST(DATE_FORMAT(reg_date, '%%m-%%d') AS char)"}) \
            .values('reg_date_char') \
            .annotate(reg_date_count=Count('id')) \
            .order_by('reg_date_char')

            provider.append(
                [data['reg_date_count'] for data in provider_qs][0] if provider_qs.count() > 0 else 0)

            source_reviewer_qs = JobTalkSource.objects.filter(inspection_status=InspectionStatus.Reject
                                                              , inspection_date__year=checkdatetime.year
                                                              , inspection_date__month=checkdatetime.month
                                                              , inspection_date__day=checkdatetime.day) \
                .extra({'inspection_date_char': "CAST(DATE_FORMAT(inspection_date, '%%m-%%d') AS char)"}) \
                .values('inspection_date_char') \
                .annotate(inspection_date_count=Count('id')) \
                .filter(source_reviewer_condition) \
                .order_by('inspection_date_char')

            provider_reject.append(
                [data['inspection_date_count'] for data in source_reviewer_qs][0] if source_reviewer_qs.count() > 0 else 0)

        context['all_notices'] = bbs_qs
        context['days'] = days
        context['annotator'] = annotator
        context['provider'] = provider
        context['source_reviewer'] = source_reviewer
        context['reviewer'] = reviewer
        context['source_reject'] = provider_reject
        context['annotator_reject'] = annotator_reject


        return context
