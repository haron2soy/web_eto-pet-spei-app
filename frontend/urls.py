from django.urls import path
from .views import HomeView, UploadClimateFilesView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("upload/", UploadClimateFilesView.as_view(), name="upload"),
]
