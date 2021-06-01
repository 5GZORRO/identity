#from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import json

#Verification Key
from app.bootstrap.key import holder_key #,issuer_key
#Database Setup
from app.db import mongo_setup_provider # For Holder Operations
from app.db import mongo_setup_admin
#Connection First
from app.bootstrap import setup_issuer #, setup_verifier
#Setup required Schemas
from app.bootstrap import setup_vc_schema, setup_stake_schema


#from app.did import did
from app.authentication import send_proof, verify_credential
from app.holder import holder
from app.issuer import issuer
#from app.verifier import verifier


with open('app/openapi/openapi_admin.json') as json_file:
    tags_metadata = json.load(json_file)


app = FastAPI(
    docs_url="/",
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json",
    title="Identity & Permissions Manager - Admin Agent API",
    description="""This is a project able to supply the mechanisms required for generating unique identifiers in 5GZORRO ecosystem, recognising communicating endpoints, 
        identifying and authenticating entities, services, and organizations, and authorising consumer requests to access a preserved services and resources."""
)

origins = [
    "http://localhost:3000",
    "http://172.28.3.126:30008/",
    "http://172.28.3.126:30009/",
    "https://5gzorro.netlify.app/",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

######## Routes to Endpoints in Different Files ########
#app.include_router(did.router)
app.include_router(holder.router)
app.include_router(issuer.router)
app.include_router(send_proof.router)
app.include_router(verify_credential.router)
#app.include_router(verifier.router)

holder_key.holder_key_create()
#issuer_key.issuer_key_create()

#@app.get("/", include_in_schema=False)
#def redirect_main():
#    response = RedirectResponse(url='/admin')
#    return response