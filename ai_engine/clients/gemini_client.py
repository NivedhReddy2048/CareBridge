import os
import json
import time
import logging
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential
from django.conf import settings
from ai_engine.models import AIUsageLog

logger = logging.getLogger(__name__)

class GeminiClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GeminiClient, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self):
        if not self.initialized:
            api_key = os.environ.get('GEMINI_API_KEY')
            if not api_key:
                logger.warning("Gemini API key missing. Falling back to heuristic engine.")
            else:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.initialized = True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def generate_json(self, prompt, user=None, endpoint="gemini_generate"):
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise Exception("Gemini API key missing. Forcing fallback.")
            
        start_time = time.time()
        success = False
        error_msg = ""
        result_json = None
        tokens = 0
        
        try:
            # Force JSON output by instructing model, though Gemini 1.5/2.5 supports generation_config={"response_mime_type": "application/json"}
            response = self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )
            raw_text = response.text
            result_json = json.loads(raw_text)
            
            # Estimate tokens safely if response.usage_metadata exists
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                tokens = response.usage_metadata.total_token_count
            else:
                tokens = len(prompt) // 4 + len(raw_text) // 4 # Rough heuristic
                
            success = True
            return result_json
        except json.JSONDecodeError as e:
            error_msg = f"JSON Parse Error: {str(e)} | Raw: {raw_text}"
            logger.error(error_msg)
            raise Exception("Malformed JSON from Gemini")
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Gemini API Error: {error_msg}")
            raise
        finally:
            latency = int((time.time() - start_time) * 1000)
            status = 'SUCCESS' if success else 'ERROR'
            # Fire and forget logging
            try:
                AIUsageLog.objects.create(
                    user=user,
                    endpoint=endpoint,
                    tokens_used=tokens,
                    latency_ms=latency,
                    status=status
                )
            except Exception as db_err:
                logger.error(f"Failed to save AI Log: {db_err}")

gemini_client = GeminiClient()
