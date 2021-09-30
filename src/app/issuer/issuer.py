from typing import Optional
from fastapi import APIRouter, Response, status
import requests, json, os

from bson import ObjectId

from app.db import mongo_setup_admin
from app.bootstrap import setup_issuer, setup_vc_schema, setup_stake_schema
#from app.authentication import authentication

# classes
from app.issuer.classes import ReqCred, IssueCred, RevokeCred, ReqStakeCred, IssueStakeCred

router = APIRouter(
    prefix="/issuer",
    tags=["issuer"]
)

header = {
    'Content-Type': 'application/json'        
}


####################### Verifiable Credentials Management #######################
@router.post("/request_credential_issue/{request_id}", include_in_schema=False)
async def request_credential_issue(request_id: str, response: Response, body: ReqCred):
    # SETUP ISSUER CONNECTION
    try:
        body_dict = body.dict()

        setup_issuer.issuer_connection(body_dict["agent_service_endpoint"])
        print(setup_issuer.connection_id)
    except:
        return "Unable to establish Issuer Connection"

    # SETUP VC SCHEMA
    try:
        setup_vc_schema.vc_setup()
        print(setup_vc_schema.cred_def_id)
    except:
        return "Unable to setup Verifiable Credential Schema"

    # CHECK FOR REQUEST RECORD
    test = mongo_setup_admin.collection.find_one({"holder_request_id": request_id})
    if test != None:
        if test["state"] == "Credential Issued":
            return "Credential Request was already issued"

    # SUBMIT REQUEST TO ADMIN HANDLER
    try:
        res_to_insert_db = {
            "holder_request_id": request_id,
            "type": body_dict["type"],
            "credentialSubject": {
                "id": body_dict["credentialSubject"]["id"],
                "claims": body_dict["credentialSubject"]["claims"]
            },
            "timestamp": body_dict["timestamp"],
            "state": "Credential Requested",
            #"handler_url": body_dict["handler_url"]
            "service_endpoint": body_dict["service_endpoint"]
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
            "timestamp": body_dict["timestamp"],
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
                    },
                    {
                        "name": "timestamp",
                        "value": str(body_dict["timestamp"])
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
                mongo_setup_admin.collection.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": "Credential Issued", "credential_definition_id": cred_info["credential_definition_id"], "credential_exchange_id": cred_info["credential_exchange_id"]}})
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

@router.get("/read_issued_did")
async def read_issued_did(response: Response, did_identifier: str): #token: str,
    #if token != authentication.id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"

    try:
        #URL = os.environ["HOLDER_AGENT_URL"]
        #resp = requests.get(URL+"/credential/"+cred_id, timeout=30)
        #body = resp.json()
        #return body
        
        subscriber = mongo_setup_admin.collection.find_one({"credentialSubject.id": did_identifier, "state": "Credential Issued", "revoked" : {"$exists" : False}}, {"_id": 0, "holder_request_id":0, "state": 0, "service_endpoint": 0})
        if subscriber == None:
            return "Marketplace Credential revoked or not issued"
        else: 
            return subscriber

    except:
        return "Unable to fetch specific issued Marketplace Credential"

@router.get("/read_issued_did/all")
async def read_all_issued_did(response: Response): #, token: str
    #if token != authentication.id_token:
    #    response.status_code = status.HTTP_401_UNAUTHORIZED
    #    return "Invalid ID Token"

    try:
        #URL = os.environ["HOLDER_AGENT_URL"]
        #resp = requests.get(URL+"/credentials", timeout=30)
        #body = resp.json()
        #return body
        subscriber = mongo_setup_admin.collection.find({"state": "Credential Issued", "revoked" : {"$exists" : False}}, {"_id": 0, "holder_request_id":0, "state": 0, "service_endpoint": 0})
        result_list = []

        for result_object in subscriber:
            #print(result_object)
            result_list.append(result_object)

        return result_list

    except:
        return "Unable to fetch issued Marketplace Credentials"

@router.put("/revoke_did")
async def revoke_credential(response: Response, body: RevokeCred):
    # CHECK FOR REQUEST RECORD
    try:
        body_dict = body.dict()
        subscriber = mongo_setup_admin.collection.find_one({"credential_exchange_id": body_dict["cred_exchange_id"]}, {"_id":0})
        #return subscriber
        if subscriber == None:
            return "Credential doesn't exist in Database or hasn't been issued yet."
    except:
        return "Unable to find Credential."

    # CHECK IF CRED IS ALREADY REVOKED
    try:
        if "revoked" in subscriber:
            response.status_code = status.HTTP_409_CONFLICT
            return "Credential already revoked."
    except:
        return "Unable to check if Credential is revoked."   

    # REVOKE CREDENTIAL
    try:
        # Configure Credential to be published
        revoke_cred = {
            "cred_ex_id": subscriber["credential_exchange_id"],
            "publish": True
        }
        URL = os.environ["ISSUER_AGENT_URL"]
        final_resp = requests.post(URL+"/revocation/revoke", data=json.dumps(revoke_cred), headers=header, timeout=60)
        #revoke_info = json.loads(final_resp.text)
        #return revoke_info
    except:
        return "Unable to revoke Credential."

    # UPDATE CRED INFO
    try:
        mongo_setup_admin.collection.find_one_and_update({"credential_exchange_id": subscriber["credential_exchange_id"]}, {'$set': {"revoked": True}})
        resp_revoke = {
            "credential_exchange_id": subscriber["credential_exchange_id"],
            "revoked": True
        }
    except:        
        return "Unable to subscribe to response."

    # NOTIFY HOLDER AGENT
    holder_url = subscriber["service_endpoint"]
    #print(holder_url)
    requests.post(holder_url+"/holder/update_revoked_state/"+str(subscriber["credential_exchange_id"]), json=resp_revoke, timeout=60)
    
    return resp_revoke

@router.get("/read_did/revoked")
async def read_revoked_credential():
    try:
        subscriber = mongo_setup_admin.collection.find({"revoked" : { "$exists" : True}}, {"_id": 0, "holder_request_id":0, "state": 0, "service_endpoint": 0, "revoked": 0})
        result_list = []

        for result_object in subscriber:
            result_list.append(result_object)

        return result_list

    except:
        return "Unable to fetch specific Marketplace Credential"


####################### Stakeholder Registration Management #######################
@router.post("/request_stakeholder_issue/{request_id}", include_in_schema=False)
async def request_stakeholder_issue(request_id: str, response: Response, body: ReqStakeCred):
    # SETUP ISSUER CONNECTION
    try:
        body_dict = body.dict()

        setup_issuer.issuer_connection(body_dict["agent_service_endpoint"])
        #setup_issuer.issuer_connection()
        print(setup_issuer.connection_id)
    except:
        return "Unable to establish Issuer Connection"

    # SETUP AUTH SCHEMA
    try:
        setup_stake_schema.stakeholder_cred_setup()
        print(setup_stake_schema.cred_def_id)
    except:
        return "Unable to setup Stakeholder Schema"
    
    # CHECK FOR REQUEST RECORD
    test = mongo_setup_admin.stakeholder_col.find_one({"holder_request_id": request_id})
    if test != None:
        if test["state"] == "Stakeholder Registered":
            return "Stakeholder Request was already issued"

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
            "state": "Stakeholder Registration Requested",
            #"handler_url": body_dict["handler_url"]
            "service_endpoint": body_dict["service_endpoint"]
        }

        mongo_setup_admin.stakeholder_col.insert_one(res_to_insert_db)

        res_to_admin_handler = {
            "_id": str(res_to_insert_db["_id"]),
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
            "service_endpoint": body_dict["service_endpoint"]
        }
        #print(res_to_admin_handler)
        
        admin_handler_url = os.environ["HANDLER_ADMIN_URL"]        
        requests.post(admin_handler_url+"/stakeholder/receive", headers=header, json=res_to_admin_handler, timeout=60)
        #print(res.json())

        return res_to_admin_handler
    
    except:
        return "Unable to connect to Admin Handler"

