'''# Create your views here.
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
        })'''
from django.views import View
from django.shortcuts import render
from django.contrib import messages
import pandas as pd

from climate_core.utils.upload_utils import (
    normalize_columns,
    apply_column_mappings,
    validate_minimum_schema,
    get_preview_dataframe,
    merge_climate_dataframes,
    extract_stationid_map,
    attach_stationid
    
)


class HomeView(View):
    template_name = "frontend/home.html"

    def get(self, request):
        return render(request, self.template_name)


class UploadClimateFilesView(View):
    template_name = "frontend/home.html"

    def post(self, request):
        files = request.FILES.getlist("files")

        if not files:
            messages.error(request, "Please select at least one file.")
            return render(request, self.template_name)

        dfs = []
        all_undetected = set()
        try:
            for f in files:
                if f.name.endswith(".csv"):
                    df = pd.read_csv(f)
                elif f.name.endswith((".xls", ".xlsx")):
                    df = pd.read_excel(f)
                else:
                    raise ValueError(f"Unsupported file type: {f.name}")

                df = normalize_columns(df)
                df = apply_column_mappings(df)
                validate_minimum_schema(df)
                
                all_undetected.update(df.attrs.get("undetected_columns", []))
                dfs.append(df)

            #combined_df = pd.concat(dataframes, ignore_index=True)
            station_map = extract_stationid_map(dfs)
            merged_df = merge_climate_dataframes(dfs)
            merged_df = attach_stationid(merged_df, station_map)
            merged_df.attrs["undetected_columns"] = sorted(all_undetected)

        except Exception as e:
            messages.error(request, str(e))
            return render(request, self.template_name)
       
        preview_df = get_preview_dataframe(merged_df).head(500)

        request.session["climate_preview"] = preview_df.to_dict("records")
        request.session["climate_columns"] = list(preview_df.columns)
        request.session["undetected_columns"] = merged_df.attrs.get(
           "undetected_columns", []
        )

        messages.success(
            request,
            f"{len(files)} file(s) uploaded successfully. Preview below."
        )

        return render(
            request,
            self.template_name,
            {
                "preview_rows": request.session["climate_preview"],
                "preview_cols": request.session["climate_columns"],
            }
        )
