import os
import django

# Set the default settings module for Django.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'connectai.settings')

# Initialize Django
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
import base.routing  # Import your routing here

# Define the application
application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Handles HTTP requests
    "websocket": AuthMiddlewareStack(
        URLRouter(
            base.routing.websocket_urlpatterns  # Define websocket routes
        )
    ),
})
