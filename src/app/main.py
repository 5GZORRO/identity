#from typing import Optional
from fastapi import FastAPI
from starlette.responses import RedirectResponse

import json

#Database Setup
from app.bootstrap import mongo_setup
#Connection First
from app.bootstrap import setup_issuer, setup_verifier
#Setup VC Schema
from app.bootstrap import setup_vc_schema
#After Auth token 
from app.authentication import authentication

from app.did import did
from app.holder import holder
from app.issuer import issuer
from app.verifier import verifier
#from app.authentication import authentication


with open('app/openapi/openapi.json') as json_file:
    tags_metadata = json.load(json_file)


app = FastAPI(
    openapi_tags=tags_metadata,
    #openapi_url="/openapi.json",
    title="Identity & Permissions Manager API",
    description="""This is a project able to supply the mechanisms required for generating unique identifiers in 5GZORRO ecosystem, recognising communicating endpoints, 
        identifying and authenticating entities, services, and organizations, and authorising consumer requests to access a preserved services and resources."""
)

######## Routes to Endpoints in Different Files ########
app.include_router(did.router)
app.include_router(holder.router)
app.include_router(issuer.router)
app.include_router(verifier.router)
#app.include_router(authentication.router)


@app.get("/", include_in_schema=False)
def redirect_main():
    response = RedirectResponse(url='/docs')
    return response

#@app.get("/items/{item_id}")
#def read_item(item_id: int, q: Optional[str] = None):
#    return {"item_id": item_id, "q": q}