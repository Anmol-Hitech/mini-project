
import logging
from fastapi import FastAPI
from logger.logging import setup_logging
from logger.req_res_log import log_requests
from exception.global_exception import integrity_exception_handler,global_exception_handler
setup_logging()
from routes.users import userrouter
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(userrouter,prefix="/api/users")
app.middleware("http")(log_requests)
app.exception_handler(integrity_exception_handler)
app.exception_handler(global_exception_handler)
@app.get("/")
async def root():
    logger.info("Root endpoint hit")
    return {"message": "Hello World"}