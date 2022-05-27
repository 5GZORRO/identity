from fastapi import APIRouter, Response, status, Query
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

#from app.authentication import authentication
from app.db import mongo_setup_provider
#from app.bootstrap.key import holder_key
from app.holder import utils

# classes
from app.holder.classes import License, State, StateQuery

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/license", status_code=201)
async def register_license(response: Response, body: License): 
    # AUTH
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["id_token"]}, {"_id": 0})
        if subscriber is not None:
            if body_dict["id_token"] != subscriber["id_token"]:            
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid ID Token")
            
            elif "revoked" in subscriber:
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Revoked Stakeholder is unable to request new Licenses")

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
            "stakeholderDID": subscriber["stakeholderClaim"]["stakeholderDID"], 
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
            "stakeholderDID": subscriber["stakeholderClaim"]["stakeholderDID"], 
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


@router.get("/license/did")
async def read_specific_license_by_did(response: Response, license_did: str):
    try:
        subscriber = mongo_setup_provider.license_collection.find_one({"licenseDID": license_did}, {"_id": 0})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Stakeholder License Credential non existent or not found")
        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read specific Stakeholder License Credential")


@router.get("/license", status_code=200)
async def query_license_creds(state: set[StateQuery] = Query(...)):
    try:
        result_list = []
        for status in state:
            if status == StateQuery.approved:
                subscriber = mongo_setup_provider.license_collection.find({"state": State.license_issue, "revoked" : {"$exists" : False}}, {"_id": 0})
            elif status == StateQuery.pending:
                subscriber = mongo_setup_provider.license_collection.find({"state": State.license_request, "revoked" : {"$exists" : False}}, {"_id": 0})
            elif status == StateQuery.rejected:
                subscriber = mongo_setup_provider.license_collection.find({"state": State.license_decline, "revoked" : {"$exists" : False}}, {"_id": 0})
            else:
                subscriber = mongo_setup_provider.license_collection.find({"revoked" : {"$exists" : True}}, {"_id": 0})

            for result_object in subscriber:
                result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch Stakeholder License Credentials on Database")
