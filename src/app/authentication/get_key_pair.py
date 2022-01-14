from typing import Optional, List
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests, json, sys, os, time, threading, jwt
from enum import Enum

from loguru import logger

from app.bootstrap.key import key_pair
from app.config import log_config

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"]
)

@router.get("/operator_key_pair", status_code=200)
async def get_key_pair(response: Response, shared_secret: str):
    # Fetch bootstrap public key
    try:
        # Check shared component secret
        if shared_secret != os.environ["KEY"]:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid component secret")
        else:
            key_pair_res = {
                "public_key": key_pair.pub_key,
                "private_key": key_pair.priv_key
            }
            return key_pair_res
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch public agent key")
