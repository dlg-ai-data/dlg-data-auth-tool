from django.db import models


class UseType(models.TextChoices):
    Y = 'Y', 'Y'
    N = 'N', 'N'


class MemberRole(models.TextChoices):
    Annotrator = 'MR01', '어노테이터'
    Reviewer = 'MR02', '리뷰어'
    SummaryReviewer = 'MR03', '요약리뷰어'
    Provider = 'MR04', '대화제공자'


class MemberGrade_Choice(models.TextChoices):
    Beginner = 'AA01', '초급자'
    Intermediate = 'AA02', '중급자'
    Advanced = 'AA03', '고급자'
    Provider = 'AA04', '대화제공자'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'AA01': '초급자' \
                , 'AA02': '중급자' \
                , 'AA03': '고급자'
                , 'AA04': '대화제공자'}[value]


class BankCode(models.TextChoices):
    KB = 'AB01', '국민은행'
    Shinhan = 'AB02', '신한은행'
    NH = 'AB03', '농협'
    Hana = 'AB04', '하나은행'
    Kakao = 'AB05', '카카오뱅크'
    IBK = 'AB06', '기업은행'
    WOORI = 'AB07', '우리은행'
    KBANK = 'AB08', '케이뱅크'
    KFCC = 'AB09', '새마을금고'
    EPOST = 'AB10', '우체국'
    SCBANK = 'AB11', 'SC은행'
    KNBANK = 'AB12', '경남은행'
    CUBANK = 'AB13', '신협'
    CITYBANK = 'AB14', '씨티은행'
    SUHYUP = 'AB15', '수협'
    KDB = 'AB16', '산업은행'
    KJBANK = 'AB17', '광주은행'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'AB01': '국민은행' \
                , 'AB02': '신한은행' \
                , 'AB03': '농협' \
                , 'AB04': '하나은행' \
                , 'AB05': '카카오뱅크' \
                , 'AB06': '기업은행' \
                , 'AB07': '우리은행' \
                , 'AB08': '케이뱅크' \
                , 'AB09': '새마을금고' \
                , 'AB10': '우체국' \
                , 'AB11': 'SC은행' \
                , 'AB12': '경남은행' \
                , 'AB13': '신협' \
                , 'AB14': '씨티은행' \
                , 'AB15': '수협' \
                , 'AB16': '산업은행'\
                , 'AB17': '광주은행'}[value]


class BBSType(models.TextChoices):
    QnA = 'AC01', '1:1문의'
    Notice = 'AC02', '공지사항'
    Reference = 'AC03', '자료실'


class BBSContentsType(models.TextChoices):
    Join = 'AD01', '회원가입'
    Site = 'AD02', '홈페이지'
    Credit = 'AD03', '크레딧'
    Job = 'AD04', '대화조각'
    Etc = 'AD05', '기타문의'


class BBSStatusType(models.TextChoices):
    Writing = 'AE01', '작성중'
    Complete = 'AE02', '작성완료'
    Answered = 'AE03', '답변완료'


class FileType(models.TextChoices):
    BBSFile = 'AF01', '게시판 첨부파일',
    UCTFile = 'AF02', '계약서 첨부파일',
    UBBFile = 'AF03', '통장사본 첨부파일',
    UITFile = 'AF04', '신분서류 첨부파일',
    UDPFile = 'AF05', '장애증빙 첨부파일',
    RESFile = 'AF06', '이력서 첨부파일',
    AGRFile = 'AF07', '동의서 첨부파일'

class CalcType(models.TextChoices):
    TAX = 'AI01', 'TAX'
    VAT = 'AI02', 'VAT'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'AI01': 'TAX' \
                , 'AI02': 'VAT'}[value]


class PayType(models.TextChoices):
    Request = 'AJ01', '기타'
    Monthly = 'AJ02', '월마감'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'AJ01': '포인트지급신청' \
                , 'AJ02': '월마감'}[value]


class JobStatus(models.TextChoices):
    Initial = 'AK01', '초기'
    Complete = 'AK02', '작업완료'
    Writing = 'AK03', '작업중'
    Exclude = 'AK04', '작업제외'
    Recover = 'AK05', '회수'


class InspectionStatus(models.TextChoices):
    Initial = 'AL01', '초기'
    Reject = 'AL02', '반려'
    Complete = 'AL03', '승인'
    Impossible = 'AL04', '불가'
    Inspection = 'AL05', '검수 중'


class PointStatus(models.TextChoices):
    Initial = 'AM01', '초기'
    Complete = 'AM02', '적립완료'


class CalcStatus(models.TextChoices):
    Initial = 'AN01', '진행중'
    Complete = 'AN02', '정산완료'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'AN01': '진행중' \
                , 'AN02': '정산완료'}[value]


class GenderType(models.TextChoices):
    Man = 'AO01', '남자'
    Woman = 'AO02', '여자'


class AgeType(models.TextChoices):
    Teenager = 'AP01', '10대'
    Twenty = 'AP02', '20대'
    Thirty = 'AP03', '30대'
    Forty = 'AP04', '40대'
    FifTy = 'AP05', '50대'
    Sixty = 'AP06', '60대'


