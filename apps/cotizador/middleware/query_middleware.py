import time
import logging
from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class QueryTimeMiddleware(MiddlewareMixin):
    """
    Middleware to log database query execution time.
    Only active when DEBUG is True.
    """
    def process_request(self, request):
        if settings.DEBUG:
            request.start_time = time.time()

    def process_response(self, request, response):
        if settings.DEBUG and hasattr(request, 'start_time'):
            total_time = time.time() - request.start_time
            # Log queries that take more than 0.5 seconds
            if total_time > 0.5:
                for query in connection.queries:
                    if float(query['time']) > 0.5:
                        logger.warning(
                            f"Slow query detected ({query['time']}s): {query['sql']}"
                        )
                logger.info(
                    f"Request to {request.path} took {total_time:.2f}s "
                    f"with {len(connection.queries)} queries"
                )
        return response
