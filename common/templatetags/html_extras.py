from datetime import date, timedelta

from django import template
from django.db.models import Q, Sum

from calc.models import CalcDetail
from common.AESCipher import AESCipher
from common.choices import *
import importlib
import socket
import os
from dataset.models import Dataset
from member.models import User, MemberGrade

register = template.Library()

# 새로 프로젝트 타입이 추가되면 choice 에 추가될 것이고, 여기에도 색을 따로 추가해줘야 함. 그것만 하면 됨.
# 원래는 수동적으로 프로젝트 타입이 쓰는 곳에 일일이 다 추가해줘야 했음.

color_list = [
    # "color background-color"
    "#3699FF !important,#e1f0ff !important",  # light-primary
    "#F64E60 !important,#ffe2e5 !important",  # light-danger
    "#FFA800 !important,#fff4de !important",  # light-warning
    "#8950FC !important,#eee5ff !important",  # light-info
    "#3F4254 !important,#e4e6ef !important",  # secondary
    "#1BC5BD !important,#C9F7F5 !important",  # light-success
]

@register.filter(name='plus')
def plus(value, value2):
    return value + value2
@register.filter(name='minus')
def minus(value, value2):
    return value - value2
@register.filter(name='calc_share')
def calc_share(divided, divisor):
    return divided // divisor
@register.filter(name='get_groupcount')
def get_groupcount(groupcount, seq):
    if seq > 1:
        return groupcount - seq + 1
    else:
        return groupcount

@register.filter(name='get_rowspan')
def get_rowspan(group_count, rev_loopcount):
    if rev_loopcount < group_count:
        return rev_loopcount
    else:
        return group_count

@register.filter(name='group_count')
def group_count(value, group_count):
    share = calc_share(value, group_count)
    if value % group_count == 0:
        return share - 1
    else:
        return share
@register.filter(name='parse_rrn')
def parse_rrn(value, type):
    if value is None or value == '':
        return ''
    rrn = AESCipher().decrypt(value)
    if type == 'head':
        return rrn[:6]
    elif type == 'rear':
        return rrn[6:]


@register.filter(name='parse_tel')
def parse_tel(tel, type):
    section = tel.split("-")
    if type == 'head':
        return section[0]
    elif type == 'middle':
        return section[1]
    elif type == 'rear':
        return section[2]


@register.filter(name='zero_to_blank')
def zero_to_blank(value):
    if value == 0:
        return ''
    else:
        return value


@register.filter(name='wiyn')
def wiyn(member_id):
    someone = User.objects.get(id=member_id)  # 회원의 id를 받아와 레코드를 가져온다.
    if someone:
        return someone.name
    else:
        return None


@register.filter(name='get_start_path')
def get_start_path(current_path, target_path):
    if current_path == '/':
        return ''
    if current_path.split('/')[:-2][1] == target_path or current_path.split('/')[:4] == target_path.split('/')[:4]:
        return 'menu-item-open'


@register.filter(name='get_start_path_sub')
def get_start_path_sub(current_path, target_path):
    if current_path == '/':
        return ''
    if target_path in current_path:
        return 'menu-item-open'

@register.filter(name='get_member_grade')
def get_member_grade(member_id):
    member_grade = MemberGrade.objects.get(member_id=member_id, valid_yn=UseType.Y)
    return member_grade.grade_code

@register.filter(name='get_member_grade_name')
def get_member_grade_name(member_id):
    member_grade = MemberGrade.objects.get(member_id=member_id, valid_yn=UseType.Y)
    return '<span class="label label-inline ' + member_grade.get_member_grade_color() + '">' + member_grade.get_grade_code_display() + '</span>'

@register.filter(name='page_seq_print')
def page_seq_print(value, args):
    page = args.paginator.page(args.number)
    return page.start_index() + int(value)


@register.filter(name='take_value_in_dict')
def take_value_in_dict(data_structure, key):
    if isinstance(data_structure, list):
        data_structure = dict(data_structure)
    return data_structure[key]


@register.filter(name='cut_text')
def cut_text(value, length):
    if value is not None and value != '' and len(value) > length:
        return value[:length]
    else:
        return value


@register.filter(name='toInt')
def toInt(value):
    if value is not None and value != '' and value.isdigit():
        return int(value)
    else:
        return value


@register.filter(name='calc_divide')
def calc_divide(divided, divisor):
    return divided / divisor


@register.filter(name='calc_remainder')
def calc_remainder(divided, divisor):
    return divided % divisor


@register.filter(name='add_extra')
def add_extra(val1, val2):
    if val1 is None:
        val1 = 0
    if val2 is None:
        val2 = 0
    return val1 + val2