class JobJoinType(models.TextChoices):
    Living = 'AQ01', '생계형'
    Sideline = 'AQ02', '부업형'
    Contribution = 'AQ03', '사회공헌'
    Leisure = 'AQ04', '여가시간'


class WorkTimeType(models.TextChoices):
    All = 'AR01', '종일'
    Morning = 'AR02', '오전'
    Afternoon = 'AR03', '오후'
    Nighttime = 'AR04', '야간'
    Dawn = 'AR05', '새벽'
    Week = 'AR06', '주중'
    Saturday = 'AR07', '토요일'
    Sunday = 'AR08', '일요일'


class MemberJobType(models.TextChoices):
    Research = 'AS01', '연구직'
    Office = 'AS02', '사무직'
    Manufacturing = 'AS03', '제조업'
    Inoccupation = 'AS04', '무직'
    Medical = 'AS05', '의료직'
    Nursery = 'AS06', '어린이관련'
    Caregiver = 'AS07', '요양관련'
    Official = 'AS08', '공무원'
    Colleger = 'AS09', '대학생'
    ETC = 'AS10', '기타'


class MemberJoinSource(models.TextChoices):
    Internet = 'AT01', 'SNS/블로그'
    Notification = 'AT02', '모집공고'
    Friend = 'AT03', '지인추천'
    Yuseong = 'AT04', '유성구청'
    KAPO = 'AT05', '정리수납협회'
    Ibabynews = 'AT06', '베이비뉴스'
    Reseat = 'AT07', '고경력과학기술연구협회'
    Daejeon = 'AT08', '대전시청'
    AIHUB = 'AT09', 'AIHUB'
    PHOTO = 'AT10', '알바사이트(사진촬영)'
    BOOKMACHINEREADING = 'AT11', '도서자료기계독해'
    DAEDEOKSCIENCE = 'AT12', '대덕과학기술사회적협동조합'
    ANORECRUIT = 'AT13', '어노테이터 모집(SNS)'
    GWANGJU = 'AT14', '광주광역시'
    OYOUTUBE = 'AT15', '오과장유튜브'
    DAEGU = 'AT16', '대구광역시'
    GYEONGSANGBUKDO = 'AT17', '경상북도'
    DAEJEONYOUTHCOOPERATIVEFEDERATION = 'AT18', '대전청년협동조합'
    VQA1 = 'AT19', 'VQA1'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'AT01': 'SNS/블로그' \
                , 'AT02': '모집공고' \
                , 'AT03': '지인추천' \
                , 'AT04': '유성구청' \
                , 'AT05': '정리수납협회' \
                , 'AT06': '베이비뉴스' \
                , 'AT07': '고경력과학기술연구협회' \
                , 'AT08': '대전시청' \
                , 'AT09': 'AIHUB' \
                , 'AT10': '알바사이트(사진촬영)' \
                , 'AT11': '도서자료기계독해' \
                , 'AT12': '대덕과학기술사회적협동조합' \
                , 'AT13': '어노테이터 모집(SNS)' \
                , 'AT14': '광주광역시' \
                , 'AT15': '오과장유튜브' \
                , 'AT16': '대구광역시' \
                , 'AT17': '경상북도' \
                , 'AT18': '대전청년협동조합'\
                , 'AT19': 'VQA1'}[value]


class JoinType(models.TextChoices):
    Annotator = 'AU01', 'Annotator'
    Reviewer = 'AU02', 'Reviewer'


class JoinStatus(models.TextChoices):
    Initial = 'AV01', '신청중'
    Reject = 'AV02', '승인불가'
    Complete = 'AV03', '승인완료'


class AuthCertStatus(models.TextChoices):
    Failed = 'AW01', '인증실패'
    Timeout = 'AW02', '타임아웃'
    Completed = 'AW03', '인증된상태'
    Success = 'AW04', '인증성공'


class DeIdentificationStatus(models.TextChoices):
    NotNeed = 'AY01', '불필요'
    Initial = 'AY02', '작업전'
    Completed = 'AY03', '작업완료'

class WorkType(models.TextChoices):
    Create = 'BC01', '생성'
    Update = 'BC02', '변경'
    Delete = 'BC03', '삭제'
    Reset = 'BC04', '초기화'

class QAType(models.TextChoices):
    UserQuestion = 'BA01', '(질문)사용자'
    SystemQuestion = 'BA02', '(질문)시스템'
    UserAnswer = 'BA03', '(답변)사용자'
    SystemAnswer = 'BA04', '(답변)시스템'
    Noti = 'BA05', '(공지)시스템'

class JobSourceType(models.TextChoices):
    Provider = 'BB01', '대화원문제공'
    TalkSummary = 'BB02', '대화조각요약'
    SourceInspection = 'BB03', '대화원문검수'
    TalkInspection = 'BB04', '대화요약검수'

    @staticmethod
    def get_value(value):
        if value == '' or value is None:
            return ''
        else:
            return {'BB01': '대화원문제공' \
                    ,'BB02': '대화조각요약'\
                    ,'BB03': '대화원문검수'\
                    ,'BB04': '대화요약검수'}[value]