# Create your views here.
from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render
from django.conf import settings
import requests

class HomeView(TemplateView):
    template_name = "frontend/home.html"


class UploadClimateCSVFrontendView(View):
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return render(request, "frontend/home.html", {
                "error": "Please select a CSV file."
            })

        api_url = request.build_absolute_uri("/api/upload-climate-csv/")

        response = requests.post(
            api_url,
            files={"file": file}
        )

        if response.status_code != 200:
            return render(request, "frontend/home.html", {
                "error": "Upload failed",
                "details": response.text
            })

        return render(request, "frontend/home.html", {
            "success": "Climate data uploaded successfully.",
            "result": response.json()
        })
