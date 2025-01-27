import logging
from fastapi import FastAPI
from atmoswing_api.app.routes import general

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s -%(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

app = FastAPI(
    title="AtmoSwing Web Forecast API",
    description="API to provide forecasts generated by AtmoSwing.",
    version="1.0.0",
)

# Include the routes
app.include_router(general.router, prefix="/general", tags=["General Data"])
#app.include_router(map.router, prefix="/map", tags=["Map Data"])
#app.include_router(graph.router, prefix="/graph", tags=["Graph Data"])
