from typing import Optional
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import requests, json, os

from bson import ObjectId

from app.db import mongo_setup_admin
from app.bootstrap import setup_issuer, setup_vc_schema
from app.authentication import authentication

router = APIRouter(
    prefix="/issuer",
    tags=["issuer"]
)

class ReqCred(BaseModel):
    type: str
    credentialSubject: dict
    service_endpoint: str
    #handler_url: str

class IssueCred(BaseModel):
    holder_request_id: str
    type: str
    credentialSubject: dict
    service_endpoint: str
    #handler_url: str

header = {
    'Content-Type': 'application/json'        
}

####################### Verifiable Credentials Management #######################
@router.post("/request_credential_issue/{request_id}") #, include_in_schema=False 
async def request_credential_issue(request_id: str, response: Response, body: ReqCred):
    # CHECK FOR REQUEST RECORD
    test = mongo_setup_admin.collection.find_one({"holder_request_id": request_id})
    if test != None:
        if test["state"] == "Credential Issued":
            return "Credential Request was already issued"

    # SUBMIT REQUEST TO ADMIN HANDLER
    try:
        body_dict = body.dict()

        res_to_insert_db = {
            "holder_request_id": request_id,
            "type": body_dict["type"],
            "credentialSubject": {
                "id": body_dict["credentialSubject"]["id"],
                "claims": body_dict["credentialSubject"]["claims"]
            },
            "state": "Credential Requested"
            #"handler_url": body_dict["handler_url"]
            #"service_endpoint": body_dict["service_endpoint"]
        }

        mongo_setup_admin.collection.insert_one(res_to_insert_db)

        res_to_admin_handler = {
            "_id": str(res_to_insert_db["_id"]),
            "holder_request_id": request_id,
            "type": body_dict["type"],
            "credentialSubject": {
                "id": body_dict["credentialSubject"]["id"],
                "claims": body_dict["credentialSubject"]["claims"]
            },
            "service_endpoint": body_dict["service_endpoint"]
        }
        #print(res_to_admin_handler)
        
        admin_handler_url = os.environ["HANDLER_ADMIN_URL"]
        requests.post(admin_handler_url+"/receive", headers=header, json=res_to_admin_handler, timeout=60)
        #print(res.json())

        return res_to_admin_handler
    
    except:
        return "Unable to connect to Admin Handler"


@router.post("/issue_requested_credential/{request_id}", status_code=201)
async def issue_requested_credential(request_id: str, response: Response, body: IssueCred): #token: str,
    #if token != authentication.id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"

    # CHECK FOR REQUEST RECORD
    try:
        test = mongo_setup_admin.collection.find_one({"_id": ObjectId(request_id)})
        #print(test)
    except:
        return "Credential Request doesn't exist in Database"

    # ISSUE CREDENTIAL
    try:
        body_dict = body.dict()

        URL = os.environ["ISSUER_AGENT_URL"]
        
        # Configure Credential to be published
        issue_cred = {
            "connection_id": setup_issuer.connection_id,
            "cred_def_id": setup_vc_schema.cred_def_id,
            "credential_proposal": {
                "attributes": [
                    {
                        "name": "type",
                        "value": body_dict["type"]
                    },
                    {
                        "name": "credentialSubject",
                        "value": str(body_dict["credentialSubject"])
                    }
                ]
            }
        }

        final_resp = requests.post(URL+"/issue-credential/send", data=json.dumps(issue_cred), headers=header, timeout=60)
        #print(final_resp.text)
        cred_info = json.loads(final_resp.text)

        if cred_info["state"] == "offer_sent":
            # SUBSCRIBE TO AGENT RESPONSE
            try:
                # UPDATE REQUEST RECORD FROM MONGO
                mongo_setup_admin.collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": "Credential Issued", "credential_definition_id": cred_info["credential_definition_id"]}})
                #mongo_setup.collection.remove({"_id": ObjectId(request_id)})

                resp_cred = {
                    "credential_exchange_id": cred_info["credential_exchange_id"],
                    "credential_definition_id": cred_info["credential_definition_id"],
                    "credential_offer_dict": cred_info["credential_offer_dict"],
                    "created_at": cred_info["created_at"],
                    "updated_at": cred_info["updated_at"],
                    "schema_id": cred_info["schema_id"],
                    "state": "credential_acked"
                }
            
            except:        
                return "Unable to subscribe to response"

            # NOTIFY HOLDER AGENT
            #try:
            holder_url = body_dict["service_endpoint"]
            #print(holder_url)
            requests.post(holder_url+"/holder/update_did_state/"+str(body_dict["holder_request_id"]), json=resp_cred, timeout=60)
            #except:
            #    return "Unable to notify Holder"
            
            return resp_cred

        else:
            return "Unable to subscribe to Credential response"
    
    except:
        return "Unable to connect to Issuer Agent"

@router.get("/read_credential")
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

@router.get("/read_credential/all")
async def read_all_credentials(response: Response, token: str):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        URL = os.environ["HOLDER_AGENT_URL"]
        resp = requests.get(URL+"/credentials", timeout=30)
        body = resp.json()
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