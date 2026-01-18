import os

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from django.urls import path
from events.urls import websocket_urlpatterns
from events.consumer import VideoProgressConsumer

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kafka_django.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
        ),
})
