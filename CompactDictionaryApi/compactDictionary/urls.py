from django.urls import path
from . import views

urlpatterns = [
    path('api/dictionary', views.dictionary_lookup),  # Without trailing slash
    path('api/dictionary/', views.dictionary_lookup),  # With trailing slash
]