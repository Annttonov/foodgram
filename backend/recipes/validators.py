from django.core.exceptions import ValidationError


def username_validator(value):
    if value == 'me':
        raise ValidationError(
            message='Нельзя использовать me в качестве username',
            params={"value": value},
        )
    elif len(value) < 2:
        raise ValidationError(
            message='Нельзя использовать username менее 3-ех символов',
            params={"value": value},
        )
