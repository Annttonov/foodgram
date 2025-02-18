SHORT_TITLE = 40

SHORT_NAME = 25

STANDART_FIELD_LENGTH = 64

INVALID_NAMES = {'tags', 'tag', 'ingredients', 'ingredient', 'recipe',
                 'recipes', 'username', 'user', 'id', 'pk', 'me'}

USER_NAME_REGEX = r'^[\w.@+-]+\Z`'


def field_error_message(field):
    return f'Поле \"{field}\" Не может быть пустым или отсутствовать вовсе.'
