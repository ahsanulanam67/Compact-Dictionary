from django.urls import path, include

urlpatterns = [
    path("api/", include("compactDictionary.urls")),
]
