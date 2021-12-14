import requests, json, time, sys, os
from timeloop import Timeloop
from datetime import timedelta
from loguru import logger

# Create public agent key
def public_key_create():
    try:
        holder_url = os.environ["HOLDER_AGENT_URL"]
        resp = requests.post(holder_url+"/wallet/did/create", timeout=30)
        result = resp.json()
        global public_did, public_verkey
        public_did = result["result"]["did"]
        public_verkey = result["result"]["verkey"]
        logger.info("Public DID: " + str(public_did))
        logger.info("Public Verification Key: " + str(public_verkey))

    except Exception as error:
        logger.error(error)        
        sys.exit()
