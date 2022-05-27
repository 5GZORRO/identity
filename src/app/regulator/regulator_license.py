from typing import Optional
from fastapi import APIRouter, Response, status, Query
from fastapi.responses import JSONResponse
import requests, json, os, threading

from loguru import logger
from bson import ObjectId

from app.db import mongo_setup_provider, mongo_setup_regulator
from app.bootstrap import setup_issuer, setup_license_schema

# classes
from app.regulator.classes import ReqLicenseCred, State, ResolveLicense, StateQuery

router = APIRouter(
    prefix="/regulator",
    tags=["regulator"]
)

header = {
    'Content-Type': 'application/json'        
}


@router.post("/request_license_issue/{request_id}", status_code=201, include_in_schema=False)
async def request_license_issue(request_id: str, body: ReqLicenseCred):
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
        setup_license_schema.stake_license_cred_setup()

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to setup Stakeholder License Schema")
    
    # CHECK FOR REQUEST RECORD
    test = mongo_setup_regulator.license_collection.find_one({"holder_request_id": request_id})
    if test != None:
        if test["state"] == State.license_issue:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="Stakeholder License Request was already issued")

    # SUBMIT REQUEST TO REGULATOR HANDLER
    try:
        res_to_insert_db = {
            "holder_request_id": request_id,
            "stakeholderServices": body_dict["stakeholderServices"],
            "id_token": body_dict["id_token"],
            "stakeholderDID": body_dict["stakeholderDID"],
            "licenseDID": body_dict["licenseDID"],
            "timestamp": body_dict["timestamp"],
            "state": State.license_request,
            "service_endpoint": body_dict["service_endpoint"],
            "connection_id": setup_issuer.connection_id,
            "credential_definition_id": setup_license_schema.cred_def_id
        }

        mongo_setup_regulator.license_collection.insert_one(res_to_insert_db)
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to connect to Regulator Handler")  


@router.get("/license", status_code=200)
async def query_license_creds(state: set[StateQuery] = Query(...)):
    try:
        result_list = []
        for status in state:
            if status == "approved":
                subscriber = mongo_setup_regulator.license_collection.find({"state" : State.license_issue, "revoked" : {"$exists" : False}}, {"_id": 0, "holder_request_id":0, "service_endpoint": 0})
            elif status == "pending":
                subscriber = mongo_setup_regulator.license_collection.find({"state" : State.license_request, "revoked" : {"$exists" : False}}, {"_id": 0, "holder_request_id":0, "service_endpoint": 0})
            else:
                subscriber = mongo_setup_regulator.license_collection.find({"state" : State.license_decline, "revoked" : {"$exists" : False}}, {"_id": 0, "holder_request_id":0, "service_endpoint": 0})

            for result_object in subscriber:
                result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch License Credentials on Database")


@router.put("/license/resolve", status_code=200)
async def resolve_pending_license_approval(response: Response, body: ResolveLicense):
    # AUTH
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["id_token"]})
        if subscriber is not None:
            if body_dict["id_token"] != subscriber["id_token"]:            
                return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid Regulator ID Token")
            
        else:
            return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content="Invalid Regulator ID Token")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to verify Regulator ID Token")
    
    # Check if pending license exists
    try:
        subscriber = mongo_setup_regulator.license_collection.find_one({"licenseDID": body_dict["license_did"], "state" : State.license_request, "revoked" : { "$exists" : False}}, {"_id": 0})
        if subscriber is None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Pending Stakeholder License Credential not found, or was resolved, or doesn't exist")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to verify existance of pending Stakeholder License Credential")

    # Resolve license credential
    try:
        if body_dict["approval"] is False:
            # Reject license Credential
            mongo_setup_regulator.license_collection.find_one_and_update({"licenseDID": body_dict["license_did"]}, {'$set': {"state": State.license_decline}}) # UPDATE REQUEST RECORD FROM MONGO
            requests.post(subscriber["service_endpoint"]+"/holder/decline_license/"+str(subscriber["holder_request_id"]), timeout=30)
            return "Stakeholder License Credential was rejected"
        else:
            # Issue license Credential
            try:
                URL = os.environ["ISSUER_AGENT_URL"]
            
                # Configure license to be registered
                issue_cred = {
                    "connection_id": subscriber["connection_id"],
                    "cred_def_id": subscriber["credential_definition_id"],
                    "credential_proposal": {
                        "attributes": [
                            {
                                "name": "stakeholderServices",
                                "value": str(subscriber["stakeholderServices"])
                            },
                            {
                                "name": "licenseDID",
                                "value": str(subscriber["licenseDID"])
                            },
                            {
                                "name": "timestamp",
                                "value": str(subscriber["timestamp"])
                            }
                        ]
                    }
                }

                final_resp = requests.post(URL+"/issue-credential/send", data=json.dumps(issue_cred), headers=header, timeout=60)
                cred_info = json.loads(final_resp.text)

            except Exception as error:
                logger.error(error)
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to issue credential on agent")

            if cred_info["state"] == "offer_sent":
                # SUBSCRIBE TO AGENT RESPONSE
                try:
                    # UPDATE REQUEST RECORD FROM MONGO
                    mongo_setup_regulator.license_collection.find_one_and_update({"licenseDID": body_dict["license_did"]}, {'$set': {"state": State.license_issue, "credential_exchange_id": cred_info["credential_exchange_id"]}})

                    resp_cred = {
                        "credential_exchange_id": cred_info["credential_exchange_id"],
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
                requests.post(subscriber["service_endpoint"]+"/holder/update_license_state/"+str(subscriber["holder_request_id"]), json=resp_cred, timeout=60)

                return resp_cred

            else:
                return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to subscribe to Stakeholder License Credential response")
    
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to resolve pending Stakeholder License Credential for approval")
