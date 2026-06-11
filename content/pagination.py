from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class CustomPagination(PageNumberPagination):
    """Custom pagination with meta information"""
    
    page_size = 9
    page_size_query_param = 'limit'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': data,
            'meta': {
                'current_page': self.page.number,
                'total_pages': self.page.paginator.num_pages,
                'total_items': self.page.paginator.count,
                'per_page': self.page_size,
                'has_next': self.page.has_next(),
                'has_previous': self.page.has_previous(),
            }
        })
