"""FastAPI Application Entry Point & Lifespan Management.

Coordinates background Ignition MQTT ingestion with FastAPI lifecycle.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from factory_backend.api.router import router
from factory_backend.core.config import settings
from factory_backend.integrations.mqtt_listener import mqtt_listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starts the Ignition MQTT background listener on startup and stops on shutdown."""
    loop = asyncio.get_running_loop()

    # Start Ignition MQTT Subscriber
    mqtt_listener.start(loop)

    yield

    # Teardown
    mqtt_listener.stop()


app = FastAPI(
    title="Factory Data Integration & Ignition MQTT Backend",
    description="Single Industrial MQTT Architecture Connected to Ignition SCADA for Mobile Applications",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for Mobile Apps (Flutter / React Native) & Web Dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


def start():
    """CLI script runner."""
    uvicorn.run(
        "factory_backend.api.main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=False,
    )


if __name__ == "__main__":
    start()
