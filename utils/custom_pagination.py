from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 5000

    def paginate_queryset(self, queryset, request, view=None):
        page_size = request.query_params.get('page_size')

        if page_size:
            if page_size.isdigit():
                limit = int(page_size)

                if limit > self.max_page_size:
                    error = {"statusCode": 400, "error": True, "data": "",
                             "message": "Bad Request, Please check request",
                             "errors": {"page_size": [
                                 "page_size should be less than or equal to {0}".format(self.max_page_size)], }}
                    raise serializers.ValidationError(error)
            else:
                error = {"statusCode": 400, "error": True, "data": "",
                         "message": "Bad Request, Please check request",
                         "errors": {"page_size": [
                             "Invalid page_size."]}}
                raise serializers.ValidationError(
                    error)

        return super(self.__class__, self).paginate_queryset(queryset, request, view)
