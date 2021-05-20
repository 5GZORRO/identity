from typing import Optional, List
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import requests, json, sys, os, time, threading
from enum import Enum

from bson import ObjectId

#from app.authentication import authentication
from app.db import mongo_setup_provider
from app.bootstrap.key import holder_key

router = APIRouter(
    prefix="/holder",
    tags=["holder"]
)

### Role -> Enums ###
class Type(str, Enum):
    product_offer = 'ProductOffer'
    regulated_product_offer = 'RegulatedProductOffer'
    governance_proposal = 'GovernanceProposal'
    governance_vote = 'GovernanceVote'
    legal_prose_template = 'LegalProseTemplate'
    sla = 'SLA'
    agreement = 'Agreement'

class Offer(BaseModel):
    token: str
    type: Type
    #claims: dict
    claims: list = []
    handler_url: str

### Role -> Enums ###
class Role(str, Enum):
    Regulator = 'Regulator'
    Resource_Provider = 'ResourceProvider'
    Resource_Consumer = 'ResourceConsumer'
    Service_Provider = 'ServiceProvider'
    Service_Consumer = 'ServiceConsumer'

### Assets -> Enums ###
class Assets(str, Enum):
    InformationResource = 'InformationResource'
    SpectrumResource = 'SpectrumResource'
    PhysicalResource = 'PhysicalResource'
    NetworkFunction = 'NetworkFunction'

### notificationType -> Enum ###
class NType(str, Enum):
    EMAIL = 'EMAIL'

class SHRoles(BaseModel):
    #role: str
    role: Role
    assets: List[Assets]
    #assets: str

class SHServices(BaseModel):
    type: str
    endpoint: str

class SHNotify(BaseModel):
    notificationType: NType
    distributionList: str

class SHProfile(BaseModel):
    name: str
    address: str
    notificationMethod: SHNotify

class Stakeholder(BaseModel):
    key: str
    governanceBoardDID: str
    #stakeholderServices: list = []
    stakeholderServices: List[SHServices]
    stakeholderRoles: List[SHRoles]
    #stakeholderRoles: SHRoles
    stakeholderProfile: SHProfile
    handler_url: str


class ReadStakeDID(BaseModel):
    stakeholderDID: str

class ReadOfferDID(BaseModel):
    token: str
    did_identifier: str


header = {
    'Content-Type': 'application/json'        
}


