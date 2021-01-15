from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordBearer
import requests, json
from pydantic import BaseModel, HttpUrl

#oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/dids",
    tags=["did"]
)

#class Did(BaseModel):
#    did: str
#    verkey: str

class User(BaseModel):
    username: str
    password: str
    company: dict = {}


####################### DID Management #######################
@router.post("/create", summary="Create an DID") #response_model=Did,
async def create_did(did: str, verkey: str):
    return {"did": did, "verkey": verkey, "message": "Successfully tested"}

@router.get("/read")
async def read_did():
    return "Awaiting Implementation"

@router.post("/register")
async def register_did(body: User): #body: dict
    print("Received body: " + str(body))
    print("\n")
    body_dict = body.dict()
    print("Converted body: " + str(body_dict))
    body_dict.update({"specs": {'user_test': 'yes', 'flag': '1'}})
    return body_dict


'''
async def register_did(body: dict): 
    print("Received body: " + str(body))
    print("\n")
    body['specs'] = {'user_test': 'yes', 'flag': '1'}
    return body
'''