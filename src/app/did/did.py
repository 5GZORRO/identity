from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
import requests, json
from pydantic import BaseModel, HttpUrl

#Connection First
#from app.bootstrap import setup_issuer, setup_verifier
#After Auth token 
#from app.authentication import authentication

#from app import test_comm_between_agent
#from ..src/authentication import setup_i
#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/dids",
    tags=["did"]
)

#class Did(BaseModel):
#    did: str
#    verkey: str

####################### DID Management #######################
@router.post("/create", summary="Create an DID") #response_model=Did,
async def create_did(did: str, verkey: str, handler_url: Optional[str] = None): #, token: str = Depends(oauth2_scheme),  current_user: User = Depends(get_current_active_user)
    if handler_url != None:
        requests.post(handler_url, json={"did": did, "verkey": verkey, "message": "Successfully tested"})
    return {"did": did, "verkey": verkey, "message": "Successfully tested"}

@router.get("/read")
async def read_did():
    return "Awaiting Implementation"
    #return "ISSUER conn_id: " + setup_issuer.connection_id + "; VERIFIER conn_id: " + setup_verifier.connection_id + "; ADMIN id_token: " + authentication.id_token

@router.post("/register")
async def register_did():
    return "Awaiting Implementation"