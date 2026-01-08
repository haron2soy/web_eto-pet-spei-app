import os
import uuid
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import CSVUploadSerializer
from .tasks import run_climate_job

class UploadClimateCSVView(APIView):
    """
    Upload a CSV and trigger climate job (ETo → PET → SPEI).
    """

    def post(self, request, format=None):
        serializer = CSVUploadSerializer(data=request.data)
        if serializer.is_valid():
            csv_file = serializer.validated_data['file']

            # Generate a unique job ID
            job_id = str(uuid.uuid4())

            # Save uploaded file
            upload_dir = os.path.join(settings.MEDIA_ROOT, "uploads")
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{job_id}.csv")

            with open(file_path, 'wb+') as f:
                for chunk in csv_file.chunks():
                    f.write(chunk)

            # Enqueue Celery task
            task = run_climate_job.delay(job_id, file_path)

            return Response({
                "message": "Job submitted successfully",
                "job_id": job_id,
                "task_id": task.id
            }, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
def compute_climate(df, spei_scales=(3,6,12)):
    if "ETo" not in df.columns:
        FAO56ETo(df).compute()

    if "PET" not in df.columns:
        PETCalculator(method="fao56").compute(df)

    if "D" not in df.columns:
        WaterBalance(df).compute()

    for k in spei_scales:
        spei_col = f"SPEI_{k}"
        if spei_col not in df.columns:
            SPEICalculator(df).compute(k=k)

    return df
