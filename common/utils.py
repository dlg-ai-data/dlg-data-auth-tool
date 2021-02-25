import json
import os
import uuid
import re
from datetime import datetime
from os.path import getsize
from pathlib import Path, PurePosixPath

from django.core import serializers
from django.core.files.base import ContentFile
from collections import namedtuple
from django.db.models import QuerySet, Choices
from vaiv import settings
from common import choices


def KDataTableAjaxRequest(request):
    page = request.POST.get('pagination[page]')
    pages = request.POST.get('pagination[pages]')
    perpage = request.POST.get('pagination[perpage]')
    total = request.POST.get('pagination[total]')
    sort = request.POST.get('sort[sort]')
    sortField = request.POST.get('sort[field]')
    searchCondition = request.POST.get('query[generalSearch]')

    if sort == 'desc':
        sortField = '-' + sortField

    return page, pages, perpage, total, sort, sortField, searchCondition


def get_page_range(paginator, page, perpage):
    page_numbers_range = int(perpage)
    max_index = len(paginator.page_range)
    current_page = int(page) if page else 1
    start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
    end_index = start_index + page_numbers_range

    if end_index >= max_index:
        end_index = max_index
    return paginator.page_range[start_index:end_index]


def get_models_output_json(queryset):
    json_object = json.loads(serializers.serialize("json", list(queryset)))
    output = []
    for item in json_object:
        item['fields']['id'] = item['pk']
        output.append(item['fields'])
    return output


def get_models_output_values_json(queryset):
    return list(queryset)


def handler_file_write(file):
    wrtie_path = PurePosixPath(str(datetime.now().year)
                            , str(datetime.now().month).rjust(2, '0')
                            , str(datetime.now().day).rjust(2, '0'))
    write_media_path = PurePosixPath(settings.MEDIA_ROOT, wrtie_path)

    file_name, file_extension = os.path.splitext('./' + str(file))
    file_name = str(uuid.uuid1()).replace('-', '') + file_extension

    if not os.path.isdir(write_media_path):
        os.makedirs(write_media_path)

    with open(PurePosixPath(write_media_path, file_name), 'wb+') as file_output:
        for chunk in file.chunks():
            file_output.write(chunk)

    return wrtie_path, file_name, str(file), getsize(PurePosixPath(write_media_path, file_name))


def get_page_range(paginator, page):
    page_numbers_range = 10
    max_index = len(paginator.page_range)
    current_page = int(page) if page else 1
    start_index = int((current_page - 1) / page_numbers_range) * page_numbers_range
    end_index = start_index + page_numbers_range

    if end_index >= max_index:
        end_index = max_index
    return paginator.page_range[start_index:end_index]

def convert_dict_to_queryset(obj_name, dict_queryset):
    return [(namedtuple(obj_name, obj.keys())(*obj.values())) for obj in dict_queryset]

