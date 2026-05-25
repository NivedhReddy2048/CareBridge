import jwt
from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs
from accounts.models import CustomUser

@database_sync_to_async
def get_user(user_id):
    try:
        return CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode('utf-8')
        query_params = parse_qs(query_string)
        token = query_params.get('token', [None])[0]

        if token:
            try:
                # Decode the JWT token
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
                user_id = payload.get('user_id')
                scope['user'] = await get_user(user_id)
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                scope['user'] = AnonymousUser()
        else:
            # Fallback to standard Django session if possible (useful for templates using standard login)
            if 'user' not in scope or scope['user'].is_anonymous:
                scope['user'] = AnonymousUser()

        return await super().__call__(scope, receive, send)
