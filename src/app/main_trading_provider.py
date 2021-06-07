#from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse

import json

#Verification Key
from app.bootstrap.key import holder_key
#Database Setup
from app.db import mongo_setup_provider
#Connection First
#from app.bootstrap import setup_verifier #setup_issuer,
#Setup VC Schema
#from app.bootstrap import setup_vc_schema


#from app.did import did
from app.authentication import send_proof
from app.holder import holder


with open('app/openapi/openapi_trading_provider.json') as json_file:
    tags_metadata = json.load(json_file)


app = FastAPI(
    docs_url="/",
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json",
    title="Identity & Permissions Manager - Trading Provider Agent API",
    description="""This is a project able to supply the mechanisms required for generating unique identifiers in 5GZORRO ecosystem, recognising communicating endpoints, 
        identifying and authenticating entities, services, and organizations, and authorising consumer requests to access a preserved services and resources."""
)

origins = [
    "http://localhost:3000",
    "http://172.28.3.126:30008",
    "http://172.28.3.126:30009",
    "https://5gzorro.netlify.app",
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
app.include_router(send_proof.router)
app.include_router(holder.router)

holder_key.holder_key_create()

#@app.get("/", include_in_schema=False)
#def redirect_main():
#    response = RedirectResponse(url='/provider')
#    return response