import os
from functools import lru_cache

from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer


@lru_cache(maxsize=None)
def get_logger():

    logger = Logger()
    if "LOGGING" in os.environ:
        logger.setLevel(os.environ["LOGGING"])
    return logger


@lru_cache(maxsize=None)
def get_tracer():
    return Tracer()
