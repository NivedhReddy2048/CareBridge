import os
import django

if not os.getenv("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE",
        "config.settings.production"
    )
django.setup()

print("DEBUG asgi.py: DJANGO_SETTINGS_MODULE =", os.getenv("DJANGO_SETTINGS_MODULE"))
print("DEBUG asgi.py: raw ALLOWED_HOSTS env =", os.getenv("ALLOWED_HOSTS"))

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from notifications.middleware import JWTAuthMiddleware
import notifications.routing
import telemedicine.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": JWTAuthMiddleware(
        AuthMiddlewareStack(
            URLRouter(
                notifications.routing.websocket_urlpatterns +
                telemedicine.routing.websocket_urlpatterns
            )
        )
    ),
})
