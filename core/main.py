
import logging
from fastapi import FastAPI
from logger.logging import setup_logging
from exception.global_exception import integrity_exception_handler,global_exception_handler
setup_logging()
from routes.users import userrouter
from routes.teams import teamrouter
from routes.tasks import taskrouter
logger = logging.getLogger(__name__)

app = FastAPI()
app.include_router(userrouter,prefix="/api/users")
app.include_router(teamrouter,prefix="/api/teams")
app.include_router(taskrouter,prefix="/api/tasks")
app.exception_handler(integrity_exception_handler)
app.exception_handler(global_exception_handler)
@app.get("/")
async def root():
    logger.info("Root endpoint hit")
    return {"message": "Hello World"}