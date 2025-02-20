from rest_framework import pagination

from recipes.constants import STANDART_PAGINATE_COUNT, UNLIMITED_PAGINATION


class PageNumberCustomPaginator(pagination.PageNumberPagination):
    page_size = STANDART_PAGINATE_COUNT
    page_size_query_param = 'limit'


class SubscriptionsRecipesPaginator(pagination.PageNumberPagination):
    page_size = UNLIMITED_PAGINATION
    page_size_query_param = 'recipes_limit'
    template = None
