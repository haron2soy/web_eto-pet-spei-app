from django.urls import path
from .views import UploadClimateCSVView

urlpatterns = [
    path('upload-climate-csv/', UploadClimateCSVView.as_view(), name='upload-climate-csv'),
]
