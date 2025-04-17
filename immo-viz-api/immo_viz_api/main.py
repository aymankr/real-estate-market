from fastapi import FastAPI
from immo_viz_api import database
from immo_viz_api.routers import (
    regions,
    departments,
    cities,
    property_ads,
    fetching_reports,
    scheduling_reports,
    analysis_reports,
)

database.VizBase.metadata.create_all(bind=database.viz_engine)
database.MonitoringBase.metadata.create_all(bind=database.monitoring_engine)

app = FastAPI()


@app.get("/")
async def root():
    return "Welcome to Immo Viz API!"


app.include_router(regions.router)
app.include_router(departments.router)
app.include_router(cities.router)
app.include_router(property_ads.router)
app.include_router(fetching_reports.router)
app.include_router(scheduling_reports.router)
app.include_router(analysis_reports.router)
