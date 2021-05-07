from typing import Optional, List
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import requests, json, sys, os, time, threading, jwt
from enum import Enum

from bson import ObjectId

from app.db import mongo_setup_admin
from app.bootstrap import setup_issuer
from app.bootstrap.key import holder_key

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"]
)

class EncodedProof(BaseModel):
    proof_token: str

header = {
    'Content-Type': 'application/json'        
}

@router.get("/teste", include_in_schema=False, status_code=202)
async def teste(response: Response):
    objecto = {
        "presentation_request_dict":{
            "@type":"did:sov:BzCbsNYhMrjHiqZDTUASHg;spec/present-proof/1.0/request-presentation",
            "@id":"5a2177d2-fafc-4de4-8249-8009ce63f0c0",
            "comment":"Verify Stakeholder",
            "request_presentations~attach":[
                {
                    "@id":"libindy-request-presentation-0",
                    "mime-type":"application/json",
                    "data":{
                        "base64":"eyJuYW1lIjogIlByb29mIG9mIFN0YWtlaG9sZGVyIiwgInZlcnNpb24iOiAiMS4wIiwgInJlcXVlc3RlZF9hdHRyaWJ1dGVzIjoge30sICJyZXF1ZXN0ZWRfcHJlZGljYXRlcyI6IHsiMF90aW1lc3RhbXBfR0VfdXVpZCI6IHsibmFtZSI6ICJ0aW1lc3RhbXAiLCAicF90eXBlIjogIj49IiwgInBfdmFsdWUiOiAxNjIwMTQ3ODQ5LCAicmVzdHJpY3Rpb25zIjogW3siY3JlZF9kZWZfaWQiOiAiVG12dGJ1dWpDUTJlTlUycWRhcExEazozOkNMOjM4OnN0YWtlaG9sZGVyX2NyZWQifV19LCAiMV90aW1lc3RhbXBfR0VfdXVpZCI6IHsibmFtZSI6ICJ0aW1lc3RhbXAiLCAicF90eXBlIjogIjw9IiwgInBfdmFsdWUiOiAxNjIwMTQ3ODQ5LCAicmVzdHJpY3Rpb25zIjogW3siY3JlZF9kZWZfaWQiOiAiVG12dGJ1dWpDUTJlTlUycWRhcExEazozOkNMOjM4OnN0YWtlaG9sZGVyX2NyZWQifV19fSwgIm5vbmNlIjogIjM3MjIzMDk3NTUzMTIzNDA1MzMzMzAxMyJ9"
                    }
                }
            ]
        },
        "connection_id":"663f0cd7-eccb-49be-8009-44058ffa1e3b",
        "auto_present":False,
        "updated_at":"2021-05-04 17:05:10.228346Z",
        "initiator":"self",
        "thread_id":"5a2177d2-fafc-4de4-8249-8009ce63f0c0",
        "presentation_exchange_id":"2f008508-dbf5-42b6-902b-8d996574e752",
        "state":"request_sent",
        "created_at":"2021-05-04 17:05:10.228346Z",
        "role":"verifier",
        "trace":False,
        "presentation_request":{
            "name":"Proof of Stakeholder",
            "version":"1.0",
            "requested_attributes":{
                
            },
            "requested_predicates":{
                "0_timestamp_GE_uuid":{
                    "name":"timestamp",
                    "p_type":">=",
                    "p_value":1620147849,
                    "restrictions":[
                        {
                            "cred_def_id":"TmvtbuujCQ2eNU2qdapLDk:3:CL:38:stakeholder_cred"
                        }
                    ]
                },
                "1_timestamp_GE_uuid":{
                    "name":"timestamp",
                    "p_type":"<=",
                    "p_value":1620147849,
                    "restrictions":[
                        {
                            "cred_def_id":"TmvtbuujCQ2eNU2qdapLDk:3:CL:38:stakeholder_cred"
                        }
                    ]
                }
            },
            "nonce":"372230975531234053333013"
        }
    }
    URL = os.environ["ISSUER_AGENT_URL"]
    stakeholderDID = "XPF1DmYrfr4s6Uv8tY2BA3"
    if objecto["state"] == "request_sent":
        # Check for verification true
        final_resp = requests.get(URL+"/present-proof/records/"+objecto["presentation_exchange_id"], headers=header, timeout=60)
        check_true = json.loads(final_resp.text)
        if check_true["verified"] == "true":
            # UPDATE REQUEST RECORD FROM MONGO
            mongo_setup_admin.stakeholder_col.find_one_and_update({"stakeholderClaim.stakeholderDID": stakeholderDID}, {'$set': {"verified": True}})
            ending = {
                "stakeholderDID": stakeholderDID,
                "verified": True
            }
            return ending






@router.post("/verify_credential", include_in_schema=False, status_code=202)
async def verify_credential(response: Response, body: EncodedProof):
    # Read encoded object
    try:
        body_dict = body.dict()
        key = os.environ["KEY"]
        decoded = jwt.decode(body_dict["proof_token"], key, algorithms="HS256")
    except:
        return "Unable to read proof token"
    
    # Check if Admin has emitted cred
    try:
        subscriber = mongo_setup_admin.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": decoded["stakeholderDID"]})
    except:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Stakeholder Credential wasn't emitted by this Admin Agent"

    # SETUP CONNECTION
    try:
        setup_issuer.issuer_connection()
        #print(setup_issuer.connection_id)
    except:
        return "Unable to establish Issuer Connection"

    # Perform validation
    try:
        verify_object = {
            "connection_id": setup_issuer.connection_id,
            "comment": "Verify Stakeholder",
            "proof_request": {
                "name": "Proof of Stakeholder",
                "version": "1.0",
                "requested_attributes": {},
                "requested_predicates": {
                    "0_timestamp_GE_uuid": {
                        "name": "timestamp",
                        "p_type": ">=",
                        "p_value": int(subscriber["timestamp"]),
                        "restrictions": [
                            {
                                "cred_def_id": subscriber["credential_definition_id"]
                            }
                        ]
                    },
                    "1_timestamp_GE_uuid": {
                        "name": "timestamp",
                        "p_type": "<=",
                        "p_value": int(subscriber["timestamp"]),
                        "restrictions": [
                            {
                                "cred_def_id": subscriber["credential_definition_id"]
                            }
                        ]
                    }
                }
            }
        }
        #print(json.dumps(verify_object))
        URL = os.environ["ISSUER_AGENT_URL"]
        resp = requests.post(URL+"/present-proof/send-request", data=json.dumps(verify_object), headers=header, timeout=60)
        verify_info = json.loads(resp.text)
        #print(verify_info)
        if verify_info["state"] == "request_sent":
            # Check for verification true
            #final_resp = requests.get(URL+"/present-proof/records/"+verify_info["presentation_exchange_id"], headers=header, timeout=60)
            #check_true = json.loads(final_resp.text)
            #print(check_true)
            #time.sleep(10)
            #if check_true["verified"] == "true":
            # UPDATE REQUEST RECORD FROM MONGO
            mongo_setup_admin.stakeholder_col.find_one_and_update({"stakeholderClaim.stakeholderDID": decoded["stakeholderDID"]}, {'$set': {"verified": True}})
            ending = {
                "stakeholderDID": decoded["stakeholderDID"],
                "verified": True
            }
            return ending
    except:
        return "Unable to perform validation"