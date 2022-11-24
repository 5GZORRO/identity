from typing import Optional, List
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import requests, json, sys, os, time, threading, jwt
from enum import Enum

from bson import ObjectId
from loguru import logger

from app.db import mongo_setup_admin
from app.bootstrap import setup_issuer
#from app.bootstrap.key import holder_key

router = APIRouter(
    prefix="/authentication",
    tags=["authentication"]
)

class EncodedProof(BaseModel):
    proof_token: str

header = {
    'Content-Type': 'application/json'        
}

@router.post("/verify_credential", status_code=202)
async def verify_credential(response: Response, body: EncodedProof):
    # Read encoded object
    try:
        body_dict = body.dict()
        key = os.environ["KEY"]
        decoded = jwt.decode(body_dict["proof_token"], key, algorithms="HS256")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read proof token")
    
    # Check if Admin has emitted cred, and check if already verified
    try:
        subscriber = mongo_setup_admin.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": decoded["stakeholderDID"]})
        if subscriber is None:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Stakeholder Credential wasn't emitted by this Admin Agent")
        else:
            if "verified" in subscriber:
                return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="Stakeholder Credential already verified")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to check who emitted Stakeholder Credential")

    # SETUP CONNECTION
    try:
        setup_issuer.issuer_connection(decoded["service_endpoint"])

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to establish Issuer Connection")

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
        URL = os.environ["ISSUER_AGENT_URL"]
        logger.info('--- Sending /present-proof/send-request:')
        logger.info(verify_object)
        resp = requests.post(URL+"/present-proof/send-request", data=json.dumps(verify_object), headers=header, timeout=60)
        verify_info = json.loads(resp.text)
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

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform validation")