@register.inclusion_tag(filename='partials/default_text.html',
                        takes_context=False, name='advanced_default_if_none')
def advanced_default_if_none(**kwargs):
    value = get_dict_value(kwargs, 'value')
    default_text = get_dict_value(kwargs, 'default_text')
    style = get_dict_value(kwargs, 'style')
    filterName = get_dict_value(kwargs, 'filter')
    args = get_dict_value(kwargs, 'args')
    temp = value
    if value == '0' or value == 0:
        value = None
    if style is None:
        style = 'color: #a4b0be;'
    if isinstance(value, str):
        temp = value
        temp = temp.replace(" ", "")
    if value is None \
            or (isinstance(value, list) and len(value) == 0) \
            or (isinstance(value, list) and isinstance(value[0], str) and value[0].replace(" ", "") == "") \
            or ((temp is not None) and isinstance(temp, str) and len(temp) == 0):
        return {'default_text': default_text, 'style': style, 'is_default': True}
    else:
        return {'value': value, 'is_default': False, 'filter': filterName, 'args': args}


@register.inclusion_tag(filename='partials/searched_keyword_highlight_message.html',
                        takes_context=False, name='search_result_highlight_message')
def search_result_highlight_message(**kwargs):
    word = get_dict_value(kwargs, 'word')
    text_limit = get_dict_value(kwargs, 'text_limit')
    return {'word': word, 'text_limit': text_limit}


@register.inclusion_tag(filename='partials/div_input_search.html',
                        takes_context=False, name='div_input_search')
def div_input_search(**kwargs):
    tooltip_text = get_dict_value(kwargs, 'tooltip_text')
    value = get_dict_value(kwargs, 'value')
    return {'tooltip_text': tooltip_text, 'value': value}


@register.inclusion_tag(filename='partials/td_search_fail_message.html',
                        takes_context=False, name='td_search_fail_message')
def td_search_fail_message(**kwargs):
    searched_word = get_dict_value(kwargs, 'searched_word')
    text_limit = get_dict_value(kwargs, 'text_limit')
    search_fail_message = get_dict_value(kwargs, 'search_fail_message')
    select_fail_message = get_dict_value(kwargs, 'select_fail_message')
    no_data_message = get_dict_value(kwargs, 'no_data_message')
    isSelected = get_dict_value(kwargs, 'isSelected')
    isSearched = get_dict_value(kwargs, 'isSearched')
    return {'searched_word': searched_word, 'text_limit': text_limit, 'search_fail_message': search_fail_message,
            'select_fail_message': select_fail_message, 'no_data_message': no_data_message, 'isSelected': isSelected,
            'isSearched': isSearched}


@register.inclusion_tag(filename='partials/inspection_state_count_table_tr.html',
                        takes_context=False, name='inspection_state_count_aggregation_card')
def inspection_state_count_aggregation_card(**kwargs):
    project_type = get_dict_value(kwargs, 'project_type')
    card_title = get_dict_value(kwargs, 'card_title')
    inspection_state_count = get_dict_value(kwargs, 'inspection_state_count')
    return {'project_type': project_type, 'card_title': card_title, 'inspection_state_count': inspection_state_count}


@register.inclusion_tag(filename='partials/checkbox_text_choices.html',
                        takes_context=False, name='tag_checkbox_text_choices')
def tag_checkbox_text_choices(**kwargs):
    value = get_dict_value(kwargs, 'value')
    name = get_dict_value(kwargs, 'name')
    class_name = get_dict_value(kwargs, 'class_name')
    disabled = get_dict_value(kwargs, 'disabled')

    if class_name == 'work_time_type':
        choiceClass = WorkTimeType.choices

    if disabled is None or disabled == '':
        disabled = False

    return {'choices': choiceClass, 'value': value, 'name': name, 'disabled': disabled}


# <option> 태그
# models.TextChoices
@register.inclusion_tag(filename='partials/options_text_choices.html',
                        takes_context=False, name='tag_options_text_choices')
