from django.urls import path
from .views import dictionary_lookup

urlpatterns = [
    path("dictionary/", dictionary_lookup),
]
