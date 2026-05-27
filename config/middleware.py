import time
import os
import psutil
import logging

logger = logging.getLogger(__name__)

class TelemetryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.process = psutil.Process(os.getpid())

    def __call__(self, request):
        start_time = time.time()
        
        # Safely measure memory
        try:
            start_memory = self.process.memory_info().rss
        except Exception:
            start_memory = 0
            
        response = self.get_response(request)
        
        duration = time.time() - start_time
        
        try:
            end_memory = self.process.memory_info().rss
            mem_diff_mb = (end_memory - start_memory) / (1024 * 1024)
            total_mem_mb = end_memory / (1024 * 1024)
        except Exception:
            mem_diff_mb = 0.0
            total_mem_mb = 0.0
            
        # Standard printed stdout log for direct Render logs inspection
        print(
            f"[TELEMETRY] PATH: {request.path} | "
            f"METHOD: {request.method} | "
            f"STATUS: {response.status_code} | "
            f"DURATION: {duration:.4f}s | "
            f"MEM_DIFF: {mem_diff_mb:+.2f}MB | "
            f"TOTAL_MEM: {total_mem_mb:.2f}MB"
        )
        
        return response
