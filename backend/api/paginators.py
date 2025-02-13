from rest_framework import pagination


class PageNumberCustomPaginator(pagination.PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'


class SubscriptionsRecipesPaginator(pagination.PageNumberPagination):
    page_size = 999
    page_size_query_param = 'recipes_limit'
    template = None
