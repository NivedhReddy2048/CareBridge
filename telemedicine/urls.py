from django.urls import path
from . import apis

app_name = 'telemedicine'

urlpatterns = [
    path('sessions/', apis.create_consultation, name='create_consultation'),
    path('sessions/<uuid:pk>/join/', apis.join_consultation, name='join_consultation'),
    path('sessions/<uuid:pk>/end/', apis.end_consultation, name='end_consultation'),
    path('sessions/<uuid:pk>/chat/', apis.fetch_chat_history, name='fetch_chat_history'),
]
