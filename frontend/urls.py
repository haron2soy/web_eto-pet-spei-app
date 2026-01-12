from django.urls import path
from .views import (
    HomeView,
    UploadClimateFilesView,
    ConflictsView,
    SaveStationIdsView,
    )
    
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("upload/", UploadClimateFilesView.as_view(), name="upload"),
    path("conflicts/", ConflictsView.as_view(), name="conflicts"),
    path("save-station-ids/", SaveStationIdsView.as_view(), name="save_station_ids"),
    path("preview/", HomeView.as_view(), name="preview"),
    
]
