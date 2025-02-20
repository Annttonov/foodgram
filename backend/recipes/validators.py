from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

from .constants import INVALID_NAMES

username_validator = UnicodeUsernameValidator()


def name_validator(value):
    for name in INVALID_NAMES:
        if value == name:
            raise ValidationError(
                message=f'Нельзя использовать {name} для поля name',
                params={"value": value},
            )
    if len(value) < 2:
        raise ValidationError(
            message='Нельзя использовать name менее 4-ех символов',
            params={"value": value},
        )
