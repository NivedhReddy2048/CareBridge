import logging
import json
import traceback
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        if record.exc_info:
            log_record["exception"] = "".join(traceback.format_exception(*record.exc_info))
            
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id
            
        if hasattr(record, "latency"):
            log_record["latency_ms"] = record.latency

        return json.dumps(log_record)

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

# Pre-defined loggers
ai_logger = get_logger('carebridge.ai')
celery_logger = get_logger('carebridge.celery')
billing_logger = get_logger('carebridge.billing')
storage_logger = get_logger('carebridge.storage')
websocket_logger = get_logger('carebridge.websockets')
