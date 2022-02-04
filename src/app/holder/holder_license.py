from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

#from app.authentication import authentication
from app.db import mongo_setup_provider
#from app.bootstrap.key import holder_key
from app.holder import utils

# classes
from app.holder.classes import License, State

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/license", status_code=201)
async def register_license(response: Response, body: License): 
    # AUTH
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["id_token"]})
        if subscriber is not None:
            if body_dict["id_token"] != subscriber["id_token"]:            
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid ID Token")
        else:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid ID Token")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to verify ID Token")

    # PRIVATE DID
    try:
        holder_url = os.environ["HOLDER_AGENT_URL"]
        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        did = result["result"]["did"]
        #verkey = result["result"]["verkey"]

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to create wallet DID")

    # STORE REQUEST ON MONGO
    try:
        epoch_ts = str(int(time.time()))

        # MONGO WILL ADD _id TO THIS DICT
        res_to_mongo = {
            "stakeholderServices": body_dict["stakeholderServices"],
            "id_token": body_dict["id_token"],
            "licenseDID": did,
            "timestamp": epoch_ts,
            "state": State.license_request
        }
        client_res = copy.deepcopy(res_to_mongo)

        mongo_setup_provider.license_collection.insert_one(res_to_mongo)

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to store License request on Database")
    
    # SEND TO REGULATOR
    try:
        res_to_reg = {
            "stakeholderServices": body_dict["stakeholderServices"],
            "id_token": body_dict["id_token"],
            "licenseDID": did,
            "timestamp": epoch_ts,
            "service_endpoint": os.environ["TRADING_PROVIDER_AGENT_CONTROLLER_URL"],
            "agent_service_endpoint": holder_url
        }
        
        URL = os.environ["REGULATOR_AGENT_CONTROLLER_URL"]
        requests.post(URL+"/regulator/request_license_issue/"+str(res_to_mongo["_id"]), json=res_to_reg, timeout=60)

        return client_res
        
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform Stakeholder License request")       


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
    

@router.get("/license/all")
async def read_license_all():
    try:
        result_list = []
        
        subscriber = mongo_setup_provider.license_collection.find({"revoked" : { "$exists" : False}}, {"_id": 0})

        for result_object in subscriber:
            result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read Stakeholder License Credentials")

'''
@router.get("/read_stakeholder")
async def read_specific_stakeholder(response: Response, stakeholder_did: str):
    try:
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": stakeholder_did, "revoked" : { "$exists" : False}}, {"_id": 0})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Active Stakeholder Credential non existent or not found")
        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read specific Stakeholder Credential")
'''