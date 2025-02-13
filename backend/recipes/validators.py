import re

from django.core.exceptions import ValidationError

from .constants import INVALID_NAMES


def username_validator(value):
    for name in INVALID_NAMES:
        if value == name:
            raise ValidationError(
                message=f'Нельзя использовать {name} в качестве \"username\"',
                params={"value": value},
            )
    if re.fullmatch(r'^[\w.@+-]+\Z', value) is None:
        raise ValidationError(
            message='Можно использовать латинские буквы и символы ., @, +, -.',
            params={"value": value},
        )
    elif len(value) < 2:
        raise ValidationError(
            message='Нельзя использовать username менее 3-ех символов',
            params={"value": value},
        )


def name_validator(value):
    for name in INVALID_NAMES:
        if value == name:
            raise ValidationError(
                message=f'Нельзя использовать {name} для поля name',
                params={"value": value},
            )
    if len(value) < 3:
        raise ValidationError(
            message='Нельзя использовать name менее 4-ех символов',
            params={"value": value},
        )
