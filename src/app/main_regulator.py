#from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import RedirectResponse
import json, os

#Log Configuration
from loguru import logger
from app.config import log_config

logger.remove()
logger.add("./app/logs/file_regulator_agent.log", format="{time:YYYY-MM-DD at HH:mm:ss} | {level}: {message} | {function} in line {line} on {file}", rotation="5 MB")

#Verification Key
from app.bootstrap.key import key_pair
#Database Setup
from app.db import mongo_setup_provider # For Holder Operations
from app.db import mongo_setup_regulator
#Connection First
from app.bootstrap import setup_issuer
#Setup required Schemas
from app.bootstrap import setup_license_schema


from app.authentication import send_proof, get_key_pair

# Holder Agent Ops
from app.holder import holder_stakeholder, holder_did
from app.holder.state_update import update_stakeholder

from app.regulator import regulator_license


with open('app/openapi/openapi_regulator.json') as json_file:
    tags_metadata = json.load(json_file)


app = FastAPI(
    docs_url="/",
    openapi_tags=tags_metadata,
    openapi_url="/openapi.json",
    title="Identity & Permissions Manager - Regulator Agent API",
    description="""This is a project able to supply the mechanisms required for generating unique identifiers in 5GZORRO ecosystem, recognising communicating endpoints, 
        identifying and authenticating entities, services, and organizations, and authorising consumer requests to access a preserved services and resources."""
)

origins = os.environ["WHITELIST"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

######## Routes to Endpoints in Different Files ########
app.include_router(holder_stakeholder.router)
app.include_router(holder_did.router)
app.include_router(update_stakeholder.router)

app.include_router(regulator_license.router)

app.include_router(get_key_pair.router)
app.include_router(send_proof.router)
