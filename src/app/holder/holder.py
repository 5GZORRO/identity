from typing import Optional
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import requests, json, sys, os

from bson import ObjectId

from app.authentication import authentication
from app.db import mongo_setup_provider

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

class Offer(BaseModel):
    type: str
    claims: dict

header = {
    'Content-Type': 'application/json'        
}

####################### Verifiable Credentials Management #######################
@router.post("/create_did", status_code=201)
async def request_credential(response: Response, token: str, body: Offer, handler_url: str):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    # PRIVATE DID
    try:
        holder_url = os.environ["HOLDER_AGENT_URL"]
        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        did = result["result"]["did"]
    except:
        return "Unable to create wallet DID."

    # STORE REQUEST ON MONGO
    try:
        body_dict = body.dict()

        # MONGO WILL ADD _id TO THIS DICT
        res_to_mongo = {
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "state": "Credential Requested",
            "handler_url": handler_url
        }
        mongo_setup_provider.collection.insert_one(res_to_mongo)

    except:
        return "Unable to store Credential request on Database."

    # SEND TO ADMIN
    try:
        res_to_admin = {
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "service_endpoint": os.environ["TRADING_PROVIDER_AGENT_CONTROLLER_URL"]
            #"handler_url": handler_url
        }
        #print(res_to_admin)
        #print("\n")
        
        URL = os.environ["ADMIN_AGENT_CONTROLLER_URL"]
        requests.post(URL+"/issuer/request_credential_issue/"+str(res_to_mongo["_id"]), json=res_to_admin, timeout=60)
        #body = resp.json()
        #print(body)
        #if "detail" in body:
        #    return "Unable to access Credential issuing request endpoint"

        client_res = {
            "_id": str(res_to_mongo["_id"]),
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "state": "Credential Requested",
            "handler_url": handler_url
        }
        
        # SEND TO HOLDER HANDLER
        try:
            holder_handler_resp = requests.post(handler_url, headers=header, json=client_res, timeout=30)
            holder_body = resp.json()
        except:
            return "Unable to send request info to Holder's Handler"

        return client_res
        
    except:
        return "Unable to perform Credential issuing request."

@router.post("/update_did_state/{request_id}", include_in_schema=False)
async def update_did_state(request_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        #print(body)
        mongo_setup_provider.collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": "Credential Issued", "credential_definition_id": body["credential_definition_id"]}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.collection.find_one({"_id": ObjectId(request_id)})
        #print(subscriber["handler_url"])
    except:
        return "Unable to update Mongo record"
    
    # SEND REQUEST RECORD TO HOLDER HANDLER
    try:
        requests.post(subscriber["handler_url"], headers=header, json=body, timeout=30)
    except:
        return "Unable to send info to Holder Handler"

@router.get("/read_did_status")
async def read_credential_status(response: Response, token: str, request_id: str):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        subscriber = mongo_setup_provider.collection.find_one({"_id": ObjectId(request_id)})
        res = {
            "type": subscriber["type"],
            "credentialSubject": {
                "id": subscriber["credentialSubject"]["id"],
                "claims": subscriber["credentialSubject"]["claims"]
            },
            "state": subscriber["state"],
            "handler_url": subscriber["handler_url"]
        }
        return res

    except:
        return "Unable to fetch requested DID"

@router.get("/read_did")
async def read_credential(response: Response, token: str, cred_id: str):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        URL = os.environ["HOLDER_AGENT_URL"]
        resp = requests.get(URL+"/credential/"+cred_id, timeout=30)
        body = resp.json()
        return body

    except:
        return "Unable to fetch specific Marketplace Credential"

@router.get("/read_did/all")
async def read_all_credentials(response: Response, token: str, handler_url: Optional[str] = None):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        URL = os.environ["HOLDER_AGENT_URL"]
        resp = requests.get(URL+"/credentials", timeout=30)
        body = resp.json()
        if handler_url != None:
            try:
                requests.post(handler_url, headers=header, json=body, timeout=30)
            except:
                body.update({"handler_info": "Unable to send data to Handler URL"})
        return body

    except:
        return "Unable to fetch Marketplace Credentials"

@router.put("/revoke")
async def revoke_credential():
    return "Awaiting Implementation"

@router.get("/read/revoke")
async def read_revoked_credential():
    return "Awaiting Implementation"

@router.delete("/remove")
async def remove_credential():
    return "Awaiting Implementation"