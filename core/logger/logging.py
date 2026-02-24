import logging
import logging.config
import os
from logging.handlers import RotatingFileHandler

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(filename)s:%(lineno)d | %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": f"{LOG_DIR}/app.log",
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "level": "DEBUG",
        },
    },
    "loggers": {
        "uvicorn.access": {  # FastAPI request logs
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "uvicorn.error": {  # FastAPI error logs
            "handlers": ["console", "file"],
            "level": "ERROR",
            "propagate": False,
        },
        "sqlalchemy.engine": {  # SQLAlchemy query logs
            "handlers": ["file"],
            "level": "INFO",
            "propagate": False,
        },
    }
}

def setup_logging():
    logging.config.dictConfig(LOGGING_CONFIG)