def tag_options_text_choices(**kwargs):
    value = get_dict_value(kwargs, 'value')
    values = get_dict_value(kwargs, 'values')
    blank_option = get_dict_value(kwargs, 'blank_option')
    blank_text = get_dict_value(kwargs, 'blank_text')
    blank_value = get_dict_value(kwargs, 'blank_value')
    class_name = get_dict_value(kwargs, 'class_name')
    is_label_setting = get_dict_value(kwargs, 'is_label_setting')
    unregistered_option = get_dict_value(kwargs, 'unregistered_option')
    project_type = get_dict_value(kwargs, 'project_type')
    all_select = get_dict_value(kwargs, 'all_select')
    blank_disabled = get_dict_value(kwargs, 'blank_disabled')

    useType_color = [
        'label-light-primary',
        'label-light-danger',
    ]

    payType_color = [
        'label-outline-info',
        'label-outline-dark',
    ]

    calcType_color = [
        'label-outline-success',
        'label-outline-warning',
    ]

    CalcStatus_color = [
        'label-outline-danger',
        'label-outline-primary',
    ]
    CalcStatus_style = [
        'width: 63.5px;',
        '',
    ]

    requestType_color = calcType_color
    requestType_style = [
        '',
        'width: 71px;',
    ]

    inspectionStatus_color = [
        'label-secondary',
        'label-light-warning',
        'label-light-success',
        'label-light-danger',
        'label-light-info'
    ]
    inspectionStatus_style = [
        'width: 63.5px;',
        'width: 63.5px;',
        'width: 63.5px;',
        'width: 63.5px;',
        'width: 63.5px;'
    ]

    jobStatus_color = [
        'label-secondary',
        'label-light-primary',
        'label-light-danger',
        'label-light-warning'
    ]
    jobStatus_style = [
        'width: 63.5px;',
        'width: 63.5px;',
        'width: 63.5px;',
        'width: 63.5px;'
    ]

    memberGrade_color = [
        'label-success',
        'label-warning',
        'label-primary',
        'label-danger',
        'label-dark'
    ]

    contentType_color = [
        'label-outline-primary',
        'label-outline-danger',
        'label-outline-warning',
        'label-outline-info',
        'label-outline-secondary',
    ]

    contentType_style = [
        'width: 63.5px; border-radius: 0rem !important;',
        'width: 63.5px; border-radius: 0rem !important;',
        'width: 63.5px; border-radius: 0rem !important;',
        'width: 63.5px; border-radius: 0rem !important;',
        'width: 63.5px; border-radius: 0rem !important;'
    ]

    colors, styles, choiceClass = None, None, None
    colored = False
    styled = False
    is_multi_select = False
    is_not_choice = False
    if blank_option is None:
        blank_option = True

    if all_select is None:
        all_select = False

    if blank_disabled is None:
        blank_disabled = False

    if values is not None :
        if 'all' not in values:
            for i in range(len(values)):
                try:
                    values[i] = int(values[i])
                except ValueError:
                    pass
        is_multi_select = True

    if is_label_setting is None:
        is_label_setting = False

    if class_name == 'UseType':
        choiceClass = UseType.choices
        colors = useType_color
    if class_name == 'PayType':
        choiceClass = PayType.choices
        colors = payType_color
    if class_name == 'CalcType':
        choiceClass = CalcType.choices
        colors = calcType_color
    if class_name == 'CalcStatus':
        choiceClass = CalcStatus.choices
        colors = CalcStatus_color
        styles = CalcStatus_style
    if class_name == 'JoinType':
        choiceClass = JoinType.choices
        colors = requestType_color
        styles = requestType_style
    if class_name == 'MemberGrade':
        choiceClass = MemberGrade_Choice.choices
        colors = memberGrade_color
    if class_name == 'BBSContentsType':
        choiceClass = BBSContentsType.choices
        colors = contentType_color
        styles = contentType_style
    if class_name == 'InspectionStatus':
        choiceClass = InspectionStatus.choices
        colors = inspectionStatus_color
        styles = inspectionStatus_style
    if class_name == 'Bbox_InspectionStatus':
        choiceClass = [InspectionStatus.choices[0], InspectionStatus.choices[1], InspectionStatus.choices[2]]
        colors = inspectionStatus_color
        styles = inspectionStatus_style
    if class_name == 'Seg_InspectionStatus':
        choiceClass = [InspectionStatus.choices[0], InspectionStatus.choices[1], InspectionStatus.choices[2]]
        colors = inspectionStatus_color
        styles = inspectionStatus_style
    if class_name == 'Tqa_InspectionStatus':
        choiceClass = [InspectionStatus.choices[0], InspectionStatus.choices[1], InspectionStatus.choices[2]]
        colors = inspectionStatus_color
        styles = inspectionStatus_style
    if class_name == 'Vqa_InspectionStatus':
        choiceClass = [InspectionStatus.choices[0], InspectionStatus.choices[1], InspectionStatus.choices[2]]
        colors = inspectionStatus_color
        styles = inspectionStatus_style
    if class_name == 'Image_InspectionStatus':
        choiceClass = InspectionStatus.choices
        colors = inspectionStatus_color
        styles = inspectionStatus_style
    if class_name == 'JobStatus':
        choiceClass = [JobStatus.choices[0], JobStatus.choices[1], JobStatus.choices[3], JobStatus.choices[4]]
        colors = jobStatus_color
        styles = jobStatus_style
    if class_name == 'Bbox_JobStatus':
        choiceClass = [JobStatus.choices[0], JobStatus.choices[1], JobStatus.choices[3], JobStatus.choices[4]]
        colors = jobStatus_color
        styles = jobStatus_style
    if class_name == 'Seg_JobStatus':
        choiceClass = [JobStatus.choices[0], JobStatus.choices[1], JobStatus.choices[3], JobStatus.choices[4]]
        colors = jobStatus_color
        styles = jobStatus_style
    if class_name == 'Tqa_JobStatus':
        choiceClass = [JobStatus.choices[0], JobStatus.choices[1], JobStatus.choices[3], JobStatus.choices[4]]
        colors = jobStatus_color
        styles = jobStatus_style
    if class_name == 'Vqa_JobStatus':
        choiceClass = [JobStatus.choices[0], JobStatus.choices[1]]
        colors = jobStatus_color
        styles = jobStatus_style
    if class_name == 'Image_JobStatus':
        choiceClass = [JobStatus.choices[0], JobStatus.choices[1], JobStatus.choices[3], JobStatus.choices[4]]
        colors = jobStatus_color
        styles = jobStatus_style
    if class_name == 'MemberRole':
        choiceClass = MemberRole.choices

    if class_name == 'bank_code':
        choiceClass = BankCode.choices
    if class_name == 'job_join_type':
        choiceClass = JobJoinType.choices
    if class_name == 'work_time_type':
        choiceClass = WorkTimeType.choices
    if class_name == 'member_job_type':
        choiceClass = MemberJobType.choices
    if class_name == 'member_join_source':
        choiceClass = MemberJoinSource.choices

    if class_name == 'DatasetSelectList':
        datasets = Dataset.objects.all()
        choiceClass = [(item.id, item.dataset_name) for item in datasets]

    if class_name == 'DeIdentificationStatus':
        choiceClass = DeIdentificationStatus.choices

    if class_name == 'QAType':
        choiceClass = QAType.choices
    if class_name == 'JobSourceType':
        choiceClass == JobSourceType.choices

    if colors:
        colored = True
        for idx, item in enumerate(choiceClass):
            choiceClass[idx] += (colors[idx],)
    if styles:
        styled = True
        for idx, item in enumerate(choiceClass):
            choiceClass[idx] += (styles[idx],)

    return {'choices': choiceClass, 'value': value, 'values': values, 'blank_option': blank_option,
            'unregistered_option': unregistered_option, 'all_select': all_select, 'blank_disabled': blank_disabled,
            'blank_text': blank_text, 'blank_value': blank_value, 'colored': colored, 'styled': styled,
            'is_multi_select': is_multi_select, 'is_not_choice': is_not_choice, 'is_label_setting': is_label_setting,
            'class_name': class_name}


