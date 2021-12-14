from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

#from app.authentication import authentication
from app.db import mongo_setup_provider
from app.holder import utils

# classes
from app.holder.classes import Offer, ReadOfferDID, State

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/create_did", status_code=201)
async def request_credential(response: Response, body: Offer):
    # AUTH
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["token"]})
        if subscriber is not None:
            if body_dict["token"] != subscriber["id_token"]:            
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
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to create wallet DID")

    # STORE REQUEST ON MONGO
    try:
        epoch_ts = str(int(time.time()))

        # MONGO WILL ADD _id TO THIS DICT
        res_to_mongo = {
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "timestamp": epoch_ts,
            "state": State.did_offer_request,
            "handler_url": body_dict["handler_url"]
        }
        client_res = copy.deepcopy(res_to_mongo)

        mongo_setup_provider.collection.insert_one(res_to_mongo)

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to store Credential request on Database")

    # SEND TO ADMIN
    try:
        res_to_admin = {
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "timestamp": epoch_ts,
            "service_endpoint": os.environ["TRADING_PROVIDER_AGENT_CONTROLLER_URL"],
            "agent_service_endpoint": holder_url
            #"handler_url": handler_url
        }
        #print(res_to_admin)
        
        URL = os.environ["ADMIN_AGENT_CONTROLLER_URL"]
        requests.post(URL+"/issuer/request_credential_issue/"+str(res_to_mongo["_id"]), json=res_to_admin, timeout=60)
       
        # SEND TO HOLDER HANDLER
        thread = threading.Thread(target = utils.send_to_holder, args=(body_dict["handler_url"],client_res,), daemon=True)
        thread.start()

        return client_res
        
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform Credential issuing request")


@router.post("/decline_offer_did/{request_id}", include_in_schema=False)
async def decline_offer_did(request_id: str, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.did_offer_decline}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.collection.find_one({"_id": ObjectId(request_id)}, {"_id": 0})

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")
    
    # SEND REQUEST RECORD TO HOLDER HANDLER
    thread = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],subscriber,), daemon=True)
    thread.start()

@router.post("/update_did_state/{request_id}", include_in_schema=False)
async def update_did_state(request_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        #print(body)
        mongo_setup_provider.collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": State.did_offer_issue, "credential_definition_id": body["credential_definition_id"], "credential_exchange_id": body["credential_exchange_id"]}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.collection.find_one({"_id": ObjectId(request_id)})
        #print(subscriber["handler_url"])

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")
    
    # SEND REQUEST RECORD TO HOLDER HANDLER
    thread = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],body,), daemon=True)
    thread.start()
    

@router.post("/update_revoked_state/{credential_exchange_id}", include_in_schema=False)
async def update_revoked_state(credential_exchange_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        #print(body)
        mongo_setup_provider.collection.find_one_and_update({'credential_exchange_id': credential_exchange_id}, {'$set': {"revoked": True}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.collection.find_one({"credential_exchange_id": credential_exchange_id})
        
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update Mongo record")

    # SEND REQUEST RECORD TO HOLDER HANDLER
    thread = threading.Thread(target = utils.send_to_holder, args=(subscriber["handler_url"],body,), daemon=True)
    thread.start()


@router.post("/read_did_status")
async def read_credential_status(response: Response, body: ReadOfferDID):
    #if token != id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["token"]})
        if subscriber is not None:
            if body_dict["token"] != subscriber["id_token"]:            
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid ID Token")
        else:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid ID Token")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to verify ID Token")

    try:
        subscriber = mongo_setup_provider.collection.find_one({"credentialSubject.id": body_dict["did_identifier"]}, {"_id": 0})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="DID Credential non existent")
        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch requested DID")


@router.get("/read_did")
async def read_specific_credential(response: Response, did_identifier: str): #, token: str, handler_url: Optional[str] = None
    #if token != id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"
    
    #try:
    #    subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": token})
    #    if token != subscriber["id_token"]:
    #        response.status_code = status.HTTP_401_UNAUTHORIZED
    #        return "Invalid ID Token"
    #except:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"

    try:
        subscriber = mongo_setup_provider.collection.find_one({"credentialSubject.id": did_identifier, "state": State.did_offer_issue, "revoked" : {"$exists" : False}}, {"_id": 0, "state": 0, "handler_url": 0, "credential_exchange_id": 0})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Marketplace Credential not issued or non existent")
        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch specific Marketplace Credential")


@router.get("/read_did_catalog")
async def read_all_credentials(response: Response): #, token: str, handler_url: Optional[str] = None
    #if token != id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"

    #try:
    #    subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": token})
    #    if token != subscriber["id_token"]:
    #        response.status_code = status.HTTP_401_UNAUTHORIZED
    #        return "Invalid ID Token"
    #except:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"
    
    try:
        subscriber = mongo_setup_provider.collection.find({"state": State.did_offer_issue, "revoked" : { "$exists" : False}}, {"_id": 0, "state": 0, "handler_url": 0, "credential_exchange_id": 0})
        result_list = []

        for result_object in subscriber:
            #print(result_object)
            result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch Marketplace Credentials")


@router.get("/read_did/revoked")
async def read_revoked_credential():
    try:
        subscriber = mongo_setup_provider.collection.find({"revoked" : { "$exists" : True}}, {"_id": 0, "state": 0, "handler_url": 0, "credential_exchange_id": 0, "revoked": 0})
        result_list = []

        for result_object in subscriber:
            #print(result_object)
            result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch revoked Marketplace Credentials")