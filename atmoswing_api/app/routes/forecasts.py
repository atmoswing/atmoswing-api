import logging
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends
from typing_extensions import Annotated

import config

router = APIRouter()


@lru_cache
def get_settings():
    return config.Settings()
