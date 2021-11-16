from typing import Optional, List
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests, json, sys, os, time, threading, jwt
from enum import Enum

from loguru import logger

from app.bootstrap.key import public_key
from app.config import log_config

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"]
)

@router.get("/public_key", status_code=200)
async def get_public_key(response: Response):
    # Fetch bootstrap public key
    try:
        return public_key.public_verkey

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch public agent key")
