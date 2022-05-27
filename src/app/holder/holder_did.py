from fastapi import APIRouter, Response, status, Query, Header
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

#from app.authentication import authentication
from app.db import mongo_setup_provider
from app.holder import utils

# classes
from app.holder.classes import Offer, ReadOfferDID, State, Type 

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

@router.post("/create_did", status_code=201)
async def request_credential(response: Response, body: Offer):
    # AUTH
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["token"]}, {"_id": 0})
        if subscriber is not None:
            if body_dict["token"] != subscriber["id_token"]:            
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid ID Token")
            
            elif "revoked" in subscriber:
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Revoked Stakeholder is unable to request new DIDs")

            # Compare proposed offer assets with stakeholder approved assets
            #if len(list(set(body_dict["assets"]) ^ set(subscriber["stakeholderClaim"]["stakeholderRoles"][0]["assets"]))) > 0:
            #    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="ID Token of Stakeholder unauthorized to request offer for specified assets")
            #set_with_all_assets = set()
            #for object_with_assets in subscriber["stakeholderClaim"]["stakeholderRoles"]:
            #    set_with_assets_from_object = set(body_dict["assets"]).intersection(object_with_assets["assets"])
            #    set_with_all_assets.update(set_with_assets_from_object)
            
            #if len(list(set(body_dict["assets"]) ^ set_with_all_assets)) > 0:
            #    return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="ID Token of Stakeholder unauthorized to request offer for specified assets")
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
                "id": did
                #"assets": body_dict["assets"],
                #"claims": body_dict["claims"]
            },
            "timestamp": epoch_ts,
            "state": State.did_offer_issue, #State.did_offer_request
            "handler_url": body_dict["handler_url"]
        }
        client_res = copy.deepcopy(res_to_mongo)

        mongo_setup_provider.collection.insert_one(res_to_mongo)

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to store DID request on Database")

    # SEND TO HOLDER HANDLER
    try:
        worker = threading.Thread(target = utils.send_to_holder, args=(body_dict["handler_url"],client_res,), daemon=True)
        worker.start()

        return client_res
        
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform DID issuing request")


@router.get("/did/type", status_code=200)
async def query_did_by_type(type: set[Type] = Query(...)):
    try:
        result_list = []
        for value in type:
            subscriber = mongo_setup_provider.collection.find({"type": value}, {"_id": 0, "handler_url": 0})

            for result_object in subscriber:
                result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch DID Credentials on Database")


@router.get("/did")
async def read_specific_did(did: str = Header(...), type: str = Header(...)):
    try:
        subscriber = mongo_setup_provider.collection.find_one({"credentialSubject.id": did, "type": type}, {"_id": 0})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="DID Credential not issued or non existent")
        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch specific DID Credential")
