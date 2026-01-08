from django.urls import path
from .views import HomeView, UploadClimateCSVFrontendView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("upload/", UploadClimateCSVFrontendView.as_view(), name="upload"),
]
