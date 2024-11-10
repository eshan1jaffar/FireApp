from django.urls import path

import chatbot.views
from chatbot import views

urlpatterns = [
    path('', chatbot.views.chatbot_view, name='chatbot'),
]