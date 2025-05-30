from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

def generate_paginated_response(response, data):
        return Response({
        'prev page' : response.get_previous_link(),
        'next page' : response.get_next_link(),
        'current page' : response.page.number,
        'total pages' : response.page.paginator.num_pages,
        'total count' : response.page.paginator.count,
        'results' : data
        })

class PostCommentsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return generate_paginated_response(self, data)



class LikePagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'

    def get_paginated_response(self, data):
        return generate_paginated_response(self, data)
