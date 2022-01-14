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
from app.holder.classes import Stakeholder, State

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/register_stakeholder", status_code=201)
async def register_stakeholder(response: Response, body: Stakeholder): #key: str,
    # AUTH
    try:
        body_dict = body.dict()
        if body_dict["key"] != os.environ["KEY"]: #holder_key.verkey
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid Verification Key")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to authenticate provided key")

    # CHECK FOR ACTIVE STAKE CRED
    #try:
    #    subscriber = mongo_setup_provider.stakeholder_col.find_one({"revoked" : { "$exists" : False} }, {"_id": 0, "handler_url": 0})
    #    if subscriber != None:
    #        response.status_code = status.HTTP_409_CONFLICT
    #        return "A Stakeholder Credential has already been requested/issued"
    #except:
    #    return "Unable to check for active stakeholder credential"

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
            "stakeholderClaim": {
                "governanceBoardDID": body_dict["governanceBoardDID"],
                "stakeholderServices": body_dict["stakeholderServices"],
                #"stakeholderRoles": {
                #    "role": body_dict["stakeholderRoles"]["role"],
                #    "assets": body_dict["stakeholderRoles"]["assets"]
                #},
                "stakeholderRoles": body_dict["stakeholderRoles"],
                "stakeholderProfile": {
                    "name": body_dict["stakeholderProfile"]["name"],
                    "ledgerIdentity": body_dict["stakeholderProfile"]["ledgerIdentity"],
                    "address": body_dict["stakeholderProfile"]["address"],
                    "notificationMethod": body_dict["stakeholderProfile"]["notificationMethod"]
                },
                "stakeholderDID": did
                #"did": did,
                #"verkey": verkey
            },
            "timestamp": epoch_ts,
            "state": State.stakeholder_request,
            "handler_url": body_dict["handler_url"]
        }
        client_res = copy.deepcopy(res_to_mongo)

        mongo_setup_provider.stakeholder_col.insert_one(res_to_mongo)

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to store Credential request on Database")
    
    # SEND TO ADMIN
    try:
        res_to_admin = {
            "stakeholderClaim": {
                "governanceBoardDID": body_dict["governanceBoardDID"],
                "stakeholderServices": body_dict["stakeholderServices"],
                #"stakeholderRoles": {
                #    "role": body_dict["stakeholderRoles"]["role"],
                #    "assets": body_dict["stakeholderRoles"]["assets"]
                #},
                "stakeholderRoles": body_dict["stakeholderRoles"],
                "stakeholderProfile": {
                    "name": body_dict["stakeholderProfile"]["name"],
                    "ledgerIdentity": body_dict["stakeholderProfile"]["ledgerIdentity"],
                    "address": body_dict["stakeholderProfile"]["address"],
                    "notificationMethod": body_dict["stakeholderProfile"]["notificationMethod"]
                },
                "stakeholderDID": did
                #"did": did,
                #"verkey": verkey
            },
            "timestamp": epoch_ts,
            "service_endpoint": os.environ["TRADING_PROVIDER_AGENT_CONTROLLER_URL"],
            "agent_service_endpoint": holder_url
        }
        #print(res_to_admin)
        #print("\n")
        
        URL = os.environ["ADMIN_AGENT_CONTROLLER_URL"]
        requests.post(URL+"/issuer/request_stakeholder_issue/"+str(res_to_mongo["_id"]), json=res_to_admin, timeout=60)
       

        # SEND TO HOLDER HANDLER
        thread = threading.Thread(target = utils.send_to_holder, args=(body_dict["handler_url"],client_res,), daemon=True)
        thread.start()

        return client_res
        
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform Stakeholder registration request")       


@router.post("/update_stakeholder_state/{request_id}", include_in_schema=False)
async def update_stakeholder_state(request_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.stakeholder_col.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.stakeholder_issue, "credential_definition_id": body["credential_definition_id"], "id_token": body["id_token"]}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"_id": ObjectId(request_id)})

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")
    
    # SEND REQUEST RECORD TO HOLDER HANDLER
    thread = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],body,), daemon=True)
    thread.start()

@router.post("/decline_stakeholder/{request_id}", include_in_schema=False)
async def decline_stakeholder(request_id: str, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.stakeholder_col.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.stakeholder_decline}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"_id": ObjectId(request_id)}, {"_id": 0})

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")
    
    # SEND REQUEST RECORD TO HOLDER HANDLER
    thread = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],subscriber,), daemon=True)
    thread.start()
   

@router.get("/read_stakeholder_status")
async def read_stakeholder_status(response: Response): # key: str, stakeholder_did: str, body: ReadStakeDID
    #if key != holder_key.verkey:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid Verification Key"
    try:
        #body_dict = body.dict()
        #subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": body_dict["stakeholderDID"]}, {"_id": 0, "handler_url": 0})
        
        result_list = []
        
        subscriber = mongo_setup_provider.stakeholder_col.find({"revoked" : { "$exists" : False} }, {"_id": 0, "handler_url": 0})
        #subscriber = mongo_setup_provider.stakeholder_col.find_one({"revoked" : { "$exists" : False} }, {"_id": 0, "handler_url": 0})
        #if subscriber == None:
        #    response.status_code = status.HTTP_404_NOT_FOUND
        #    return "Active Stakeholder Credential non existent or not found"
        #else: 
        #    return subscriber

        for result_object in subscriber:
            result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read Stakeholder Credentials")


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