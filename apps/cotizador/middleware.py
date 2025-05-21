import time
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class QueryTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Código que se ejecuta antes de la vista
        start_time = time.time()
        initial_queries = len(connection.queries)

        response = self.get_response(request)

        # Código que se ejecuta después de la vista
        end_time = time.time()
        final_queries = len(connection.queries)

        # Solo registrar si DEBUG está activado
        if settings.DEBUG:
            total_time = end_time - start_time
            total_queries = final_queries - initial_queries

            # Registrar consultas que toman más de 0.5 segundos
            slow_queries = [
                {
                    'sql': q['sql'],
                    'time': float(q['time']),
                }
                for q in connection.queries[initial_queries:final_queries]
                if float(q['time']) > 0.5
            ]

            if slow_queries:
                logger.warning(
                    f"\nRequest: {request.path}\n"
                    f"Total time: {total_time:.2f}s\n"
                    f"Total queries: {total_queries}\n"
                    f"Slow queries:\n"
                    + "\n".join(
                        f"Time: {q['time']}s\nSQL: {q['sql']}\n"
                        for q in slow_queries
                    )
                )

        return response
