#from typing import Optional
from fastapi import FastAPI
from starlette.responses import RedirectResponse

import json

#Verification Key
from app.bootstrap.key import issuer_key
#Database Setup
from app.db import mongo_setup_provider # For Holder Operations
from app.db import mongo_setup_admin
#Connection First
from app.bootstrap import setup_issuer, setup_verifier
#Setup VC Schema
from app.bootstrap import setup_vc_schema
#After Auth token 
from app.authentication import authentication

from app.did import did
from app.issuer import issuer
from app.verifier import verifier


with open('app/openapi/openapi_admin.json') as json_file:
    tags_metadata = json.load(json_file)


app = FastAPI(
    docs_url="/admin",
    openapi_tags=tags_metadata,
    openapi_url="/admin/openapi.json",
    title="Identity & Permissions Manager - Admin Agent API",
    description="""This is a project able to supply the mechanisms required for generating unique identifiers in 5GZORRO ecosystem, recognising communicating endpoints, 
        identifying and authenticating entities, services, and organizations, and authorising consumer requests to access a preserved services and resources."""
)

######## Routes to Endpoints in Different Files ########
app.include_router(did.router)
app.include_router(issuer.router)
app.include_router(verifier.router)

#issuer_key.holder_key_create()

#@app.get("/", include_in_schema=False)
#def redirect_main():
#    response = RedirectResponse(url='/admin')
#    return response