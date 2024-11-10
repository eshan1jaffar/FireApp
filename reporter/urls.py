from django.urls import path

from reporter import views

urlpatterns = [
    path('', views.report, name='report'),
    path('dashboard/', views.dashboard, name='dashboard'),
]