####################### Stakeholder Registration #######################
@router.post("/register_stakeholder", status_code=201)
async def register_stakeholder(response: Response, body: Stakeholder): #key: str,
    # AUTH
    try:
        body_dict = body.dict()
        if body_dict["key"] != holder_key.verkey:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Invalid Verification Key"
    except:
        return "Unable to authenticate used key."

    # PRIVATE DID
    try:
        holder_url = os.environ["HOLDER_AGENT_URL"]
        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        did = result["result"]["did"]
        #verkey = result["result"]["verkey"]
    except:
        return "Unable to create wallet DID."

    
    # STORE REQUEST ON MONGO
    try:
        epoch_ts = str(int(time.time()))

        # MONGO WILL ADD _id TO THIS DICT
        res_to_mongo = {
            "stakeholderClaim": {
                "governanceBoardDID": body_dict["governanceBoardDID"],
                "stakeholderServices": body_dict["stakeholderServices"],
                #"stakeholderRoles": {
                #    "role": body_dict["stakeholderRoles"]["role"],
                #    "assets": body_dict["stakeholderRoles"]["assets"]
                #},
                "stakeholderRoles": body_dict["stakeholderRoles"],
                "stakeholderProfile": {
                    "name": body_dict["stakeholderProfile"]["name"],
                    "address": body_dict["stakeholderProfile"]["address"],
                    "notificationMethod": body_dict["stakeholderProfile"]["notificationMethod"]
                },
                "stakeholderDID": did
                #"did": did,
                #"verkey": verkey
            },
            "timestamp": epoch_ts,
            "state": "Stakeholder Registration Requested",
            "handler_url": body_dict["handler_url"]
        }

        mongo_setup_provider.stakeholder_col.insert_one(res_to_mongo)

    except:
        return "Unable to store Credential request on Database."
    

    # SEND TO ADMIN
    try:
        res_to_admin = {
            "stakeholderClaim": {
                "governanceBoardDID": body_dict["governanceBoardDID"],
                "stakeholderServices": body_dict["stakeholderServices"],
                #"stakeholderRoles": {
                #    "role": body_dict["stakeholderRoles"]["role"],
                #    "assets": body_dict["stakeholderRoles"]["assets"]
                #},
                "stakeholderRoles": body_dict["stakeholderRoles"],
                "stakeholderProfile": {
                    "name": body_dict["stakeholderProfile"]["name"],
                    "address": body_dict["stakeholderProfile"]["address"],
                    "notificationMethod": body_dict["stakeholderProfile"]["notificationMethod"]
                },
                "stakeholderDID": did
                #"did": did,
                #"verkey": verkey
            },
            "timestamp": epoch_ts,
            "service_endpoint": os.environ["TRADING_PROVIDER_AGENT_CONTROLLER_URL"],
            "agent_service_endpoint": holder_url
        }
        #print(res_to_admin)
        #print("\n")
        
        URL = os.environ["ADMIN_AGENT_CONTROLLER_URL"]
        requests.post(URL+"/issuer/request_stakeholder_issue/"+str(res_to_mongo["_id"]), json=res_to_admin, timeout=60)
       

        client_res = {
            #"_id": str(res_to_mongo["_id"]),
            "stakeholderClaim": {
                "governanceBoardDID": body_dict["governanceBoardDID"],
                "stakeholderServices": body_dict["stakeholderServices"],
                #"stakeholderRoles": {
                #    "role": body_dict["stakeholderRoles"]["role"],
                #    "assets": body_dict["stakeholderRoles"]["assets"]
                #},
                "stakeholderRoles": body_dict["stakeholderRoles"],
                "stakeholderProfile": {
                    "name": body_dict["stakeholderProfile"]["name"],
                    "address": body_dict["stakeholderProfile"]["address"],
                    "notificationMethod": body_dict["stakeholderProfile"]["notificationMethod"]
                },
                "stakeholderDID": did
                #"did": did,
                #"verkey": verkey
            },
            "timestamp": epoch_ts,
            "state": "Stakeholder Registration Requested",
            "handler_url": body_dict["handler_url"]
        }

        # SEND TO HOLDER HANDLER
        #try:
        #    holder_handler_resp = requests.post(body_dict["handler_url"], headers=header, json=client_res, timeout=30)
        #    holder_body = holder_handler_resp.json()
        #except:
        #    return "Unable to send request info to Holder's Handler"
        thread = threading.Thread(target = send_to_holder, args=(body_dict["handler_url"],client_res,), daemon=True)
        thread.start()

        return client_res
        
    except:
        return "Unable to perform Stakeholder registration request."

def send_to_holder(url: str, client_response: dict):
    try:    
        holder_handler_resp = requests.post(url, headers=header, json=client_response, timeout=30)
        holder_body = holder_handler_resp.json()
        return holder_body
    except:
        return "Unable to send request info to Holder's Handler"


@router.post("/update_stakeholder_state/{request_id}", include_in_schema=False)
async def update_stakeholder_state(request_id: str, body: dict, response: Response):
    #UPDATE MONGO RECORD
    try:
        mongo_setup_provider.stakeholder_col.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": "Stakeholder Registered", "credential_definition_id": body["credential_definition_id"], "id_token": body["id_token"]}}) # UPDATE REQUEST RECORD FROM MONGO
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"_id": ObjectId(request_id)})
        #global id_token
        #id_token = body["id_token"]
        #print("\n")
        #print("id_token: "+ str(id_token))
    except:
        return "Unable to update Mongo record"
    
    # SEND REQUEST RECORD TO HOLDER HANDLER
    try:
        requests.post(subscriber["handler_url"], headers=header, json=body, timeout=30)
    except:
        return "Unable to send info to Holder Handler"

