#!/usr/bin/env python
import os
import sys
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('smoke_tests')

def run_smoke_tests():
    """
    CareBridge Enterprise Smoke Test Runner
    Validates the availability of critical infrastructure, databases, and APIs.
    """
    logger.info("Starting CareBridge Enterprise Smoke Tests...")
    
    # 1. Django Setup
    try:
        import django
        from django.conf import settings
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
        django.setup()
        logger.info("Django setup successful.")
    except Exception as e:
        logger.error(f"Django setup failed: {e}")
        return False

    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {},
        "summary": "PASS"
    }

    # Helper for running tests
    def run_test(name, test_func):
        try:
            test_func()
            results["tests"][name] = "PASS"
            logger.info(f"Test '{name}' PASSED.")
        except Exception as e:
            results["tests"][name] = f"FAIL: {str(e)}"
            results["summary"] = "FAIL"
            logger.error(f"Test '{name}' FAILED: {e}")

    # 2. Database Connectivity
    def test_database():
        from django.db import connections
        connections['default'].cursor().execute("SELECT 1")
    run_test("Database Connectivity", test_database)

    # 3. Redis Connectivity
    def test_redis():
        from django.core.cache import cache
        cache.set('smoke_test', 'ok', timeout=1)
        if cache.get('smoke_test') != 'ok':
            raise Exception("Redis cache mismatch")
    run_test("Redis Connectivity", test_redis)

    # 4. Celery Availability (check broker url)
    def test_celery():
        broker_url = os.environ.get('REDIS_URL')
        if not broker_url:
            raise Exception("REDIS_URL for Celery broker not found")
    run_test("Celery Configuration", test_celery)
    
    # 5. AWS / Storage Config
    def test_storage():
        bucket = os.environ.get('AWS_STORAGE_BUCKET_NAME')
        # If in production, ensure bucket is set. In local, it might not be.
        if settings.DEBUG == False and not bucket:
            raise Exception("AWS_STORAGE_BUCKET_NAME missing in production")
    run_test("Storage Configuration", test_storage)

    # 6. AI Engine API Key
    def test_ai_engine():
        if not os.environ.get('GEMINI_API_KEY'):
            raise Exception("GEMINI_API_KEY missing")
    run_test("AI Engine Configuration", test_ai_engine)

    # Dump results
    print("\n--- SMOKE TEST RESULTS ---")
    print(json.dumps(results, indent=4))
    
    return results["summary"] == "PASS"

if __name__ == "__main__":
    success = run_smoke_tests()
    sys.exit(0 if success else 1)
