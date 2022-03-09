from typing import Optional, List
from fastapi import APIRouter, Response, status, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests, json, sys, os, time, threading, jwt
from enum import Enum

from loguru import logger

from app.db import mongo_setup_provider
from app.bootstrap.key import key_pair
from app.config import log_config

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"]
)

class KeyInfo(BaseModel):
    did: str
    public_key: str
    timestamp: str


@router.get("/operator_key_pair", status_code=200)
async def get_key_pair(response: Response, shared_secret: str = Header(...)):
    # Fetch bootstrap public key
    try:
        # Check shared component secret
        if shared_secret != os.environ["KEY"]:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid validation key")
        else:
            return key_pair.operator_key_pair_create()
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to generate Operator Key Pair")


@router.post("/operator_key_pair/verify", status_code=200)
async def verify_key_pair(body: KeyInfo, shared_secret: str = Header(...)):
    # Verify issued keys
    try:
        # Check shared component secret
        if shared_secret != os.environ["KEY"]:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid validation key")
        else:
            body_dict = body.dict()
            for i in json.loads(os.environ["OTHER_IDP_CONTROLLERS"]):
                res = requests.post(i+"/authentication/controller/check", json=body_dict, timeout=60)
                if res.status_code == 200:
                    return "Operator Key Pair successfully validated"

            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Operator Key Pair is invalid for any other Id&P instance")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to validate Operator Key Pair")
        
# Confirm key pair across all other ops
@router.post("/controller/check", status_code=200, include_in_schema=False)
async def check_others_key_pair(body: KeyInfo):
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.key_pair_col.find_one({"DID": body_dict["did"], "public_key": body_dict["public_key"], "timestamp": body_dict["timestamp"]}, {"_id": 0})
        if subscriber is None:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="Operator Key Pair non existent or not found")
        else: 
            return subscriber
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to check requested Operator Key Pair")