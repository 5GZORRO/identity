#from typing import Optional
from fastapi import FastAPI
from starlette.responses import RedirectResponse

import json

#Connection First
from app.bootstrap import setup_issuer, setup_verifier
#After Auth token 
from app.authentication import authentication

from app.did import did
from app.credential import credential


with open('app/openapi.json') as json_file:
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
app.include_router(credential.router)


@app.get("/", include_in_schema=False)
def redirect_main():
    response = RedirectResponse(url='/docs')
    return response