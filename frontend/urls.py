from django.urls import path
from .views import (
    HomeView,
    UploadClimateFilesView,
    ConflictsView,
    SaveStationIdsView,
    ResetHomeView,
    SaveUpdatedDataView,
    ContinueToComputationView,
    ComputationHomeView,
    ComputeEToView,
    )
    
urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("upload/", UploadClimateFilesView.as_view(), name="upload"),
    path("conflicts/", ConflictsView.as_view(), name="conflicts"),
    path("save-station-ids/", SaveStationIdsView.as_view(), name="save_station_ids"),
    path("preview/", HomeView.as_view(), name="preview"),
    path("reset/", ResetHomeView.as_view(), name="reset_home"),
    path("continue/", ContinueToComputationView.as_view(), name="continue_to_computation"),
    path("save-updated/", SaveUpdatedDataView.as_view(), name="save_updated_data"),
    path("continue/", ContinueToComputationView.as_view(), name="continue_to_computation"),
    path("computation/", ComputationHomeView.as_view(), name="computation_home"),
    path("compute-eto/", ComputeEToView.as_view(), name="compute_eto"),
    # path("compute-pet/", ComputePETView.as_view(), name="compute_pet"),
    # path("compute-spei/", ComputeSPEIView.as_view(), name="compute_spei"),
]
