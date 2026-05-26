from rest_framework.throttling import UserRateThrottle, AnonRateThrottle

class AIHeavyThrottle(UserRateThrottle):
    scope = 'ai_heavy'

class AIChatThrottle(UserRateThrottle):
    scope = 'ai_chat'

class AIAnonThrottle(AnonRateThrottle):
    scope = 'ai_anon'
