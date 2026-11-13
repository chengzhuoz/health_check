import time
import logging

logger = logging.getLogger(__name__)

class RequestTimeCostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        end_time = time.time()
        cost_time_ms = int((end_time - start_time) * 1000)
        
        request_path = request.path
        method = request.method
        
        logger.info(f"[{method}] {request_path} cost: {cost_time_ms} ms")
        
        response['X-Request-Cost-Time'] = str(cost_time_ms)
        
        return response