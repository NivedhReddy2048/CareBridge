import json
import re

class ResponseParser:
    @staticmethod
    def parse_triage_json(raw_text):
        """Clean markdown formatting and parse JSON strictly."""
        text = raw_text.strip()
        if text.startswith('```json'):
            text = text[7:]
        elif text.startswith('```'):
            text = text[3:]
        if text.endswith('```'):
            text = text[:-3]
            
        try:
            data = json.loads(text.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Malformed JSON: {e}")
            
        required_keys = {"urgency", "department", "emergency_risk", "recommendation", "confidence"}
        if not required_keys.issubset(data.keys()):
            raise ValueError("Missing required keys in JSON")
            
        if data.get('urgency') not in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            raise ValueError(f"Invalid urgency level: {data.get('urgency')}")
            
        return data
