class MedicalValidator:
    @staticmethod
    def validate_triage(data):
        """Validate medical safety of the triage response."""
        confidence = float(data.get('confidence', 0.0))
        if confidence < 0.6:
            raise ValueError("Confidence too low")
            
        recommendation = data.get('recommendation', '').lower()
        forbidden_phrases = [
            'guaranteed cure', 
            '100% accurate', 
            'you have cancer',
            'you will die'
        ]
        
        for phrase in forbidden_phrases:
            if phrase in recommendation:
                raise ValueError("Unsafe hallucinated phrase detected")
                
        # Append disclaimer
        disclaimer = "\n\nDisclaimer: AI recommendations are informational only and do not replace professional medical consultation."
        if "disclaimer:" not in data.get('recommendation', '').lower():
            data['recommendation'] = data.get('recommendation', '') + disclaimer
            
        if data.get('urgency') in ['HIGH', 'CRITICAL'] or data.get('emergency_risk'):
            if "immediate medical attention" not in data.get('recommendation', '').lower():
                data['recommendation'] += "\n\nCRITICAL: Please seek immediate medical attention or call emergency services."
                
        return data
