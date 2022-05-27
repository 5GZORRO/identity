from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

from app.db import mongo_setup_provider

# classes
from app.holder.classes import State

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/update_license_state/{request_id}", include_in_schema=False)
async def update_license_state(request_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.license_collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.license_issue, "credential_definition_id": body["credential_definition_id"], "credential_exchange_id": body["credential_exchange_id"]}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.license_collection.find_one({"_id": ObjectId(request_id)}, {"_id": 0})

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")

@router.post("/decline_license/{request_id}", include_in_schema=False)
async def decline_license(request_id: str, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.license_collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.license_decline}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.license_collection.find_one({"_id": ObjectId(request_id)}, {"_id": 0})

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")