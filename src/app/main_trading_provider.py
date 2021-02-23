#from typing import Optional
from fastapi import FastAPI
from starlette.responses import RedirectResponse

import json

#Database Setup
from app.db import mongo_setup_provider
#Connection First
from app.bootstrap import setup_verifier #setup_issuer,
#Setup VC Schema
#from app.bootstrap import setup_vc_schema
#After Auth token 
#from app.authentication import authentication

from app.did import did
from app.holder import holder


with open('app/openapi/openapi_trading_provider.json') as json_file:
    tags_metadata = json.load(json_file)


app = FastAPI(
    openapi_tags=tags_metadata,
    #openapi_url="/openapi.json",
    title="Identity & Permissions Manager - Trading Provider Agent API",
    description="""This is a project able to supply the mechanisms required for generating unique identifiers in 5GZORRO ecosystem, recognising communicating endpoints, 
        identifying and authenticating entities, services, and organizations, and authorising consumer requests to access a preserved services and resources."""
)

######## Routes to Endpoints in Different Files ########
app.include_router(did.router)
app.include_router(holder.router)


@app.get("/", include_in_schema=False)
def redirect_main():
    response = RedirectResponse(url='/docs')
    return response