@register.filter
def get_at_index(object_list, index):
    return object_list[index]


@register.filter(name='get_rate')
def get_rate(count, total):
    if count is None or total is None:
        return 0.0
    else:
        count = int(count)
        total = int(total)
        return format((count / total * 100), '10.1f')


def get_dict_value(dic, key):
    val = None
    if key in dic:
        val = dic[key]
    if val == '':
        val = None
    return val

@register.filter(name='get_job_price')
def get_job_price(calc_id):
    select_result = list(CalcDetail.objects.filter(calc_id=calc_id). \
                         values('calc_id'). \
                         annotate(Sum('job_price')). \
                         values('job_price__sum'))
    if len(select_result) != 0:
        return select_result[0]['job_price__sum']
    else:
        return None


@register.filter(name='get_grade_price')
def get_grade_price(calc_id):
    select_result = CalcDetail.objects.filter(calc_id=calc_id). \
        values('calc_id'). \
        annotate(Sum('grade_price')). \
        values('grade_price__sum')
    if len(select_result) != 0:
        return select_result[0]['grade_price__sum']
    else:
        return None

@register.filter
def modulo(num, val):
    return num % val


def return_start_end_date(date_string):
    temp = date_string.split(" ")
    start_date = temp[0].split("-")
    end_date = temp[2].split("-")

    start_date = date(int(start_date[0]), int(start_date[1]), int(start_date[2]))
    end_date = date(int(end_date[0]), int(end_date[1]), int(end_date[2])) + timedelta(days=1)
    return start_date, end_date
