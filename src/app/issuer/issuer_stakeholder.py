from typing import Optional
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
import requests, json, os, threading

from loguru import logger
from bson import ObjectId

from app.db import mongo_setup_admin
from app.bootstrap import setup_issuer, setup_stake_schema
#from app.authentication import authentication

# classes
from app.issuer.classes import ReqStakeCred, IssueStakeCred, State, ResolveStake

router = APIRouter(
    prefix="/issuer",
    tags=["issuer"]
)

header = {
    'Content-Type': 'application/json'        
}


@router.get("/stakeholder/pending")
async def read_pending_stakeholder_approval(response: Response):
    try:
        result_list = []
        subscriber = mongo_setup_admin.stakeholder_col.find({"state" : State.stakeholder_request, "revoked" : { "$exists" : False}}, {"_id": 0, "service_endpoint": 0})
        
        for result_object in subscriber:
            result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read pending Stakeholder Credentials for approval")


@router.put("/stakeholder/resolve", status_code=200)
async def resolve_pending_stakeholder_approval(response: Response, body: ResolveStake):
    # Check if pending stakeholder exists
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_admin.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": body_dict["stakeholder_did"], "state" : State.stakeholder_request, "revoked" : { "$exists" : False}}, {"_id": 0})
        if subscriber is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Pending Stakeholder Credential not found, or was resolved, or doesn't exist")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to verify existance of pending Stakeholder Credential")

    # Resolve stakeholder credential
    try:
        if body_dict["approval"] is False:
            # Reject Stakeholder Credential
            mongo_setup_admin.stakeholder_col.find_one_and_update({"stakeholderClaim.stakeholderDID": body_dict["stakeholder_did"]}, {'$set': {"state": State.stakeholder_decline}}) # UPDATE REQUEST RECORD FROM MONGO
            requests.post(subscriber["service_endpoint"]+"/holder/decline_stakeholder/"+str(subscriber["holder_request_id"]), timeout=30)
            return "Stakeholder Credential was rejected"
        else:
            # Issue Stakeholder Credential
            try:
                URL = os.environ["ISSUER_AGENT_URL"]
            
                # Configure Stakeholder to be registered
                issue_cred = {
                    "connection_id": subscriber["connection_id"],
                    "cred_def_id": subscriber["credential_definition_id"],
                    "credential_proposal": {
                        "attributes": [
                            {
                                "name": "stakeholderClaim",
                                "value": str(subscriber["stakeholderClaim"])
                            },
                            {
                                "name": "timestamp",
                                "value": str(subscriber["timestamp"])
                            }
                        ]
                    }
                }

                final_resp = requests.post(URL+"/issue-credential/send", data=json.dumps(issue_cred), headers=header, timeout=60)
                #print(final_resp.text)
                cred_info = json.loads(final_resp.text)
                id_token = cred_info["credential_exchange_id"]

            except Exception as error:
                logger.error(error)
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to issue credential on agent")

            if cred_info["state"] == "offer_sent":
                # SUBSCRIBE TO AGENT RESPONSE
                try:
                    # UPDATE REQUEST RECORD FROM MONGO
                    mongo_setup_admin.stakeholder_col.find_one_and_update({"stakeholderClaim.stakeholderDID": body_dict["stakeholder_did"]}, {'$set': {"state": State.stakeholder_issue, "id_token": id_token}})
                    #mongo_setup.stakeholder_col.remove({"_id": ObjectId(request_id)})

                    resp_cred = {
                        #"credential_exchange_id": cred_info["credential_exchange_id"],
                        "id_token": id_token,
                        "credential_definition_id": cred_info["credential_definition_id"],
                        "credential_offer_dict": cred_info["credential_offer_dict"],
                        "created_at": cred_info["created_at"],
                        "updated_at": cred_info["updated_at"],
                        "schema_id": cred_info["schema_id"],
                        "state": "credential_acked"
                    }
                
                except Exception as error:
                    logger.error(error)
                    return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to update and subscribe to response")

                # NOTIFY HOLDER AGENT
                requests.post(subscriber["service_endpoint"]+"/holder/update_stakeholder_state/"+str(subscriber["holder_request_id"]), json=resp_cred, timeout=60)

                return resp_cred

            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to subscribe to Stakeholder Credential response")
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to resolve pending Stakeholder Credential for approval")


@router.post("/request_stakeholder_issue/{request_id}", status_code=201, include_in_schema=False)
async def request_stakeholder_issue(request_id: str, response: Response, body: ReqStakeCred):
    try:
        worker = threading.Thread(target = process_holder_request, args=(request_id, body,), daemon=True)
        worker.start()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to process Holder Request")

def process_holder_request(request_id: str, body: dict):
    # SETUP ISSUER CONNECTION
    try:
        body_dict = body.dict()
        setup_issuer.issuer_connection(body_dict["agent_service_endpoint"])

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to establish Issuer Connection")

    # SETUP AUTH SCHEMA
    try:
        setup_stake_schema.stakeholder_cred_setup()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to setup Stakeholder Schema")
    
    # CHECK FOR REQUEST RECORD
    test = mongo_setup_admin.stakeholder_col.find_one({"holder_request_id": request_id})
    if test != None:
        if test["state"] == State.stakeholder_issue: # "Stakeholder Registered"
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="Stakeholder Request was already issued")

    # SUBMIT REQUEST TO ADMIN HANDLER
    try:
        res_to_insert_db = {
            "holder_request_id": request_id,
            "stakeholderClaim": {
                "governanceBoardDID": body_dict["stakeholderClaim"]["governanceBoardDID"],
                "stakeholderServices": body_dict["stakeholderClaim"]["stakeholderServices"],
                #"stakeholderRoles": {
                #    "role": body_dict["stakeholderClaim"]["stakeholderRoles"]["role"],
                #    "assets": body_dict["stakeholderClaim"]["stakeholderRoles"]["assets"]
                #},
                "stakeholderRoles": body_dict["stakeholderClaim"]["stakeholderRoles"],
                "stakeholderProfile": {
                    "name": body_dict["stakeholderClaim"]["stakeholderProfile"]["name"],
                    "ledgerIdentity": body_dict["stakeholderClaim"]["stakeholderProfile"]["ledgerIdentity"],
                    "address": body_dict["stakeholderClaim"]["stakeholderProfile"]["address"],
                    "notificationMethod": body_dict["stakeholderClaim"]["stakeholderProfile"]["notificationMethod"]
                },
                "stakeholderDID": body_dict["stakeholderClaim"]["stakeholderDID"]
                #"did": body_dict["stakeholderClaim"]["did"],
                #"verkey": body_dict["stakeholderClaim"]["verkey"]
            },
            "timestamp": body_dict["timestamp"],
            "state": State.stakeholder_request,
            "service_endpoint": body_dict["service_endpoint"],
            "handler_url": body_dict["handler_url"],
            "connection_id": setup_issuer.connection_id,
            "credential_definition_id": setup_stake_schema.cred_def_id
        }

        mongo_setup_admin.stakeholder_col.insert_one(res_to_insert_db)
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to connect to Admin Handler")  
