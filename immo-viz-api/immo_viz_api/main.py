from fastapi import FastAPI
from immo_viz_api import database
from immo_viz_api.routers import regions, departments, cities

database.VizBase.metadata.create_all(bind=database.viz_engine)
database.MonitoringBase.metadata.create_all(bind=database.monitoring_engine)

app = FastAPI()

@app.get("/")
async def root():
    return "Welcome to Immo Viz API!"

app.include_router(regions.router)
app.include_router(departments.router)
app.include_router(cities.router)