@router.post("/issue_stakeholder/{request_id}", status_code=201)
async def issue_stakeholder(request_id: str, response: Response, body: IssueStakeCred):
    # CHECK FOR REQUEST RECORD
    try:
        test = mongo_setup_admin.stakeholder_col.find_one({"_id": ObjectId(request_id)})
        #print(test)
    except:
        return "Stakeholder Request doesn't exist in Database"

    # ISSUE CREDENTIAL
    try:
        body_dict = body.dict()

        URL = os.environ["ISSUER_AGENT_URL"]
        
        # Configure Stakeholder to be registered
        issue_cred = {
            "connection_id": setup_issuer.connection_id,
            "cred_def_id": setup_stake_schema.cred_def_id,
            "credential_proposal": {
                "attributes": [
                    {
                        "name": "stakeholderClaim",
                        "value": str(body_dict["stakeholderClaim"])
                    },
                    {
                        "name": "timestamp",
                        "value": str(body_dict["timestamp"])
                    }
                ]
            }
        }
        #print(issue_cred)

        final_resp = requests.post(URL+"/issue-credential/send", data=json.dumps(issue_cred), headers=header, timeout=60)
        #print(final_resp.text)
        cred_info = json.loads(final_resp.text)
        id_token = cred_info["credential_exchange_id"]

        #print(cred_info)
        #print(id_token)

        if cred_info["state"] == "offer_sent":
            # SUBSCRIBE TO AGENT RESPONSE
            try:
                # UPDATE REQUEST RECORD FROM MONGO
                mongo_setup_admin.stakeholder_col.find_one_and_update({'_id': ObjectId(request_id)}, {'$set': {"state": "Stakeholder Registered", "credential_definition_id": cred_info["credential_definition_id"], "id_token": id_token}})
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
            
            except:        
                return "Unable to subscribe to response"

            # NOTIFY HOLDER AGENT
            #try:
            holder_url = body_dict["service_endpoint"]
            #print(holder_url)
            requests.post(holder_url+"/holder/update_stakeholder_state/"+str(body_dict["holder_request_id"]), json=resp_cred, timeout=60)
            #except:
            #    return "Unable to notify Holder"
            
            return resp_cred

        else:
            return "Unable to subscribe to Credential response"
    
    except:
        return "Unable to connect to Issuer Agent"