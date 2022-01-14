from typing import Optional, List
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests, json, sys, os, time, threading, jwt
from enum import Enum

from bson import ObjectId
from loguru import logger

from app.db import mongo_setup_provider
#from app.bootstrap.key import holder_key

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"]
)

class Proof(BaseModel):
    stakeholderDID: str
    #agent_endpoint: str

@router.post("/send_proof", status_code=201)
async def send_proof(response: Response, body: Proof):
    # Check for stakeholder being issued
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": body_dict["stakeholderDID"]})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content="Stakeholder Credential non existent in this Agent")

        if subscriber["state"] != "Stakeholder Registered":
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Stakeholder Credential hasn't been emitted")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch requested Stakeholder Credential")
    
    # Build object for encoding
    try:
        payload = {
            "stakeholderDID": subscriber["stakeholderClaim"]["stakeholderDID"],
            "timestamp": subscriber["timestamp"],
            "credential_definition_id": subscriber["credential_definition_id"],
            "service_endpoint": os.environ["HOLDER_AGENT_URL"]
        }

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to build encoded object")

    # Encode object
    try:
        key = os.environ["KEY"]
        encoded = jwt.encode(payload, key, algorithm="HS256")
        return encoded

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform encoding")