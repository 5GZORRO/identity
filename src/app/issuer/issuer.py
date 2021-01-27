from typing import Optional
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import requests, json, os

from bson import ObjectId

from app.bootstrap import setup_issuer, setup_vc_schema, mongo_setup
from app.authentication import authentication

router = APIRouter(
    prefix="/issuer",
    tags=["issuer"]
)

class VC(BaseModel):
    type: str
    credentialSubject: dict
    handler_url: str

header = {
    'Content-Type': 'application/json'        
}

####################### Verifiable Credentials Management #######################
@router.post("/request_credential_issue/{request_id}") #, include_in_schema=False 
async def request_credential_issue(request_id: str, response: Response, body: VC):
    # CHECK FOR REQUEST RECORD
    try:
        test = mongo_setup.collection.find_one({"_id": ObjectId(request_id)})
        if test["state"] == "Credential Issued":
            return "Credential Request was already issued"
        #print(test)
    except:
        return "Credential Request doesn't exist in Database"

    try:
        #print("\n" + str(body))
        body_dict = body.dict()
        #print("ID: " + str(body_dict["id"]))

        URL = os.environ["ISSUER_AGENT_URL"]
        print(body_dict)

        res_to_admin_handler = {
            "_id": request_id,
            "type": body_dict["type"],
            "credentialSubject": {
                "id": body_dict["credentialSubject"]["id"],
                "claims": body_dict["credentialSubject"]["claims"]
            },
            "handler_url": body_dict["handler_url"]
        }
        print(res_to_admin_handler)
        
        handler_url = os.environ["HANDLER_ADMIN_URL"]
        requests.post(handler_url+"/receive", headers=header, json=res_to_admin_handler, timeout=60)
        #print(res.json())

        return res_to_admin_handler
    
    except:
        return "Unable to connect to Admin Handler"

@router.post("/issue_requested_credential/{request_id}", status_code=201)
async def issue_requested_credential(request_id: str, response: Response, token: str, body: VC):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    # CHECK FOR REQUEST RECORD
    try:
        test = mongo_setup.collection.find_one({"_id": ObjectId(request_id)})
        print(test)
    except:
        return "Credential Request doesn't exist in Database"

    # ISSUE CREDENTIAL
    try:
        #print("\n" + str(body))
        body_dict = body.dict()
        #print("ID: " + str(body_dict["id"]))

        URL = os.environ["ISSUER_AGENT_URL"]
        
        # Configure Credential to be published
        issue_cred = {
            "connection_id": "9248ee8a-7b70-4723-a36a-94e863745133", #setup_issuer.connection_id,
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
        #print(issue_cred)

        final_resp = requests.post(URL+"/issue-credential/send", data=json.dumps(issue_cred), headers=header, timeout=60)
        #print(final_resp.text)
        cred_info = json.loads(final_resp.text)

        if cred_info["state"] == "offer_sent":
            # SUBSCRIBE TO AGENT RESPONSE
            try:
                mongo_setup.collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": "Credential Issued"}}) # UPDATE REQUEST RECORD FROM MONGO
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

            # SEND REQUEST RECORD TO HOLDER HANDLER
            try:
                #print(body_dict["handler_url"])
                requests.post(body_dict["handler_url"], headers=header, json=resp_cred, timeout=30)
            except:
                return "Unable to send info to Holder Handler"
            
            return resp_cred

        else:
            return "Unable to subscribe to Credential response"
    
    except:
        return "Unable to connect to Issuer Agent"

@router.post("/issue")
async def issue_credential(response: Response, token: str, body: VC, handler_url: Optional[str] = None):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        #print("\n" + str(body))
        body_dict = body.dict()
        #print("ID: " + str(body_dict["id"]))

        URL = os.environ["ISSUER_AGENT_URL"]
        
        # Configure Credential to be published
        issue_cred = {
            "connection_id": "9248ee8a-7b70-4723-a36a-94e863745133", #setup_issuer.connection_id,
            "cred_def_id": setup_vc_schema.cred_def_id,
            "credential_proposal": {
                "attributes": [
                    #{
                    #    "name": "id",
                    #    "value": body_dict["id"]
                    #},
                    {
                        "name": "type",
                        "value": body_dict["type"]
                    },
                    {
                        "name": "credentialSubject",
                        "value": str(body_dict["credentialSubject"])
                    }
                    #{
                    #    "name": "issuer",
                    #    "value": str(body_dict["issuer"])
                    #},
                    #{
                    #    "name": "issuanceDate",
                    #    "value": body_dict["issuanceDate"]
                    #},
                    #{
                    #    "name": "expirationDate",
                    #    "value": body_dict["expirationDate"]
                    #},
                    #{
                    #    "name": "credentialStatus",
                    #    "value": str(body_dict["credentialStatus"])
                    #},
                    #{
                    #    "name": "proof",
                    #    "value": str(body_dict["proof"])
                    #}
                ]
            }
        }
        #print(issue_cred)

        final_resp = requests.post(URL+"/issue-credential/send", data=json.dumps(issue_cred), headers=header, timeout=60)
        #print(final_resp.text)
        cred_info = json.loads(final_resp.text)
        if cred_info["state"] == "offer_sent":
            resp_cred = {
                "credential_exchange_id": cred_info["credential_exchange_id"],
                "credential_definition_id": cred_info["credential_definition_id"],
                "credential_offer_dict": cred_info["credential_offer_dict"],
                "created_at": cred_info["created_at"],
                "updated_at": cred_info["updated_at"],
                "schema_id": cred_info["schema_id"],
                "state": "credential_acked"
            }
            if handler_url != None:
                try:
                    requests.post(handler_url, headers=header, json=resp_cred, timeout=30)
                except:
                    resp_cred.update({"handler_info": "Unable to send data to Handler URL"})
            response.status_code = status.HTTP_201_CREATED
            return resp_cred
        else:
            return "Unable to subscribe to Credential response"
    
    except:
        return "Unable to connect to Issuer Agent"

@router.get("/read")
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

@router.get("/read/all")
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