from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

from app.db import mongo_setup_provider

from app.holder import utils

# classes
from app.holder.classes import State

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/update_stakeholder_state/{request_id}", include_in_schema=False)
async def update_stakeholder_state(request_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.stakeholder_col.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.stakeholder_issue, "credential_definition_id": body["credential_definition_id"], "id_token": body["id_token"]}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"_id": ObjectId(request_id)}, {"_id": 0})

        # SEND REQUEST RECORD TO HOLDER HANDLER
        worker = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],subscriber,), daemon=True)
        worker.start()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")

@router.post("/update_stake_revoked_state/{stakeholder_did}", include_in_schema=False)
async def update_revoked_state(stakeholder_did: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.stakeholder_col.find_one_and_update({"stakeholderClaim.stakeholderDID": body["stakeholderDID"]}, {'$set': {"revoked": True}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": body["stakeholderDID"]}, {"_id": 0})
        
        # SEND REQUEST RECORD TO HOLDER HANDLER
        worker = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],subscriber,), daemon=True)
        worker.start()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")

@router.post("/decline_stakeholder/{request_id}", include_in_schema=False)
async def decline_stakeholder(request_id: str, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.stakeholder_col.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.stakeholder_decline}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"_id": ObjectId(request_id)}, {"_id": 0})

        # SEND REQUEST RECORD TO HOLDER HANDLER
        worker = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],subscriber,), daemon=True)
        worker.start()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")
   