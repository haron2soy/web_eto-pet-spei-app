# Create your views here.
from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render
from django.contrib import messages
import pandas as pd
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from climate_core.utils.upload_utils import (
    CANONICAL_COLUMNS,
    normalize_columns,
    apply_column_mappings,
    validate_minimum_schema,
    get_preview_dataframe,
    merge_climate_dataframes,
    extract_stationid_map,
    attach_stationid,
    detect_duplicate_variables,
    resolve_duplicates_by_data_count,
    #validate_station_coverage
       
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
            duplicates = detect_duplicate_variables(dfs, CANONICAL_COLUMNS)
            selected_columns, conflicts_metadata = resolve_duplicates_by_data_count(dfs, duplicates)
            
            station_map, missing_stations= extract_stationid_map(dfs)
            #validate_station_coverage(dfs, station_map)
            merged_df = merge_climate_dataframes(dfs, selected_columns)
            merged_df = attach_stationid(merged_df, station_map)
            merged_df.attrs["missing_stationids"] = missing_stations
            merged_df.attrs["undetected_columns"] = sorted(all_undetected)
        
            preview_df = get_preview_dataframe(merged_df).head(500)
            context = {
                "preview_rows": preview_df.to_dict("records"),
                "preview_cols": list(preview_df.columns),
                "conflicts_metadata": conflicts_metadata
                }
            request.session["climate_preview"] = preview_df.to_dict("records")
            request.session["climate_columns"] = list(preview_df.columns)
            request.session["undetected_columns"] = merged_df.attrs.get(
            "undetected_columns", []
            )
            request.session["station_map"] = station_map
            request.session["missing_stationids"] = missing_stations
        except Exception as e:
                    messages.error(request, str(e))
                    return render(request, self.template_name)

        messages.success(
            request,
            f"{len(files)} file(s) uploaded successfully. Preview below."
        )
        
        if missing_stations:
            '''return render(
                request,
                "frontend/missing_station_ids.html",
                {
                    "missing_stationids": missing_stations
                }
            )'''
            return render(
                request,
                self.template_name,
                {
                    "preview_rows": request.session["climate_preview"],
                    "preview_cols": request.session["climate_columns"],
                    "missing_stationids": missing_stations, 
                }
            )



class ConflictsView(TemplateView):
    template_name = "frontend/conflicts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass conflicts from session (set when files uploaded)
        context["conflicts_metadata"] = self.request.session.get("conflicts_metadata", [])
        return context
'''class SaveStationIdsView(View):
    def post(self, request):
        station_map = request.session.get("station_map", {})

        for key in request.POST:
            if key.startswith("stationname_"):
                idx = key.split("_")[1]
                name = request.POST[key]
                sid = request.POST.get(f"stationid_{idx}")

                station_map[name] = sid

        request.session["station_map"] = station_map
        messages.success(request, "Station IDs saved successfully.")

        return redirect("home")'''
class SaveStationIdsView(View):
    def post(self, request):
        station_map = request.session.get("station_map", {})

        for key, value in request.POST.items():
            if key.startswith("stationname_"):
                idx = key.split("_")[-1]
                station = value.strip().lower()
                sid = request.POST.get(f"stationid_{idx}")

                if sid:
                    station_map[station] = sid.strip()

        request.session["station_map"] = station_map
        request.session["missing_stationids"] = []

        messages.success(request, "Station IDs saved successfully.")
        return redirect("home")

'''class SaveStationIdsView(View):
    def post(self, request):
        station_map = request.session.get("station_map", {})

        for key, value in request.POST.items():
            if key.startswith("stationname_"):
                idx = key.split("_")[-1]
                station = value.strip().lower()
                sid = request.POST.get(f"stationid_{idx}")

                if sid:
                    station_map[station] = sid.strip()

        request.session["station_map"] = station_map
        request.session["missing_stationids"] = []

        messages.success(request, "Station IDs saved successfully.")

        return redirect("preview")'''
