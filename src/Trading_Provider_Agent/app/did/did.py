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


####################### DID Management #######################
@router.post("/create", summary="Create an DID") #response_model=Did,
async def create_did():
    return "Awaiting Implementation"

@router.get("/read")
async def read_did():
    return "Awaiting Implementation"

@router.post("/register")
async def register_did():
    return "Awaiting Implementation"