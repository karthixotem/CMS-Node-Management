from django.contrib import admin
from django.urls import path
from .views import health, upload

urlpatterns = [
    path('health', health, name='health'),
    path('upload', upload, name='upload'),
]