import csv
import os
import sys

import django
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'foodgram_backend.settings')
django.setup()

User = get_user_model()


def object_create(data, model, related_model: dict = None):
    if related_model:
        field = list(related_model.keys())[0]
        RelatedModel = related_model[field]
        data[field] = RelatedModel.objects.get(
            pk=data[field]
        )
    obj = model(**data)
    obj.save()


def parse_file_and_create_models(file, model, related_model=None):
    path = os.path.abspath(fr'./{file}')
    with open(file=path, mode='r', encoding='utf-8',) as f:
        reader = csv.reader(f)
        for unparsed_data in reader:
            data = {
                'name': unparsed_data[0],
                'measurement_unit': unparsed_data[1],
            }
            try:
                object_create(data, model, related_model)
            except Exception as e:
                raise Exception(f'Возникла ошибка типа {e}')
        sys.stdout.write(f'{file} done!\n')


class Command(BaseCommand):
    help = 'Добавляет данные из .csv файла в базу данных'

    def handle(self, *args, **options):
        parse_file_and_create_models('ingredients.csv', model=Ingredient)