@router.post("/read_stakeholder_status")
async def read_stakeholder_status(response: Response, body: ReadStakeDID): # key: str, stakeholder_did: str
    #if key != holder_key.verkey:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid Verification Key"
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"stakeholderClaim.stakeholderDID": body_dict["stakeholderDID"]}, {"_id": 0, "handler_url": 0})
        if subscriber == None:
            response.status_code = status.HTTP_404_NOT_FOUND
            return "Stakeholder Credential non existent"
        else: 
            return subscriber
    except:
        return "Unable to fetch requested Stakeholder Credential"


####################### Verifiable Credentials Management #######################
@router.post("/create_did", status_code=201)
async def request_credential(response: Response, body: Offer):
    # AUTH
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["token"]})
        if body_dict["token"] != subscriber["id_token"]:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Invalid ID Token"
    except:
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
        epoch_ts = str(int(time.time()))

        # MONGO WILL ADD _id TO THIS DICT
        res_to_mongo = {
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "timestamp": epoch_ts,
            "state": "Credential Requested",
            "handler_url": body_dict["handler_url"]
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
            "timestamp": epoch_ts,
            "service_endpoint": os.environ["TRADING_PROVIDER_AGENT_CONTROLLER_URL"],
            "agent_service_endpoint": holder_url
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
            #"_id": str(res_to_mongo["_id"]),
            "type": body_dict["type"],
            "credentialSubject": {
                "id": did,
                "claims": body_dict["claims"]
            },
            "timestamp": epoch_ts,
            "state": "Credential Requested",
            "handler_url": body_dict["handler_url"]
        }
        
        # SEND TO HOLDER HANDLER
        try:
            holder_handler_resp = requests.post(body_dict["handler_url"], headers=header, json=client_res, timeout=30)
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

@router.post("/read_did_status")
async def read_credential_status(response: Response, body: ReadOfferDID):
    #if token != id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_provider.stakeholder_col.find_one({"id_token": body_dict["token"]})
        if body_dict["token"] != subscriber["id_token"]:
            response.status_code = status.HTTP_401_UNAUTHORIZED
            return "Invalid ID Token"
    except:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        subscriber = mongo_setup_provider.collection.find_one({"credentialSubject.id": body_dict["did_identifier"]}, {"_id": 0})
        if subscriber == None:
            response.status_code = status.HTTP_404_NOT_FOUND
            return "DID Credential non existent"
        else: 
            return subscriber

    except:
        return "Unable to fetch requested DID"


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

    #try:
    #    URL = os.environ["HOLDER_AGENT_URL"]
    #    resp = requests.get(URL+"/credential/"+cred_id, timeout=30)
    #    body = resp.json()
    #    return body

    #except:
    #    return "Unable to fetch specific Marketplace Credential"

    try:
        subscriber = mongo_setup_provider.collection.find_one({"credentialSubject.id": did_identifier, "state": "Credential Issued"}, {"_id": 0, "state": 0, "handler_url": 0})
        if subscriber == None:
            return "Marketplace Credential not issued"
        else: 
            return subscriber

    except:
        return "Unable to fetch specific Marketplace Credential"


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

    #try:
    #    URL = os.environ["HOLDER_AGENT_URL"]
    #    resp = requests.get(URL+"/credentials", timeout=30)
    #    body = resp.json()
    #    if handler_url != None:
    #        try:
    #            requests.post(handler_url, headers=header, json=body, timeout=30)
    #        except:
    #            body.update({"handler_info": "Unable to send data to Handler URL"})
    #    return body

    #except:
    #    return "Unable to fetch Marketplace Credentials"
    
    try:
        subscriber = mongo_setup_provider.collection.find({"state": "Credential Issued"}, {"_id": 0, "state": 0, "handler_url": 0})
        
        result_list = []

        for result_object in subscriber:
            print(result_object)
            result_list.append(result_object)

        return result_list

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