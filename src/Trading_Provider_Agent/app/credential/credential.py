from typing import Optional
from fastapi import APIRouter, Response, status
from pydantic import BaseModel
import requests, json, sys, os

from app.authentication import authentication

router = APIRouter(
    prefix="/credentials",
    tags=["credential"]
)

class Offer(BaseModel):
    id: str
    type: str
    credentialSubject: dict
    issuer: dict
    issuanceDate: str
    expirationDate: str
    credentialStatus: dict
    proof: dict

header = {
    'Content-Type': 'application/json'        
}

####################### Verifiable Credentials Management #######################
@router.post("/request")
async def request_credential(response: Response, token: str, body: Offer, handler_url: Optional[str] = None):
    if token != authentication.id_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return "Invalid ID Token"

    try:
        #print("Received body: " + str(body))
        #print("\n")
        body_dict = body.dict()
        #print("Converted body: " + str(body_dict))
        
        URL = os.environ["ADMIN_AGENT_CONTROLLER_URL"]
        resp = requests.post(URL+"/credentials/issue/trading_provider", json=body_dict, timeout=30)
        body = resp.json()
        if handler_url != None:
            try:
                requests.post(handler_url, headers=header, json=body, timeout=30)
            except:
                body.update({"handler_info": "Unable to send data to Handler URL"})
        response.status_code = status.HTTP_201_CREATED
        return body
        
    except:
        return "Unable to perform Credential issuing request."

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