import os
from celery import shared_task
from django.conf import settings
from climate_core.pipeline import PipelineManager


@shared_task(bind=True)
def run_climate_job(self, job_id, input_file):
    workdir = settings.CLIMATE_CACHE_DIR
    os.makedirs(workdir, exist_ok=True)

    pipeline = PipelineManager(
        job_id=job_id,
        workdir=workdir,
        pet_method="fao56"
    )

    pipeline.load_input(input_file)
    pipeline.run(scales=(3, 6, 12))

    pipeline.save_cache("results")

    return {"job_id": job_id, "status": "completed"}
    '''from apps.api.climate_utils import compute_climate

@shared_task(bind=True)
def run_climate_job(self, job_id, input_file):
    df = pd.read_csv(input_file, parse_dates=["date"])
    df = compute_climate(df, spei_scales=(3,6,12))
    
    # Save cache
    workdir = settings.CLIMATE_CACHE_DIR
    os.makedirs(workdir, exist_ok=True)
    df.to_parquet(os.path.join(workdir, f"{job_id}_processed.parquet"), index=False)

    return {"job_id": job_id, "status": "completed"}
    


    import os
import pandas as pd
from celery import shared_task
from django.conf import settings

from .climate_utils import compute_climate


@shared_task(bind=True)
def run_climate_job(self, job_id, input_file):
    """
    Background climate processing job with caching.
    """

    cache_dir = settings.CLIMATE_CACHE_DIR
    os.makedirs(cache_dir, exist_ok=True)

    cache_file = os.path.join(cache_dir, f"{job_id}_processed.parquet")

    # ✅ Use cache if exists
    if os.path.exists(cache_file):
        return {
            "job_id": job_id,
            "status": "cached",
            "cache_file": cache_file
        }

    # Load input
    df = pd.read_csv(input_file)

    # Run computation
    df = compute_climate(df, spei_scales=(3, 6, 12))

    # Save result
    df.to_parquet(cache_file, index=False)

    return {
        "job_id": job_id,
        "status": "completed",
        "cache_file": cache_file
    }
    '''