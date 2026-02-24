
import logging
import time
from fastapi import Request

logger = logging.getLogger("request")

async def log_requests(request: Request, call_next):
    start_time = time.time()

    logger.info(f"Incoming request: {request.method} {request.url}")

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception("Unhandled exception occurred")
        raise

    process_time = (time.time() - start_time) * 1000

    logger.info(
        f"Completed: {request.method} {request.url} "
        f"Status: {response.status_code} "
        f"Time: {process_time:.2f}ms"
    )

    return response