from fastapi import APIRouter, Response, status, Query
from fastapi.responses import JSONResponse
import requests, json, sys, os, time, threading, copy

from loguru import logger
from bson import ObjectId

#from app.authentication import authentication
from app.db import mongo_setup_provider
#from app.bootstrap.key import holder_key
from app.holder import utils

# classes
from app.holder.classes import Stakeholder, StakeholderResp, State, StateQuery

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
    try:
        # Find one not equal to Declined or revoked
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"state": {"$ne": State.stakeholder_decline}, "revoked" : { "$exists" : False} }, {"_id": 0, "handler_url": 0})
        if subscriber is not None:
            return JSONResponse(status_code=status.HTTP_409_CONFLICT, content="A Stakeholder Credential has already been requested/issued")

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to check for active stakeholder credential")

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
            "agent_service_endpoint": holder_url,
            "handler_url": body_dict["handler_url"]
        }
        #print(res_to_admin)
        #print("\n")
        
        URL = os.environ["ADMIN_AGENT_CONTROLLER_URL"]
        requests.post(URL+"/issuer/request_stakeholder_issue/"+str(res_to_mongo["_id"]), json=res_to_admin, timeout=60)


        # SEND TO HOLDER HANDLER
        worker = threading.Thread(target = utils.send_to_holder, args=(body_dict["handler_url"], client_res,), daemon=True)
        worker.start()

        return client_res
        
    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to perform Stakeholder registration request")       


@router.get("/stakeholder/{stakeholder_did}", responses={200: {"model": StakeholderResp}})
async def read_specific_stakeholder_by_did(stakeholder_did: str):
    try:
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": stakeholder_did}, {"_id": 0})
        if subscriber == None:
            # Check other Id&P instances
            for i in json.loads(os.environ["OTHER_IDP_CONTROLLERS"]):
                res = requests.get(i+"/holder/stakeholder/"+stakeholder_did+"/others", timeout=60)
                if res.status_code == 200:
                    return res.json()

            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Stakeholder Credential non existent or not found")

        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read specific Stakeholder Credential")

@router.get("/stakeholder/{stakeholder_did}/others", include_in_schema=False)
async def read_others_stakeholder_by_did(stakeholder_did: str):
    try:
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": stakeholder_did}, {"_id": 0, "id_token": 0, "handler_url": 0, "credential_definition_id": 0})
        if subscriber == None:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Stakeholder Credential non existent or not found")

        else: 
            return subscriber

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to read specific Stakeholder Credential")


@router.get("/stakeholder", responses={200: {"model": list[StakeholderResp]}})
async def query_stakeholder_creds(state: set[StateQuery] = Query(...)):
    try:
        result_list = []
        for status in state:
            if status == StateQuery.approved:
                subscriber = mongo_setup_provider.stakeholder_col.find({"state": State.stakeholder_issue, "revoked" : {"$exists" : False}}, {"_id": 0})
            elif status == StateQuery.pending:
                subscriber = mongo_setup_provider.stakeholder_col.find({"state": State.stakeholder_request, "revoked" : {"$exists" : False}}, {"_id": 0})
            elif status == StateQuery.rejected:
                subscriber = mongo_setup_provider.stakeholder_col.find({"state": State.stakeholder_decline, "revoked" : {"$exists" : False}}, {"_id": 0})
            else:
                subscriber = mongo_setup_provider.stakeholder_col.find({"revoked" : {"$exists" : True}}, {"_id": 0})

            for result_object in subscriber:
                result_list.append(result_object)

        return result_list

    except Exception as error:
        logger.error(error)
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content="Unable to fetch Stakeholder Credentials on Database")
