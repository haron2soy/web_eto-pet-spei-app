# Create your views here.
from django.views.generic import TemplateView
from django.views import View
from django.shortcuts import render
from django.contrib import messages
import pandas as pd
from django.shortcuts import redirect
from django.views.decorators.http import require_POST
from django.http import HttpResponse

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
        if not request.session.get("has_active_preview"):
            # Fresh visit → clean state
            for key in [
                "climate_preview",
                "climate_columns",
                "missing_stationids",
                "undetected_columns",
                "station_map",
            ]:
                request.session.pop(key, None)

        context = {
            "preview_rows": request.session.get("climate_preview"),
            "preview_cols": request.session.get("climate_columns"),
            "missing_stationids": request.session.get("missing_stationids"),
            "undetected_columns": request.session.get("undetected_columns"),
        }
        return render(request, self.template_name, context)

  
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
            request.session["merged_df"] = merged_df.to_json(orient="records")
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
            request.session["has_active_preview"] = True

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
    
            return render(
                request,
                self.template_name,
                    {
                    "preview_rows": preview_df.to_dict("records"),
                    "preview_cols": list(preview_df.columns),
                    "missing_stationids": missing_stations,
                    "undetected_columns": merged_df.attrs.get("undetected_columns", []),
                }
              
                )


class ResetHomeView(View):
    def get(self, request):
        for key in [
            "climate_preview",
            "climate_columns",
            "missing_stationids",
            "undetected_columns",
            "station_map",
        ]:
            request.session.pop(key, None)

        request.session.pop("has_active_preview", None)
        return redirect("home")


class ConflictsView(TemplateView):
    template_name = "frontend/conflicts.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Pass conflicts from session (set when files uploaded)
        context["conflicts_metadata"] = self.request.session.get("conflicts_metadata", [])
        return context

class SaveStationIdsView(View):
    def post(self, request):
        station_map = request.session.get("station_map", {})
        preview_rows = request.session.get("climate_preview")

        if not preview_rows:
            messages.error(request, "Session expired. Please re-upload files.")
            return redirect("reset_home")

        # 1. Update station_map from form
        for key, value in request.POST.items():
            if key.startswith("stationname_"):
                idx = key.split("_")[-1]
                station = value.strip().lower()
                sid = request.POST.get(f"stationid_{idx}")

                if sid:
                    station_map[station] = sid.strip()

        request.session["station_map"] = station_map
        request.session["missing_stationids"] = []

        # 2. Apply station IDs directly to preview rows
        for row in preview_rows:
            station = row.get("station_name")
            if station:
                row["stationid"] = station_map.get(
                    station.strip().lower()
                )

        # 3. Persist updated preview
        request.session["climate_preview"] = preview_rows

        messages.success(
            request,
            "Station IDs saved and applied successfully."
        )
        request.session["has_active_preview"] = True
        return redirect("home")



def normalize_station_name(value):
    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
    )

class ContinueToComputationView(View):
    def post(self, request):
        if not request.session.get("climate_preview"):
            messages.warning(request, "No active preview.")
            return redirect("home")

        if request.session.get("missing_stationids"):
            messages.warning(
                request,
                "Please resolve missing station IDs before continuing."
            )
            return redirect("home")

        # Lock preview state
        request.session["preview_finalized"] = True

        return redirect("computation_home")  # ETo / PET / SPEI landing page
   

class SaveUpdatedDataView(View):

    def post(self, request):
        merged_json = request.session.get("merged_df")
        station_map = request.session.get("station_map", {})

        if not merged_json:
            messages.error(request, "Session expired. Please re-upload files.")
            return redirect("home")

        df = pd.read_json(merged_json, orient="records")

        # Normalize station names
        df["station_name_norm"] = (
            df["station_name"]
            .astype(str)
            .str.strip()
            .str.lower()
        )

        df["stationid"] = df["station_name_norm"].map(station_map)

        df.drop(columns=["station_name_norm"], inplace=True)

        response = HttpResponse(
            content_type="text/csv"
        )
        response["Content-Disposition"] = (
            'attachment; filename="climate_data_with_stationids.csv"'
        )

        df.to_csv(response, index=False)

        return response
class ComputationHomeView(View):
    template_name = "frontend/computation_home.html"

    def get(self, request):
        # Ensure there is a finalized preview
        if not request.session.get("climate_preview"):
            messages.error(request, "No uploaded data found. Please upload files first.")
            return redirect("home")
        return render(request, self.template_name)
from climate_core.eto.fao56 import FAO56ETo

class ComputeEToView(View):
    def post(self, request):
        merged_json = request.session.get("merged_df")

        if not merged_json:
            messages.error(request, "No uploaded data found.")
            return redirect("home")

        df = pd.read_json(merged_json, orient="records")

        # Apply station IDs
        station_map = request.session.get("station_map", {})
        df["station_name_norm"] = df["station_name"].astype(str).str.strip().str.lower()
        df["stationid"] = df["station_name_norm"].map(station_map)
        df.drop(columns=["station_name_norm"], inplace=True)

        # Compute ETo
        eto_calculator = FAO56ETo(df)
        df["ETo"] = eto_calculator.compute()

        # Save results in session for next steps
        request.session["computed_eto"] = df.to_json(orient="records")

        messages.success(request, "ETo computation completed successfully.")
        return redirect("computation_results")  # new template to show ETo results
