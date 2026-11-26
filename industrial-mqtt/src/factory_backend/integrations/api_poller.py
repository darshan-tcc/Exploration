"""Architecture A: Async Factory API Poller worker.

Periodically queries the factory MES/SCADA HTTP API, validates authentication,
handles network timeouts/failures, and pushes payloads to the Common Ingestion Pipeline.
"""

import asyncio
import logging
import httpx
from factory_backend.core.config import settings
from factory_backend.pipeline.processor import pipeline

logger = logging.getLogger("factory_backend.integrations.api_poller")


class FactoryApiPoller:
    """Asynchronous background worker polling the Factory HTTP API."""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task | None = None
        self.endpoint = f"{settings.FACTORY_API_BASE_URL}/factory/machines/telemetry"
        self.headers = {
            "X-API-KEY": settings.FACTORY_API_KEY,
            "Accept": "application/json",
            "User-Agent": "FactoryBackendIntegration/1.0",
        }
        self.poll_interval = settings.FACTORY_API_POLL_INTERVAL_SECONDS

    async def start(self):
        """Start poller in background asyncio task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info(f"Factory API Poller started. Target: {self.endpoint} every {self.poll_interval}s")

    async def stop(self):
        """Stop poller cleanly."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Factory API Poller stopped.")

    async def _poll_loop(self):
        async with httpx.AsyncClient(timeout=4.0) as client:
            while self._running:
                try:
                    response = await client.get(self.endpoint, headers=self.headers)
                    if response.status_code == 200:
                        payload = response.json()
                        telemetry_items = payload.get("data", [])
                        for item in telemetry_items:
                            # Forward directly to the Common Ingestion Pipeline
                            await pipeline.process(raw_data=item, source_type="api")
                    elif response.status_code == 401:
                        logger.error("Authentication failed: Invalid X-API-KEY provided to Factory API.")
                    else:
                        logger.warning(f"Factory API responded with status {response.status_code}: {response.text}")

                except httpx.ConnectError:
                    logger.debug("Factory API server unreachable (offline or starting up). Retrying...")
                except Exception as ex:
                    logger.error(f"Error in Factory API poller: {ex}", exc_info=False)

                await asyncio.sleep(self.poll_interval)


# Global singleton instance
api_poller = FactoryApiPoller()
