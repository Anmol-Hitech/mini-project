
import logging
from fastapi import FastAPI
from logger.logging import setup_logging
from exception.global_exception import integrity_exception_handler,global_exception_handler
setup_logging()
from routes.users import userrouter
from routes.teams import teamrouter
from routes.tasks import taskrouter
from routes.invite import inviterouter
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
from exception.global_exception import (
    global_exception_handler,
    integrity_exception_handler
)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_exception_handler(IntegrityError, integrity_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.include_router(userrouter,prefix="/api/users")
app.include_router(teamrouter,prefix="/api/teams")
app.include_router(taskrouter,prefix="/api/tasks")
app.include_router(inviterouter,prefix="/api/invite")

@app.get("/")
async def root():
    logger.info("Root endpoint hit")
    return {"message": "Hello World"}